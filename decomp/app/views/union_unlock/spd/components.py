'''
Componentes GUI reutilizaveis (PyQt5).
Ver: alan/documentacao/16-08-2026-ARQUITETURA-SPD-INTERNA/01_MAPA_REFERENCIAS_INTERNAS.md
'''
from PyQt5.QtWidgets import (QWidget, QTextEdit, QPushButton, QProgressBar, QLabel, QFrame, QComboBox, QListWidget, QLineEdit, QVBoxLayout, QHBoxLayout, QGroupBox, QSizePolicy)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import (QFont, QColor, QTextCharFormat, QTextCursor)
class Cores:
    '''Paleta de cores para o m├│dulo SPD UNION.'''
    PRIMARY = '#2471a3'
    PRIMARY_HOVER = '#1a5276'
    PRIMARY_DARK = '#154360'
    BACKGROUND = '#f5f5f5'
    SURFACE = '#ffffff'
    TEXT = '#2c3e50'
    TEXT_MUTED = '#7f8c8d'
    SUCCESS = '#27ae60'
    ERROR = '#e74c3c'
    WARNING = '#f39c12'
    TERMINAL_BG = '#1e272e'
    TERMINAL_TEXT = '#dcdde1'
    BORDER = '#d5d8dc'
class TerminalLog(QTextEdit):
    '''
Terminal de logs com fundo escuro e cores por tipo.
     Font: Consolas 8.25pt, BorderStyle.FixedSingle
     Suporta cores diferentes e bold por trecho.
Adapta├º├úo: QTextEdit readonly com fundo escuro e HTML colorido.
'''
    COLOR_MAP = {'info': Cores.TERMINAL_TEXT, 'success': Cores.SUCCESS, 'error': Cores.ERROR, 'warning': Cores.WARNING, 'label': '#ffffff', 'value': '#a29bfe', 'op': '#fdcb6e', 'debug': '#636e72', 'footer_line': '#3498db', 'footer_title': '#ffffff', 'footer_time': '#95a5a6'}
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont('Consolas', 9))
        self.setStyleSheet(f'\n            QTextEdit {{\n                background-color: {Cores.TERMINAL_BG};\n                color: {Cores.TERMINAL_TEXT};\n                border: 1px solid {Cores.BORDER};\n                border-radius: 4px;\n                padding: 6px;\n            }}\n        ')
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    def log(self, msg: str, tipo: str='info', bold: bool=False, newline: bool=True):
        """
        Adiciona mensagem ao terminal com cor e estilo.
        Escapa HTML da mensagem para impedir renderizacao acidental de
        tracebacks Python (`<module 'xxx'>`), tags ou caracteres especiais
        que podem quebrar o layout ou vazar estrutura interna.
        """
        import html as _html
        color = self.COLOR_MAP.get(tipo, Cores.TERMINAL_TEXT)
        safe_msg = _html.escape(msg, quote=False)
        if tipo == 'footer_line':
            html = f'<hr style="border:none; height:2px; background-color:{color}; margin:8px 0 4px 0;">'
        elif tipo == 'footer_title':
            html = f'<span style="color:{color}; font-weight:bold; font-size:11pt;">{safe_msg}</span>'
            if newline:
                html += '<br>'
        elif tipo == 'footer_time':
            html = f'<span style="color:{color}; font-size:9pt;">{safe_msg}</span>'
            if newline:
                html += '<br>'
        else:
            weight = 'bold' if bold else 'normal'
            html = f'<span style="color:{color}; font-weight:{weight}">{safe_msg}</span>'
            if newline:
                html += '<br>'
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)
        self.insertHtml(html)
        self.ensureCursorVisible()
    def log_pair(self, label: str, value: str, value_tipo: str='value'):
        '''
Loga um par label: valor (padr├úo ).
     MyDisplay.RichLogs("Operation    : ", Color.Black, true, false)
     MyDisplay.RichLogs(str, Color.Orange, true, true)
'''
        self.log(f'{label}: ', tipo='label', bold=True, newline=False)
        self.log(value, tipo=value_tipo, bold=True, newline=True)
    def log_separator(self):
        '''Adiciona linha separadora.'''
        self.log('ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ', tipo='debug', bold=False)
    def clear_logs(self):
        '''
        Limpa o terminal.
        '''
        self.clear()
