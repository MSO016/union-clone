'''
Widget principal do modulo SPD (PyQt5).
Ver: alan/documentacao/16-08-2026-ARQUITETURA-SPD-INTERNA/01_MAPA_REFERENCIAS_INTERNAS.md
'''
import logging
import threading
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QMessageBox, QFrame, QTabWidget, QCheckBox, QSplitter)
from PyQt5.QtCore import (Qt, QTimer, QMetaObject, pyqtSlot)
from PyQt5.QtGui import QFont
ENABLE_NATIVE_ENGINE = False
from .components import (Cores, TerminalLog, ActionButton, DangerButton, StatusBar, DeviceListBox, OperationPanel, ResponseLabel, FDLIndicator)
from .workers import SPDFullWorker
from .partition_tab import PartitionTab
logger = logging.getLogger(__name__)
class SPDToolsWidget(QWidget):
    '''
Widget principal do m├│dulo SPD Tools para UNION.
Pode ser usado standalone ou embutido no MainWindow do UNION.
Layout:
  ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ
  Ôöé  HEADER ÔÇö TECH UNION SOLUTIONS ┬À SPD Tools               Ôöé
  Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö¼ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö¼ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ
  Ôöé  DispositivosÔöé  Opera├º├Áes    Ôöé  [Engine Ôû╝] [Status] [ÔùÅ]  Ôöé
  Ôöé  (lista)     Ôöé  (timeout)    Ôöé  Terminal de Logs         Ôöé
  Ôöé  + busca     Ôöé  (bot├Áes)     Ôöé  (auto-detect COM)        Ôöé
  Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö┤ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö┤ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ
  Ôöé  [ProgressBar ÔûêÔûêÔûêÔûêÔûêÔûêÔûêÔûêÔûêÔûêÔûêÔûêÔûêÔûêÔûêÔûêÔûêÔûêÔûêÔûê]            [STOP]    Ôöé
  Ôöé  Response: ACK                                           Ôöé
  ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ
'''
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._model_config = None
        self._is_running = False
        self._brand_map = {}
        self._brand_map_dirty = False
        self._sync_iniciado = False
        self._init_ui()
        self._connect_signals()
        self._start_port_scan()
        import atexit
        atexit.register(self._atexit_cleanup)
    def _atexit_cleanup(self):
        '''Ultima chance de nao deixar spd_dump.exe orfao.'''
        try:
            if hasattr(self, 'partition_tab'):
                if self.partition_tab:
                    self.partition_tab.cleanup()
                    return
                return
        except Exception:
            pass
    def closeEvent(self, event):
        '''Cleanup ao fechar a janela do modulo SPD.'''
        try:
            if hasattr(self, 'partition_tab') and self.partition_tab:
                self.partition_tab.cleanup()
        except Exception:
            pass
        try:
            if hasattr(self, '_port_timer') and self._port_timer:
                self._port_timer.stop()
        except Exception:
            pass
        super().closeEvent(event)
    def _init_ui(self):
        '''Monta o layout completo. Adaptavel a resolucoes >= 800x480.'''
        self.setMinimumSize(800, 480)
        self.setStyleSheet(f'background-color: {Cores.BACKGROUND};')
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)
        main_layout.addWidget(self._create_header())
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.tabBar().setExpanding(False)
        self.tab_widget.tabBar().setUsesScrollButtons(False)
        self.tab_widget.setStyleSheet(f'\n            QTabWidget::pane {{\n                border: 1px solid {Cores.BORDER};\n                border-radius: 4px;\n                background-color: {Cores.BACKGROUND};\n            }}\n            QTabBar::tab {{\n                background-color: #E8E8E8;\n                border: 1px solid {Cores.BORDER};\n                border-bottom: none;\n                border-top-left-radius: 4px;\n                border-top-right-radius: 4px;\n                padding: 8px 24px;\n                margin-right: 2px;\n                min-width: 120px;\n                font-size: 12px;\n                font-weight: bold;\n            }}\n            QTabBar::tab:selected {{\n                background-color: {Cores.BACKGROUND};\n                border-bottom: 2px solid {Cores.PRIMARY};\n                color: {Cores.PRIMARY};\n            }}\n            QTabBar::tab:!selected {{\n                margin-top: 2px;\n                color: #7f8c8d;\n            }}\n        ')
        ops_tab = QWidget()
        ops_layout = QHBoxLayout(ops_tab)
        ops_layout.setContentsMargins(4, 4, 4, 4)
        ops_layout.setSpacing(4)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet(f'\n            QSplitter::handle {{\n                background-color: {Cores.BORDER};\n            }}\n            QSplitter::handle:hover {{\n                background-color: {Cores.PRIMARY};\n            }}\n        ')
        self.device_list = DeviceListBox()
        self.device_list.setMinimumWidth(200)
        self.device_list.setMaximumWidth(360)
        splitter.addWidget(self.device_list)
        self.operation_panel = OperationPanel()
        self.operation_panel.setMinimumWidth(210)
        self.operation_panel.setMaximumWidth(320)
        splitter.addWidget(self.operation_panel)
        right_container = QWidget()
        right_panel = QVBoxLayout(right_container)
        right_panel.setContentsMargins(0, 0, 0, 0)
        right_panel.setSpacing(4)
        top_bar = QHBoxLayout()
        top_bar.setSpacing(6)
        from PyQt5.QtWidgets import QComboBox
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(['Engine Auth-1', 'Engine Auth-2'])
        self.engine_combo.setFixedWidth(130)
        self.engine_combo.setCurrentIndex(0)
        self.engine_combo.setStyleSheet(f'\n            QComboBox {{\n                border: 1px solid {Cores.BORDER};\n                border-radius: 4px;\n                padding: 4px 8px;\n                font-size: 11px;\n                background-color: white;\n            }}\n        ')
        if not ENABLE_NATIVE_ENGINE:
            self.engine_combo.hide()
        top_bar.addWidget(self.engine_combo)
        self.port_label = QLabel('Porta: auto-detect')
        self.port_label.setStyleSheet(f'\n            QLabel {{\n                color: {Cores.TEXT_MUTED};\n                font-size: 11px;\n                padding: 4px 8px;\n                border: 1px solid {Cores.BORDER};\n                border-radius: 4px;\n                background-color: white;\n            }}\n        ')
        top_bar.addWidget(self.port_label, 1)
        self.fdl_indicator = FDLIndicator()
        top_bar.addWidget(self.fdl_indicator)
        self.chk_advanced = QCheckBox('Autorizacao Avancada')
        self.chk_advanced.setFont(QFont('Segoe UI', 8))
        self.chk_advanced.setChecked(True)
        self.chk_advanced.setToolTip('Habilita autorizacao avancada para dispositivos protegidos.\nQuando desmarcado, apenas o fluxo padrao (FDL1 + FDL2) e usado.')
        self.chk_advanced.setStyleSheet(f'\n            QCheckBox {{ color: {Cores.TEXT}; spacing: 4px; padding: 2px 6px; }}\n            QCheckBox::indicator {{ width: 14px; height: 14px; }}\n            QCheckBox::indicator:checked {{\n                background-color: {Cores.PRIMARY};\n                border: 1px solid {Cores.PRIMARY_DARK if hasattr(Cores, 'PRIMARY_DARK') else '#1a5276'};\n                border-radius: 2px;\n            }}\n            QCheckBox::indicator:unchecked {{\n                background-color: white;\n                border: 1px solid {Cores.BORDER};\n                border-radius: 2px;\n            }}\n        ')
        top_bar.addWidget(self.chk_advanced)
        self.chk_force = QCheckBox('Force')
        self.chk_force.setFont(QFont('Segoe UI', 8))
        self.chk_force.setChecked(False)
        self.chk_force.setToolTip('Force: usa modo --kick do spd_dump (boot_diag -> cali_diag -> dl_diag).\nAtive se o device nao conectar normalmente ou em portas USB instaveis.')
        self.chk_force.setStyleSheet(f'\n            QCheckBox {{ color: {Cores.TEXT}; spacing: 4px; padding: 2px 6px; }}\n            QCheckBox::indicator {{ width: 14px; height: 14px; }}\n            QCheckBox::indicator:checked {{\n                background-color: #c0392b;\n                border: 1px solid #922b21;\n                border-radius: 2px;\n            }}\n            QCheckBox::indicator:unchecked {{\n                background-color: white;\n                border: 1px solid {Cores.BORDER};\n                border-radius: 2px;\n            }}\n        ')
        top_bar.addWidget(self.chk_force)
        right_panel.addLayout(top_bar)
        self.terminal = TerminalLog()
        self.terminal.setMinimumHeight(180)
        right_panel.addWidget(self.terminal, 1)
        splitter.addWidget(right_container)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 0)
        splitter.setStretchFactor(2, 1)
        splitter.setSizes([230, 240, 890])
        ops_layout.addWidget(splitter)
        self.tab_widget.addTab(ops_tab, 'Operacoes')
        self.partition_tab = PartitionTab(get_model_config_fn=self._get_current_model_config)
        self.partition_tab._sig_pause_port_scan.connect(self._on_pause_port_scan)
        self.tab_widget.addTab(self.partition_tab, 'Particoes')
        try:
            self.chk_advanced.toggled.connect(self._sync_advanced_to_partition)
            self.partition_tab.chk_advanced.toggled.connect(self._sync_advanced_from_partition)
            self.partition_tab.chk_advanced.setChecked(self.chk_advanced.isChecked())
        except Exception:
            pass
        try:
            self.chk_force.toggled.connect(self._sync_force_to_partition)
            self.partition_tab.chk_force.toggled.connect(self._sync_force_from_partition)
            self.partition_tab.chk_force.setChecked(self.chk_force.isChecked())
        except Exception:
            pass
        main_layout.addWidget(self.tab_widget, 1)
        bottom = QHBoxLayout()
        bottom.setSpacing(8)
        self.progress_bar = StatusBar()
        bottom.addWidget(self.progress_bar, 1)
        self.btn_stop = DangerButton('STOP')
        self.btn_stop.setFixedSize(80, 36)
        self.btn_stop.setEnabled(False)
        bottom.addWidget(self.btn_stop)
        main_layout.addLayout(bottom)
        self.response_label = ResponseLabel()
        main_layout.addWidget(self.response_label)
    def _create_header(self) -> QFrame:
        '''
Cria header com branding UNION + aviso MODO DE TESTE embutido.
Layout em 2 linhas dentro da faixa azul primaria:
  Linha 1: TECH UNION SOLUTIONS  ┬À  SPD Tools
  Linha 2: [W] MODO DE TESTE - RISCO DE BRICK: ...
'''
        header = QFrame()
        header.setMinimumHeight(66)
        header.setStyleSheet(f'\n            QFrame {{\n                background-color: {Cores.PRIMARY};\n                border-radius: 6px;\n            }}\n        ')
        v_wrap = QVBoxLayout(header)
        v_wrap.setContentsMargins(16, 6, 16, 6)
        v_wrap.setSpacing(2)
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6)
        title = QLabel('TECH UNION SOLUTIONS')
        title.setFont(QFont('Segoe UI', 14, QFont.Bold))
        title.setStyleSheet('color: white; background: transparent;')
        top_row.addWidget(title)
        subtitle = QLabel('┬À SPD Tools')
        subtitle.setFont(QFont('Segoe UI', 14, QFont.Light))
        subtitle.setStyleSheet('color: rgba(255,255,255,0.8); background: transparent;')
        top_row.addWidget(subtitle)
        top_row.addStretch()
        v_wrap.addLayout(top_row)
        aviso = QLabel('MODO DE TESTE ÔÇö RISCO DE BRICK: use somente se voce tem conhecimento tecnico de Unisoc/Spreadtrum, identifica o SoC/DRAM correto e opera com Test Point + backup previo.')
        aviso.setFont(QFont('Segoe UI', 9, QFont.Bold))
        aviso.setStyleSheet('color: #FFEB3B; background: transparent;')
        aviso.setWordWrap(True)
        v_wrap.addWidget(aviso)
        h_layout = top_row
        version = QLabel('v1.0')
        version.setFont(QFont('Segoe UI', 10))
        version.setStyleSheet('color: rgba(255,255,255,0.6); background: transparent;')
        h_layout.addWidget(version)
        return header
    def _connect_signals(self):
        '''Conecta sinais dos componentes.'''
        self.device_list.list_widget.currentItemChanged.connect(self._on_device_selected)
        self.btn_stop.clicked.connect(self._on_stop)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
    def _on_tab_changed(self, index: int):
        '''Atualiza estado do STOP conforme aba ativa.'''
        if index == 1 and self.partition_tab._is_busy:
            self.btn_stop.setEnabled(True)
            return
        if index == 0 and self._is_running:
            self.btn_stop.setEnabled(True)
            return
        if not self._is_running:
            self.btn_stop.setEnabled(False)
    def _start_port_scan(self):
        '''
        Inicia scan peri├│dico de portas COM.
        Adapta├º├úo: QTimer polling a cada 3 segundos
        '''
        self._scan_ports()
        self._port_timer = QTimer(self)
        self._port_timer.timeout.connect(self._scan_ports)
        self._port_timer.start(3000)
    def _on_pause_port_scan(self, paused: bool):
        '''Pausa ou retoma o scan de portas COM (chamado pela PartitionTab).'''
        if paused:
            self._port_timer.stop()
            return
        self._port_timer.start(3000)
    def _scan_ports(self):
        '''
        Escaneia portas COM e atualiza label informativo.
        N├úo interfere no worker ÔÇö ├® apenas visual.
        Quando o worker est├í rodando, ele tem seu pr├│prio detector.
        '''
        if self._is_running:
            return
        try:
            from app.views.union_unlock.spd.device_detect import DeviceDetector
            if not hasattr(self, '_device_detector') or self._device_detector is None:
                self._device_detector = DeviceDetector()
            detector = self._device_detector
            devices = detector.scan()
            if devices:
                dev = next((d for d in devices if d.is_spd_download), devices[0])
                if dev.is_spd_download:
                    label_text = f'Porta: {dev.port} ┬À Download'
                    border_color = Cores.SUCCESS
                    bg_color = '#eafaf1'
                    text_color = Cores.SUCCESS
                else:
                    mode_txt = dev.mode_label or dev.name or '?'
                    label_text = f'Porta: {dev.port} ┬À {mode_txt}'
                    border_color = '#e67e22'
                    bg_color = '#fdf5ec'
                    text_color = '#a55b0c'
                self.port_label.setText(label_text)
                self.port_label.setStyleSheet(f'\n                    QLabel {{\n                        color: {text_color};\n                        font-size: 11px;\n                        padding: 4px 8px;\n                        border: 1px solid {border_color};\n                        border-radius: 4px;\n                        background-color: {bg_color};\n                    }}\n                ')
                return
            self.port_label.setText('Porta: auto-detect')
            self.port_label.setStyleSheet(f'\n                    QLabel {{\n                        color: {Cores.TEXT_MUTED};\n                        font-size: 11px;\n                        padding: 4px 8px;\n                        border: 1px solid {Cores.BORDER};\n                        border-radius: 4px;\n                        background-color: white;\n                    }}\n                ')
            return
        except Exception:
            return
    def load_model_database(self, db):
        '''Popula a lista de dispositivos organizada por marca.'''
        self._brand_map = {}
        for brand in db.get_brands():
            devices = []
            for model in db.get_models(brand):
                display = model.model
                chipset = model.chipset or ''
                devices.append((display, chipset, model))
            if devices:
                self._brand_map[brand] = devices
        self.device_list.set_brands(self._brand_map)
    def _populate_device_list(self, db):
        '''Alias interno para load_model_database.'''
        self.load_model_database(db)
    def showEvent(self, event):
        '''Primeira exibicao dispara verificacao silenciosa em background.'''
        super().showEvent(event)
        if not self._sync_iniciado:
            self._sync_iniciado = True
            QTimer.singleShot(150, self._sync_silencioso)
    def _sync_silencioso(self):
        '''Verifica atualizacoes em background sem bloquear a UI.
        Sempre agenda repopulacao no main thread ao final, mesmo quando
        nao havia necessidade de sync (cache local ja aquecido) ÔÇö assim
        garantimos que a primeira exibicao da aba nunca fique vazia.
        '''
        def _run():
            try:
                from app.views.union_unlock.spd.spd_sync import get_sync
                sync = get_sync()
                if sync.pode_sincronizar():
                    ok = sync.sincronizar()
                    logger.info('SPD sync silencioso: %s', 'ok' if ok else 'sem conexao')
            except Exception as e:
                logger.warning('SPD sync silencioso falhou: %s', type(e).__name__)
            try:
                QMetaObject.invokeMethod(self, '_recarregar_marcas', Qt.QueuedConnection)
            except Exception:
                return
        threading.Thread(target=_run, daemon=True).start()
    def sincronizar(self):
        '''API publica para sincronizacao forcada (menu Ctrl+Shift+U).'''
        def _run():
            try:
                from app.views.union_unlock.spd.spd_sync import get_sync
                sync = get_sync()
                ok = sync.sincronizar()
                logger.info('SPD sync forcado: %s', 'ok' if ok else 'sem conexao')
            except Exception as e:
                logger.warning('SPD sync forcado falhou: %s', type(e).__name__)
            try:
                QMetaObject.invokeMethod(self, '_recarregar_marcas', Qt.QueuedConnection)
            except Exception:
                return
        threading.Thread(target=_run, daemon=True).start()
    @pyqtSlot()
    def _recarregar_marcas(self):
        '''Slot: repopula ambas as abas (Operacoes + Particoes) apos sync.
        Chamado via QueuedConnection (main thread), garante que set_brands
        e populacao de QComboBox aconteca fora de thread de rede.
        '''
        try:
            self._carregar_operacoes_mysql()
        except Exception as e:
            logger.debug('SPD _recarregar_marcas ops: %s', type(e).__name__)
        try:
            pt = getattr(self, 'partition_tab', None)
            if pt:
                if hasattr(pt, '_load_from_mysql'):
                    pt._load_from_mysql()
                    return
                return
        except Exception as e:
            logger.debug('SPD _recarregar_marcas part: %s', type(e).__name__)
    def _carregar_operacoes_mysql(self):
        '''Popula DeviceListBox (aba Operacoes) a partir do servidor.
        Consulta a mesma camada de sync usada pela aba de particoes, monta
        um dict {marca: [(display, chipset, ModelConfig), ...]} e chama
        set_brands. Silencioso em falha (mantem placeholder).
        '''
        try:
            from app.views.union_unlock.spd.spd_sync import get_sync
            from app.views.union_unlock.spd.model_data import ModelConfig
        except ImportError:
            return
        try:
            sync = get_sync()
            marcas = sync.listar_marcas()
            if not marcas:
                return
            brand_map = {}
            total = 0
            for marca in sorted(marcas):
                modelos = sync.listar_modelos_por_marca(marca)
                brand_key = marca.upper()
                devices = []
                for m in modelos:
                    ops = sync.get_operacoes(m['srv_id'])
                    op_names = [val.get('label', key) for key, val in ops.items()]
                    config = ModelConfig(brand=brand_key, model=m['modelo'], chipset=m.get('chipset') or '', fdl1_addr=int(m['fdl1_addr'], 16) if m.get('fdl1_addr') else 0, fdl2_addr=int(m['fdl2_addr'], 16) if m.get('fdl2_addr') else 0, exec_addr=int(m['exec_addr'], 16) if m.get('exec_addr') else None, fdl1_file='fdl1-dl.bin', fdl2_file='fdl2-dl.bin', operations=op_names, data_dir='')
                    config._srv_id = m['srv_id']
                    config._ops_json = ops
                    config._memoria = m.get('memoria', 'emmc')
                    display = config.model
                    chipset = config.chipset or ''
                    devices.append((display, chipset, config))
                    total += 1
                continue
                if not devices:
                    continue
                brand_map[brand_key] = devices
                continue
        except Exception as e:
            logger.warning('SPD carregar operacoes: %s', type(e).__name__)
        if brand_map:
            self._brand_map = brand_map
            self.device_list.set_brands(brand_map)
            logger.info('SPD Operacoes: %d modelos carregados', total)
    def _on_device_selected(self, current, previous):
        '''
Ao selecionar dispositivo, carrega opera├º├Áes.
     1. L├¬ Info do item selecionado
     2. MyDisplay.RtbClear()
     3. Log "Selected: ..."
'''
        if current is None or self._is_running:
            return
        config = current.data(Qt.UserRole)
        if config is None:
            return
        self._model_config = config
        self.terminal.clear_logs()
        self.terminal.log(f'Selecionado: {config.brand} {config.model} {config.chipset}', tipo='info', bold=True)
        self.operation_panel.clear_operations()
        for op_name in config.operations:
            self.operation_panel.add_operation(op_name, self._on_operation_click)
        if not config.operations:
            from app.views.union_unlock.spd.constants import OPERATIONS
            for op_name in OPERATIONS:
                self.operation_panel.add_operation(op_name, self._on_operation_click)
        self.fdl_indicator.set_loaded(False)
        self.progress_bar.setValue(0)
        self.response_label.set_response('Aguardando...')
    def _on_operation_click(self, operation_name: str):
        '''
Ao clicar bot├úo de opera├º├úo ÔåÆ entra em modo de escuta.
     1. isUniSPDRunning = true
     2. Worker entra em escuta aguardando porta SPD
     3. Detecta ÔåÆ FDL1 ÔåÆ FDL2 ÔåÆ opera├º├úo ÔåÆ reset
N├âO exige porta COM pr├®-selecionada ÔÇö detec├º├úo ├® autom├ítica.
'''
        if self._is_running:
            return
        if self._model_config is None:
            QMessageBox.warning(self, 'Aviso', 'Selecione um dispositivo primeiro.')
            return
        _op_upper = operation_name.upper()
        if _op_upper == 'PARTITIONS' or 'PARTICOES' in _op_upper or 'PARTI├ç├òES' in _op_upper:
            self.partition_tab.select_model_by_config(self._model_config)
            self.tab_widget.setCurrentWidget(self.partition_tab)
            return
        if ENABLE_NATIVE_ENGINE:
            engine = 'binary' if self.engine_combo.currentIndex() == 0 else 'internal'
        else:
            engine = 'binary'
        timeout = self.operation_panel.get_timeout_ms() // 1000 * 60
        if timeout < 30:
            timeout = 120
        self._start_operation(operation_name, engine, timeout)
    def _start_operation(self, operation: str, engine: str, timeout: int=120):
        '''
Inicia o fluxo completo: escuta ÔåÆ detecta ÔåÆ FDL ÔåÆ opera├º├úo ÔåÆ reset.
Cria um ├║nico SPDFullWorker que faz tudo sequencialmente:
  1. Aguarda dispositivo SPD na porta COM (polling)
  2. Carrega FDL1 + FDL2
  3. Executa opera├º├úo
  4. Reset
'''
        self._is_running = True
        self.btn_stop.setEnabled(True)
        self.operation_panel.set_operations_enabled(False)
        self.progress_bar.setValue(0)
        self.fdl_indicator.set_loaded(False)
        self.port_label.setText('Porta: escutando...')
        self.port_label.setStyleSheet(f'\n            QLabel {{\n                color: {Cores.WARNING};\n                font-size: 11px;\n                font-weight: bold;\n                padding: 4px 8px;\n                border: 1px solid {Cores.WARNING};\n                border-radius: 4px;\n                background-color: #fef9e7;\n            }}\n        ')
        self.terminal.clear_logs()
        mc = self._model_config
        try:
            use_adv = bool(self.chk_advanced.isChecked())
        except Exception:
            use_adv = True
        if not use_adv:
            self.terminal.log('Autorizacao avancada: DESLIGADA (fluxo padrao FDL1+FDL2)', 'info')
        force_kick = False
        try:
            force_kick = bool(self.chk_force.isChecked())
        except Exception:
            pass
        if force_kick:
            self.terminal.log('Force ativado ÔÇö spd_dump com --kick (rota boot_diag -> cali_diag -> dl_diag)', 'info')
        self._worker = SPDFullWorker(operation=operation, model_config=mc, engine=engine, timeout=timeout, use_advanced_auth=use_adv, force_kick=force_kick, parent=self)
        self._worker.log_signal.connect(self._on_worker_log)
        self._worker.progress_signal.connect(self._on_worker_progress)
        self._worker.status_signal.connect(self._on_worker_status)
        self._worker.fdl_loaded_signal.connect(self._on_fdl_loaded)
        self._worker.device_found_signal.connect(self._on_device_found)
        self._worker.finished_signal.connect(self._on_worker_finished)
        self._worker.start()
    def _on_worker_finished(self, success: bool, message: str):
        '''Callback quando o worker completo termina.'''
        self._finish(success, message)
    @pyqtSlot(bool)
    def _sync_advanced_to_partition(self, checked: bool):
        '''Espelha estado do checkbox Operacoes -> Particoes.'''
        try:
            pt_chk = self.partition_tab.chk_advanced
            if pt_chk.isChecked() != checked:
                pt_chk.blockSignals(True)
                pt_chk.setChecked(checked)
                pt_chk.blockSignals(False)
                return
        except Exception:
            pass
    @pyqtSlot(bool)
    def _sync_advanced_from_partition(self, checked: bool):
        '''Espelha estado do checkbox Particoes -> Operacoes.'''
        try:
            if self.chk_advanced.isChecked() != checked:
                self.chk_advanced.blockSignals(True)
                self.chk_advanced.setChecked(checked)
                self.chk_advanced.blockSignals(False)
                return
        except Exception:
            pass
    @pyqtSlot(bool)
    def _sync_force_to_partition(self, checked: bool):
        '''Espelha Force: Operacoes -> Particoes.'''
        try:
            pt_chk = self.partition_tab.chk_force
            if pt_chk.isChecked() != checked:
                pt_chk.blockSignals(True)
                pt_chk.setChecked(checked)
                pt_chk.blockSignals(False)
                return
        except Exception:
            pass
    @pyqtSlot(bool)
    def _sync_force_from_partition(self, checked: bool):
        '''Espelha Force: Particoes -> Operacoes.'''
        try:
            if self.chk_force.isChecked() != checked:
                self.chk_force.blockSignals(True)
                self.chk_force.setChecked(checked)
                self.chk_force.blockSignals(False)
                return
        except Exception:
            pass
    def _finish(self, success: bool, message: str):
        '''
        Finaliza opera├º├úo e restaura UI.
        Guard idempotente: se `_is_running` ja for False, sai imediatamente.
        Motivo: existem 2 callers legitimos (`_on_worker_finished` e
        `_on_stop`) que podem disparar em sequencia no cancelamento ÔÇö
        `_on_stop` chama `_finish` diretamente para dar feedback visual
        imediato, e depois o worker termina naturalmente e emite
        `finished_signal` que cai em `_on_worker_finished -> _finish`
        de novo. Sem o guard, terminal + footer + progress_bar pintam 2x.
        Fallback: fluxo normal (sucesso unico) tem `_is_running=True`
        antes do primeiro `_finish`, entao passa pelo guard e executa
        como sempre ÔÇö sem regressao.
        '''
        if not self._is_running:
            return
        self._is_running = False
        self.btn_stop.setEnabled(False)
        self.operation_panel.set_operations_enabled(True)
        self.progress_bar.setValue(100 if success else 0)
        if success:
            self.terminal.log('', 'info')
            self.terminal.log('=============================================', 'success')
            self.terminal.log('  OPERACAO CONCLUIDA COM SUCESSO', 'success')
            self.terminal.log('=============================================', 'success')
            self.response_label.set_response('Concluido')
            return
        self.terminal.log('', 'info')
        self.terminal.log(f'Falha: {message}', 'error')
        self.response_label.set_response(message, is_error=True)
    def _on_stop(self):
        '''
Bot├úo STOP pressionado ÔÇö cancela aba ativa.
     cts.Cancel() ÔåÆ Thread.Sleep(3000) ÔåÆ CkFDLLoaded = false
'''
        current_tab = self.tab_widget.currentIndex()
        if current_tab == 1:
            self.partition_tab._on_cancel()
            return
        if self._worker and self._worker.isRunning():
            self._worker.stop()
        self.terminal.log('Operacao cancelada pelo usuario', 'warning')
        self.fdl_indicator.set_loaded(False)
        self._finish(False, 'Cancelado pelo usuario')
    def _on_worker_log(self, message: str, tipo: str):
        '''Recebe log do worker.'''
        if tipo == 'label_value':
            parts = message.split(':', 1)
            if len(parts) == 2:
                self.terminal.log_pair(parts[0].strip(), parts[1].strip())
                return
            self.terminal.log(message, 'info')
            return
        self.terminal.log(message, tipo)
    def _on_worker_progress(self, current: int, total: int):
        '''Recebe progresso do worker.'''
        self.progress_bar.set_progress(current, total)
    def _on_worker_status(self, status: str):
        '''Recebe status do worker.'''
        self.response_label.set_response(status)
    def _on_device_found(self, port: str):
        '''
        Dispositivo SPD detectado automaticamente.
        Atualiza label da porta com a porta detectada.
        '''
        self.port_label.setText(f'Porta: {port}')
        self.port_label.setStyleSheet(f'\n            QLabel {{\n                color: {Cores.SUCCESS};\n                font-size: 11px;\n                font-weight: bold;\n                padding: 4px 8px;\n                border: 1px solid {Cores.SUCCESS};\n                border-radius: 4px;\n                background-color: #eafaf1;\n            }}\n        ')
    def _on_fdl_loaded(self, loaded: bool):
        '''
        FDL carregado.
        '''
        self.fdl_indicator.set_loaded(loaded)
    def _get_current_model_config(self):
        '''Retorna o ModelConfig selecionado ÔÇö usado pela PartitionTab.'''
        return self._model_config