class ActionButton(QPushButton):
    '''
Bot├úo de a├º├úo prim├írio estilo UNION.
     Size(212, 23), ForeColor(64,64,64), TextAlign.MiddleLeft
'''
    def __init__(self, text: str, primary: bool=True, parent=None):
        super().__init__(text, parent)
        if primary:
            self.setStyleSheet(f'\n                QPushButton {{\n                    background-color: {Cores.PRIMARY};\n                    color: white;\n                    border: none;\n                    border-radius: 6px;\n                    padding: 8px 16px;\n                    font-weight: bold;\n                    font-size: 12px;\n                }}\n                QPushButton:hover {{\n                    background-color: {Cores.PRIMARY_HOVER};\n                }}\n                QPushButton:pressed {{\n                    background-color: {Cores.PRIMARY_DARK};\n                }}\n                QPushButton:disabled {{\n                    background-color: #bdc3c7;\n                    color: #7f8c8d;\n                }}\n            ')
            return
        self.setStyleSheet(f'\n                QPushButton {{\n                    background-color: #ecf0f1;\n                    color: {Cores.TEXT};\n                    border: 1px solid {Cores.BORDER};\n                    border-radius: 6px;\n                    padding: 8px 16px;\n                    font-size: 12px;\n                }}\n                QPushButton:hover {{\n                    background-color: #d5d8dc;\n                }}\n                QPushButton:pressed {{\n                    background-color: #bdc3c7;\n                }}\n                QPushButton:disabled {{\n                    background-color: #f0f0f0;\n                    color: #bdc3c7;\n                }}\n            ')
class DangerButton(QPushButton):
    '''
    Bot├úo de a├º├úo perigosa (STOP, etc).
    '''
    def __init__(self, text: str='STOP', parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f'\n            QPushButton {{\n                background-color: {Cores.ERROR};\n                color: white;\n                border: none;\n                border-radius: 6px;\n                padding: 8px 16px;\n                font-weight: bold;\n                font-size: 12px;\n            }}\n            QPushButton:hover {{\n                background-color: #c0392b;\n            }}\n            QPushButton:pressed {{\n                background-color: #a93226;\n            }}\n            QPushButton:disabled {{\n                background-color: #bdc3c7;\n                color: #7f8c8d;\n            }}\n        ')
class StatusBar(QProgressBar):
    '''
Barra de progresso estilo UNION.
     Size(763, 23), Value=100
     val = Process * 100 / total
'''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(20)
        self.setTextVisible(False)
        self.setRange(0, 100)
        self.setValue(0)
        self.setStyleSheet(f'\n            QProgressBar {{\n                background-color: #ecf0f1;\n                border: none;\n                border-radius: 4px;\n            }}\n            QProgressBar::chunk {{\n                background-color: {Cores.PRIMARY};\n                border-radius: 4px;\n            }}\n        ')
    def set_progress(self, current: int, total: int):
        '''
        Atualiza progresso.
        '''
        if total > 0:
            val = min(int(current * 100 / total), 100)
            self.setValue(val)
            return
        self.setValue(0)
class DeviceListBox(QGroupBox):
    '''
GroupBox com dropdown de Marca + Modelo + busca + lista.
Contrato:
  - Combo Marca: lista as marcas do banco. `CPU` (marca virtual das
    Tigers universais) e auto-selecionada na primeira carga para
    oferecer os SoCs universais como ponto de partida. Usuario pode
    mudar para qualquer outra marca real (Realme, Motorola, etc).
  - Combo Modelo: filtrado pela marca. Selecionar o modelo aqui
    seleciona automaticamente o item correspondente na lista abaixo.
  - Busca: filtra apenas a lista (nao mexe nos combos).
  - Lista: mesma lista visual de sempre (display + chipset em 2 linhas).
Layout:
  ÔöîÔöÇ Dispositivos ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ
  Ôöé [Marca   Ôû╝]  CPU      Ôöé
  Ôöé [Modelo  Ôû╝]           Ôöé
  Ôöé [Buscar modelo...]    Ôöé
  Ôöé ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉÔöé
  Ôöé Ôöé Tiger_T616_64      ÔöéÔöé
  Ôöé Ôöé   UMS9230          ÔöéÔöé
  Ôöé ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿÔöé
  ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ
'''
    def __init__(self, parent=None):
        super().__init__('Dispositivos', parent)
        self.setStyleSheet(f'\n            QGroupBox {{\n                font-weight: bold;\n                font-size: 12px;\n                color: {Cores.TEXT};\n                border: 1px solid {Cores.BORDER};\n                border-radius: 6px;\n                margin-top: 8px;\n                padding-top: 16px;\n            }}\n            QGroupBox::title {{\n                subcontrol-origin: margin;\n                left: 10px;\n                padding: 0 4px;\n            }}\n        ')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 20, 6, 6)
        layout.setSpacing(4)
        try:
            from app.views.union_unlock.spd.config import SVG_SETA_DOWN
            _svg = SVG_SETA_DOWN.replace('\\', '/')
        except Exception:
            _svg = ''
        _arrow_rule = f'QComboBox::down-arrow {{ image: url("{_svg}"); width: 10px; height: 10px; }}' if _svg else ''
        combo_style = f'\n            QComboBox {{\n                border: 1px solid {Cores.BORDER};\n                border-radius: 4px;\n                padding: 5px 24px 5px 8px;\n                font-size: 11px;\n                font-weight: bold;\n                background-color: white;\n                color: {Cores.TEXT};\n            }}\n            QComboBox:focus {{\n                border-color: {Cores.PRIMARY};\n            }}\n            QComboBox::drop-down {{\n                subcontrol-origin: padding; subcontrol-position: top right;\n                border-left: 1px solid {Cores.BORDER};\n                border-top-right-radius: 4px;\n                border-bottom-right-radius: 4px;\n                width: 22px; background-color: #ecf0f1;\n            }}\n            QComboBox::drop-down:hover {{ background-color: #d5dbdb; }}\n            {_arrow_rule}\n            QComboBox QAbstractItemView {{\n                background-color: white;\n                border: 1px solid {Cores.BORDER};\n                outline: none;\n                padding: 2px;\n                color: {Cores.TEXT};\n            }}\n            QComboBox QAbstractItemView::item {{\n                min-height: 22px;\n                padding: 4px 8px;\n                color: {Cores.TEXT};\n                background-color: white;\n            }}\n            QComboBox QAbstractItemView::item:hover {{\n                background-color: #d6e4f0;\n                color: {Cores.TEXT};\n            }}\n            QComboBox QAbstractItemView::item:selected {{\n                background-color: #d6e4f0;\n                color: {Cores.TEXT};\n            }}\n        '
        self.brand_combo = QComboBox()
        self.brand_combo.setStyleSheet(combo_style)
        self.brand_combo.addItem('-- Marca --')
        self.brand_combo.setToolTip("Selecione a marca. Por padrao inicia em 'CPU' (Tigers universais).")
        layout.addWidget(self.brand_combo)
        self.model_combo = QComboBox()
        self.model_combo.setStyleSheet(combo_style)
        self.model_combo.addItem('-- Modelo --')
        self.model_combo.setToolTip('Modelo filtrado pela marca. Selecionar aqui destaca o item na lista.')
        layout.addWidget(self.model_combo)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Buscar modelo...')
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setStyleSheet(f'\n            QLineEdit {{\n                background-color: white;\n                border: 1px solid {Cores.BORDER};\n                border-radius: 4px;\n                padding: 5px 8px;\n                font-size: 11px;\n                color: {Cores.TEXT};\n            }}\n            QLineEdit:focus {{\n                border-color: {Cores.PRIMARY};\n                background-color: #fdfdfd;\n            }}\n        ')
        layout.addWidget(self.search_input)
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f'\n            QListWidget {{\n                border: none;\n                font-size: 11px;\n                color: {Cores.TEXT};\n            }}\n            QListWidget::item {{\n                padding: 5px 6px;\n                border-bottom: 1px solid #f0f0f0;\n            }}\n            QListWidget::item:selected {{\n                background-color: #d6e4f0;\n                color: {Cores.TEXT};\n                border-left: 3px solid {Cores.PRIMARY};\n            }}\n            QListWidget::item:hover {{\n                background-color: #eaf2f8;\n            }}\n        ')
        layout.addWidget(self.list_widget)
        self._all_devices = []
        self._brand_devices = {}
        self._default_brand_applied = False
        self.search_input.textChanged.connect(self._filter)
        self.brand_combo.currentIndexChanged.connect(self._on_brand_changed)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
    def set_brands(self, brand_device_map: dict):
        """
Popula combo de marcas + lista. Auto-seleciona 'CPU' se disponivel.
Args:
    brand_device_map: {brand: [(display, chipset, data), ...]}
"""
        self._brand_devices = brand_device_map
        self._all_devices = []
        for devs in brand_device_map.values():
            self._all_devices.extend(devs)
        self.brand_combo.blockSignals(True)
        self.brand_combo.clear()
        self.brand_combo.addItem('-- Marca --')
        marcas = list(brand_device_map.keys())
        cpu_variants = [m for m in marcas if m.strip().upper() == 'CPU']
        outras = sorted((m for m in marcas if m.strip().upper() != 'CPU'))
        for b in cpu_variants + outras:
            self.brand_combo.addItem(b)
        self.brand_combo.blockSignals(False)
        if not self._default_brand_applied:
            if cpu_variants:
                idx = self.brand_combo.findText(cpu_variants[0])
                if idx > 0:
                    self._default_brand_applied = True
                    self.brand_combo.setCurrentIndex(idx)
                    return
        self._repopulate_by_brand()
    def _on_brand_changed(self, _idx: int):
        '''Marca mudou -> repopula combo Modelo + lista + limpa busca.'''
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)
        self._repopulate_by_brand()
    def _on_model_changed(self, idx: int):
        '''
        Modelo mudou no combo -> seleciona item correspondente na lista.
        Nao dispara _on_device_selected em cascata infinita porque
        list_widget.setCurrentItem trata como interacao do usuario.
        '''
        if idx <= 0:
            return
        modelo_texto = self.model_combo.currentText()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            display = item.text().split('\n', 1)[0].strip()
            if display != modelo_texto:
                continue
            if not item.isHidden():
                self.list_widget.setCurrentItem(item)
                self.list_widget.scrollToItem(item)
            return
    def _repopulate_by_brand(self):
        '''Repopula lista e combo Modelo a partir da marca selecionada.'''
        brand_idx = self.brand_combo.currentIndex()
        if brand_idx <= 0:
            devices = self._all_devices
        else:
            brand = self.brand_combo.currentText()
            devices = self._brand_devices.get(brand, [])
        self.list_widget.clear()
        self._populate_list(devices)
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        self.model_combo.addItem('-- Modelo --')
        for display, _chipset, _data in devices:
            self.model_combo.addItem(display)
        self.model_combo.blockSignals(False)
    def _populate_list(self, devices):
        from PyQt5.QtWidgets import QListWidgetItem
        from PyQt5.QtGui import QFont as _QFont
        for display, chipset, data in devices:
            text = display
            if chipset:
                text += f'\n   {chipset}'
            item = QListWidgetItem(text)
            item.setFont(_QFont('Segoe UI', 10))
            if data is not None:
                item.setData(Qt.UserRole, data)
            self.list_widget.addItem(item)
    def _filter(self, text: str):
        text_lower = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            visible = text_lower in item.text().lower()
            item.setHidden(not visible)
            if not visible:
                continue
            if text:
                self.list_widget.setCurrentItem(item)
    def add_device(self, display_text: str, data=None):
        '''Retrocompatibilidade ÔÇö adiciona dispositivo flat.'''
        from PyQt5.QtWidgets import QListWidgetItem
        item = QListWidgetItem(display_text)
        if data is not None:
            item.setData(Qt.UserRole, data)
        self.list_widget.addItem(item)
class OperationPanel(QGroupBox):
    '''
Painel de opera├º├Áes com bot├Áes din├ómicos.
     PanelSPDOneClick (214x341) + comboBoxTimeout
     Button(212x23) para cada opera├º├úo do .txt
'''
    def __init__(self, parent=None):
        super().__init__('Opera├º├Áes', parent)
        self.setStyleSheet(f'\n            QGroupBox {{\n                font-weight: bold;\n                font-size: 12px;\n                color: {Cores.TEXT};\n                border: 1px solid {Cores.BORDER};\n                border-radius: 6px;\n                margin-top: 8px;\n                padding-top: 16px;\n            }}\n            QGroupBox::title {{\n                subcontrol-origin: margin;\n                left: 10px;\n                padding: 0 4px;\n            }}\n        ')
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(6, 20, 6, 6)
        self._layout.setSpacing(6)
        self.timeout_combo = QComboBox()
        self.timeout_combo.addItems(['Timeout - 500 ms', 'Timeout - 1000 ms', 'Timeout - 1500 ms', 'Timeout - 2000 ms', 'Timeout - 3000 ms'])
        self.timeout_combo.setCurrentIndex(0)
        self.timeout_combo.setStyleSheet(f'\n            QComboBox {{\n                border: 1px solid {Cores.BORDER};\n                border-radius: 4px;\n                padding: 4px 8px;\n                font-size: 11px;\n                background-color: white;\n                color: {Cores.TEXT};\n            }}\n            QComboBox QAbstractItemView {{\n                background-color: white;\n                color: {Cores.TEXT};\n                outline: none;\n            }}\n            QComboBox QAbstractItemView::item {{\n                min-height: 22px;\n                color: {Cores.TEXT};\n                background-color: white;\n            }}\n            QComboBox QAbstractItemView::item:hover {{\n                background-color: #d6e4f0;\n                color: {Cores.TEXT};\n            }}\n            QComboBox QAbstractItemView::item:selected {{\n                background-color: #d6e4f0;\n                color: {Cores.TEXT};\n            }}\n        ')
        self._layout.addWidget(self.timeout_combo)
        self._buttons_container = QVBoxLayout()
        self._layout.addLayout(self._buttons_container)
        self._layout.addStretch()
        self._operation_buttons = []
    def clear_operations(self):
        '''
        Remove todos os bot├Áes de opera├º├úo.
        '''
        for btn in self._operation_buttons:
            btn.deleteLater()
        self._operation_buttons.clear()
    def add_operation(self, name: str, callback=None) -> ActionButton:
        '''
Adiciona um bot├úo de opera├º├úo.
     Size(212, 23), Text = operation name, Click += SPDDoExecOneClick
'''
        btn = ActionButton(name, primary=True)
        btn.setFixedHeight(32)
        if callback:
            btn.clicked.connect((lambda checked, n=name: callback(n)))
        self._buttons_container.addWidget(btn)
        self._operation_buttons.append(btn)
        return btn
    def set_operations_enabled(self, enabled: bool):
        '''Habilita/desabilita todos os bot├Áes de opera├º├úo.'''
        for btn in self._operation_buttons:
            btn.setEnabled(enabled)
    def get_timeout_ms(self) -> int:
        '''
Retorna timeout selecionado em ms.
     Parseia "Timeout - 500 ms" ÔåÆ 500
'''
        text = self.timeout_combo.currentText()
        try:
            return int(text.replace('Timeout', '').replace('-', '').replace('ms', '').strip())
        except ValueError:
            return 500
class PortComboBox(QComboBox):
    '''
ComboBox de portas COM.
     Size(420, 21), BackColor=SeaShell
     Regex.Match(Text, @"\\((COM\\d+)\\)")
'''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f'\n            QComboBox {{\n                background-color: #fef9f0;\n                border: 1px solid {Cores.BORDER};\n                border-radius: 4px;\n                padding: 4px 8px;\n                font-size: 11px;\n                min-height: 24px;\n            }}\n            QComboBox:focus {{\n                border-color: {Cores.PRIMARY};\n            }}\n        ')
        self.setEditable(False)
        self.addItem('Selecione a porta COM...')
    def set_ports(self, ports: list):
        '''Atualiza lista de portas dispon├¡veis.'''
        current = self.currentText()
        self.clear()
        self.addItem('Selecione a porta COM...')
        for port_info in ports:
            self.addItem(str(port_info))
        idx = self.findText(current)
        if idx >= 0:
            self.setCurrentIndex(idx)
class ResponseLabel(QLabel):
    '''
    Label de resposta do protocolo.
    '''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f'\n            QLabel {{\n                color: {Cores.TEXT_MUTED};\n                font-size: 11px;\n                padding: 2px 0;\n            }}\n        ')
        self.setText('Response: Aguardando...')
    def set_response(self, text: str, is_error: bool=False):
        '''
        Atualiza texto de resposta.
        '''
        color = Cores.ERROR if is_error else Cores.TEXT_MUTED
        self.setStyleSheet(f'QLabel {{ color: {color}; font-size: 11px; padding: 2px 0; }}')
        self.setText(f'Response: {text}')
class FDLIndicator(QLabel):
    '''
Indicador de FDL carregado.
     CheckBox "FDL Loaded"
'''
    def __init__(self, parent=None):
        super().__init__(parent)
        self._loaded = False
        self._update_style()
    def _update_style(self):
        if self._loaded:
            self.setText('FDL Loaded')
            self.setStyleSheet(f'\n                QLabel {{\n                    color: {Cores.SUCCESS};\n                    font-weight: bold;\n                    font-size: 11px;\n                }}\n            ')
            return
        self.setText('FDL Not Loaded')
        self.setStyleSheet(f'\n                QLabel {{\n                    color: {Cores.TEXT_MUTED};\n                    font-size: 11px;\n                }}\n            ')
    def set_loaded(self, loaded: bool):
        '''
        Define estado do indicador.
        '''
        self._loaded = loaded
        self._update_style()
