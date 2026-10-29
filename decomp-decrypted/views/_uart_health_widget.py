import os
from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QWidget, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
try:
    from app.views.union_unlock.hxd.gui.tema import (BG, BG_WHITE, BG_TAB_PANE, PRIMARY, UNION_BLUE, UNION_ACCENT, BORDER, BORDER_LIGHT, TEXT, TEXT_MUTED, TEXT_LABEL, GREEN, RED, ORANGE, WHITE)
except ImportError:
    BG = '#f5f5f5'
    BG_WHITE = '#ffffff'
    BG_TAB_PANE = '#f7f9fc'
    PRIMARY = '#1428A0'
    UNION_BLUE = '#0D47A1'
    UNION_ACCENT = '#2196F3'
    BORDER = '#bdc3c7'
    BORDER_LIGHT = '#c5d6ec'
    TEXT = '#2c3e50'
    TEXT_MUTED = '#7f8c8d'
    TEXT_LABEL = '#3a4a63'
    GREEN = '#27ae60'
    RED = '#e53935'
    ORANGE = '#FF9800'
    WHITE = '#ffffff'
STATE_PENDING = 'pending'
STATE_RUNNING = 'running'
STATE_OK = 'ok'
STATE_ERROR = 'error'
STATE_WARN = 'warn'
_BADGE_STYLE = {STATE_PENDING: {'bg': '#e0e0e0', 'fg': '#7a7a7a', 'text_default': 'nao testado'}, STATE_RUNNING: {'bg': UNION_ACCENT, 'fg': WHITE, 'text_default': 'analisando...'}, STATE_OK: {'bg': GREEN, 'fg': WHITE, 'text_default': 'OK'}, STATE_ERROR: {'bg': RED, 'fg': WHITE, 'text_default': 'ERRO'}, STATE_WARN: {'bg': ORANGE, 'fg': WHITE, 'text_default': 'AVISO'}}
_SVG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources', 'icons_svg')
def _svg(name):
    p = os.path.join(_SVG_DIR, name)
    if os.path.isfile(p):
        return p
    return ''
_CARD_ICONS = {'battery': _svg('shield-check.svg'), 'power_key': _svg('shield-lock.svg'), 'pmic': _svg('shield-check.svg'), 'pmic_sec': _svg('shield-check.svg'), 'memory': _svg('motherboard.svg'), 'storage': _svg('motherboard.svg'), 'i2c': _svg('cpu.svg'), 'rtc': _svg('shield-check.svg'), 'cpu': _svg('cpu.svg'), 'pwrap': _svg('cpu.svg'), 'spmi': _svg('cpu.svg'), 'clocks': _svg('cpu.svg'), 'watchdog': _svg('shield-lock.svg'), 'atf': _svg('shield-lock.svg'), 'boot': _svg('terminal.svg')}
_SECTION_ICON = _svg('card-checklist.svg')
_SUBSYSTEM_ORDER_ESSENTIAL = ['battery', 'power_key', 'pmic', 'pmic_sec', 'memory', 'storage', 'i2c', 'rtc']
_SUBSYSTEM_ORDER_ADVANCED = ['cpu', 'pwrap', 'spmi', 'clocks', 'watchdog', 'atf', 'boot']
_SUBSYSTEM_ORDER = _SUBSYSTEM_ORDER_ESSENTIAL + _SUBSYSTEM_ORDER_ADVANCED
_SUBSYSTEM_NAMES = {'battery': 'Bateria (VBAT)', 'power_key': 'Botao Power', 'pmic': 'Alimentacao Principal (PMIC)', 'pmic_sec': 'Carga USB / Bateria (Sub-PMIC)', 'memory': 'Memoria RAM', 'storage': 'Memoria Interna (UFS/eMMC)', 'i2c': 'Barramento I2C', 'rtc': 'Relogio RTC (Data/Hora)', 'cpu': 'Processador (CPU/SoC)', 'pwrap': 'Barramento PMIC (PWRAP)', 'spmi': 'Barramento PMIC (SPMI)', 'clocks': 'Clocks / Frequencia (PLL)', 'watchdog': 'Watchdog (Timer)', 'atf': 'Seguranca (ATF/TEE)', 'boot': 'Inicializacao (Boot LK/Kernel)'}
def _voltage_sort_key(name):
    n = name.upper()
    if n.startswith('VBAT') or n.startswith('VCHR'):
        return 0, name
    if any((n.startswith(p) for p in ('VCORE', 'VGPU', 'VPROC', 'VRF', 'VMODEM'))):
        return 1, name
    if 'VSRAM' in n:
        return 2, name
    if n.startswith('VBUCK') or n.startswith('VS2'):
        return 3, name
    if n.startswith('DDR_'):
        return 4, name
    if n.startswith('VAUX') or n.startswith('VBG'):
        return 5, name
    if 'MT63' in n or 'MT69' in n or 'MT6315' in n:
        return 6, name
    return 7, name
def _make_font(size_px, bold=False):
    f = QFont('Segoe UI, Calibri, sans-serif')
    f.setPixelSize(size_px)
    if bold:
        f.setWeight(QFont.DemiBold)
    return f
def _create_svg_label(svg_path, size=16):
    lbl = QLabel()
    lbl.setFixedSize(size, size)
    lbl.setStyleSheet('border: none; background: transparent; padding: 0;')
    try:
        if svg_path and os.path.isfile(svg_path):
            pix = QPixmap(svg_path)
            if not pix.isNull():
                lbl.setPixmap(pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    except Exception:
        pass
    return lbl
class SubsystemCard(QFrame):
    def __init__(self, key, display_name, icon_path='', profile=None, parent=None):
        super().__init__(parent)
        self._key = key
        self._profile = profile or {}
        self._display_name = display_name
        self._icon_path = icon_path
        self._state = STATE_PENDING
        self._detail = ''
        self._build()
    def _build(self):
        p = self._profile
        font_body = max(11, p.get('body_font', 11))
        font_small = max(10, p.get('small_font', 10))
        icon_px = max(14, int(font_body * 1.2))
        icon_col_w = icon_px + 4
        card_h_min = max(40, int(font_body * 3.6))
        card_h_max = max(56, int(font_body * 5.0))
        badge_w_max = max(130, int(font_small * 13))
        badge_w_min = max(90, int(font_small * 9))
        badge_h = max(24, int(font_small * 2.4))
        pad_h = max(6, int(font_body * 0.5))
        pad_v = max(4, int(font_body * 0.45))
        self._badge_char_cap = max(12, int(badge_w_min / max(5, font_small * 0.55)))
        self.setObjectName(f'sub_card_{self._key}')
        self.setStyleSheet(f'\n            QFrame#sub_card_{self._key} {{\n                background-color: {BG_WHITE};\n                border: 1px solid {BORDER_LIGHT};\n                border-radius: 4px;\n            }}\n        ')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumHeight(card_h_min)
        self.setMaximumHeight(card_h_max)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(pad_h, pad_v, pad_h, pad_v)
        lay.setSpacing(max(4, int(font_body * 0.45)))
        if self._icon_path:
            icon_lbl = _create_svg_label(self._icon_path, icon_px)
            icon_lbl.setFixedSize(icon_col_w, icon_px)
            icon_lbl.setStyleSheet('background: transparent; border: none;')
            lay.addWidget(icon_lbl, 0, Qt.AlignVCenter)
        else:
            spacer = QLabel('')
            spacer.setFixedSize(icon_col_w, icon_px)
            spacer.setStyleSheet('background: transparent; border: none;')
            lay.addWidget(spacer, 0, Qt.AlignVCenter)
        self._name_lbl = QLabel(self._display_name)
        self._name_lbl.setFont(_make_font(font_body, bold=True))
        self._name_lbl.setWordWrap(True)
        self._name_lbl.setStyleSheet(f'QLabel {{ color: {TEXT}; border: none; background: transparent; }}')
        self._name_lbl.setMinimumHeight(max(20, int(font_body * 1.8)))
        self._name_lbl.setMinimumWidth(max(100, int(font_body * 10)))
        self._name_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self._name_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._name_lbl.setToolTip(self._display_name)
        lay.addWidget(self._name_lbl, 1, Qt.AlignVCenter)
        self._badge = QLabel(_BADGE_STYLE[STATE_PENDING]['text_default'])
        self._badge.setFont(_make_font(font_small, bold=True))
        self._badge.setAlignment(Qt.AlignCenter)
        self._badge.setMinimumWidth(badge_w_min)
        self._badge.setMaximumWidth(badge_w_max)
        self._badge.setFixedHeight(badge_h)
        self._badge.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self._apply_badge_style(STATE_PENDING, _BADGE_STYLE[STATE_PENDING]['text_default'])
        lay.addWidget(self._badge, 0, Qt.AlignVCenter | Qt.AlignRight)
    def _apply_badge_style(self, state, text):
        style = _BADGE_STYLE.get(state, _BADGE_STYLE[STATE_PENDING])
        self._badge.setText(text)
        self._badge.setStyleSheet(f'\n            QLabel {{\n                background-color: {style['bg']};\n                color: {style['fg']};\n                border-radius: 4px;\n                padding: 3px 10px;\n                border: none;\n            }}\n        ')
    def set_state(self, state, detail=''):
        if state not in _BADGE_STYLE:
            state = STATE_PENDING
        self._state = state
        self._detail = detail
        text = detail.strip() if detail else _BADGE_STYLE[state]['text_default']
        cap = getattr(self, '_badge_char_cap', 18)
        if len(text) > cap:
            text = text[:max(6, cap - 2)] + 'ÔÇª'
        try:
            self._badge.setToolTip(detail if detail else '')
        except Exception:
            pass
        self._apply_badge_style(state, text)
    def get_state(self):
        return self._state
class UartHealthPanel(QFrame):
    def __init__(self, profile=None, parent=None):
        super().__init__(parent)
        self._profile = profile or {}
        self._cards = {}
        self._extra_sections = {}
        self._extra_layouts = {}
        self._extra_placeholders = {}
        self._setup_ui()
    def _setup_ui(self):
        p = self._profile
        font_title = p.get('title_font', 13)
        font_body = p.get('body_font', 11)
        font_small = p.get('small_font', 10)
        self.setObjectName('uart_health_panel')
        self.setStyleSheet(f'\n            QFrame#uart_health_panel {{\n                background-color: {BG};\n                border: 1px solid {BORDER_LIGHT};\n                border-radius: 6px;\n            }}\n        ')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self._build_header(font_title, font_small))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f'\n            QScrollArea {{ border: none; background: transparent; }}\n            QScrollBar:vertical {{\n                background: {BG}; width: 6px; border-radius: 3px;\n            }}\n            QScrollBar::handle:vertical {{\n                background: {BORDER}; border-radius: 3px; min-height: 20px;\n            }}\n            QScrollBar::handle:vertical:hover {{ background: {UNION_ACCENT}; }}\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}\n        ')
        content = QWidget()
        content.setStyleSheet('background: transparent;')
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(4, 6, 4, 6)
        content_lay.setSpacing(8)
        content_lay.addWidget(self._build_subsystems_block('essential', 'Diagnostico Rapido', _SUBSYSTEM_ORDER_ESSENTIAL, font_body, font_small))
        hint = QLabel('Alguns testes podem ficar como "analisando..." se o aparelho nao gerar essa informacao no boot atual.')
        hint.setFont(_make_font(font_small - 1))
        hint.setWordWrap(True)
        hint.setStyleSheet(f'QLabel {{ color: {TEXT_MUTED}; background: transparent; border: none; padding: 2px 8px 6px 8px; font-style: italic; }}')
        content_lay.addWidget(hint)
        failures_block = self._build_extra_section('failures', 'Falhas Detectadas', 'Nenhuma falha detectada', RED, font_body, font_small)
        content_lay.addWidget(failures_block)
        failures_block.setVisible(False)
        content_lay.addWidget(self._build_subsystems_block('advanced', 'Infraestrutura do SoC', _SUBSYSTEM_ORDER_ADVANCED, font_body, font_small))
        freq_block = self._build_extra_section('frequencies', 'Frequencias', 'Aguardando dados de clock...', UNION_BLUE, font_body, font_small)
        content_lay.addWidget(freq_block)
        volt_block = self._build_extra_section('voltages', 'Tensoes', 'Aguardando leitura de tensao...', UNION_BLUE, font_body, font_small)
        content_lay.addWidget(volt_block)
        comm_block = self._build_extra_section('communications', 'Comunicacoes', 'Aguardando dados de barramento...', UNION_BLUE, font_body, font_small)
        content_lay.addWidget(comm_block)
        boot_block = self._build_extra_section('boot_storage', 'Boot / Storage', 'Aguardando informacoes de boot...', UNION_BLUE, font_body, font_small)
        content_lay.addWidget(boot_block)
        content_lay.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
    def _build_header(self, font_title, font_small):
        header = QFrame()
        header.setStyleSheet(f'\n            QFrame {{\n                background-color: {BG_TAB_PANE};\n                border: none;\n                border-bottom: 2px solid {UNION_BLUE};\n                border-top-left-radius: 6px;\n                border-top-right-radius: 6px;\n            }}\n        ')
        header_lay = QHBoxLayout(header)
        header_lay.setContentsMargins(10, 6, 10, 6)
        if _SECTION_ICON:
            header_lay.addWidget(_create_svg_label(_SECTION_ICON, 18))
        title = QLabel('Diagnostico')
        title.setFont(_make_font(font_title, bold=True))
        title.setStyleSheet(f'\n            QLabel {{ color: {PRIMARY}; border: none;\n                     background: transparent; padding: 0 4px; }}\n        ')
        header_lay.addWidget(title)
        header_lay.addStretch()
        self._status_label = QLabel('Pendente')
        self._status_label.setFont(_make_font(font_small))
        self._status_label.setStyleSheet(f'\n            QLabel {{ color: {TEXT_MUTED}; border: none;\n                     background: transparent; padding: 0 4px; }}\n        ')
        header_lay.addWidget(self._status_label)
        return header
    def _build_subsystems_block(self, block_id, title_text, subsystem_keys, font_body, font_small):
        block = QFrame()
        block.setObjectName(f'subsystems_block_{block_id}')
        block.setStyleSheet(f'\n            QFrame#subsystems_block_{block_id} {{\n                background-color: {BG_WHITE};\n                border: 1px solid {BORDER_LIGHT};\n                border-radius: 6px;\n            }}\n        ')
        lay = QVBoxLayout(block)
        lay.setContentsMargins(0, 0, 0, 6)
        lay.setSpacing(0)
        sec_header = QFrame()
        sec_header.setStyleSheet(f'\n            QFrame {{\n                background-color: {BG_TAB_PANE};\n                border: none;\n                border-bottom: 1px solid {BORDER_LIGHT};\n                border-top-left-radius: 6px;\n                border-top-right-radius: 6px;\n            }}\n        ')
        sec_h_lay = QHBoxLayout(sec_header)
        sec_h_lay.setContentsMargins(6, 4, 6, 4)
        sec_title = QLabel(title_text)
        sec_title.setFont(_make_font(font_body, bold=True))
        sec_title.setStyleSheet(f'QLabel {{ color: {UNION_BLUE}; border: none; background: transparent; }}')
        sec_h_lay.addWidget(sec_title)
        sec_h_lay.addStretch()
        count_lbl = QLabel('0/%d' % len(subsystem_keys))
        count_lbl.setFont(_make_font(font_small))
        count_lbl.setStyleSheet(f'QLabel {{ color: {TEXT_MUTED}; border: none; background: transparent; }}')
        sec_h_lay.addWidget(count_lbl)
        if not hasattr(self, '_block_count_lbls'):
            self._block_count_lbls = {}
        self._block_count_lbls[block_id] = count_lbl, list(subsystem_keys)
        lay.addWidget(sec_header)
        cards_container = QWidget()
        cards_container.setStyleSheet('background: transparent;')
        cards_lay = QVBoxLayout(cards_container)
        cards_lay.setContentsMargins(4, 4, 4, 4)
        cards_lay.setSpacing(3)
        for key in subsystem_keys:
            card = SubsystemCard(key=key, display_name=_SUBSYSTEM_NAMES.get(key, key), icon_path=_CARD_ICONS.get(key, ''), profile=self._profile)
            self._cards[key] = card
            cards_lay.addWidget(card)
        lay.addWidget(cards_container)
        return block
    def _build_extra_section(self, key, title_text, placeholder_text, color_accent, font_body, font_small):
        block = QFrame()
        block.setObjectName(f'extra_{key}')
        block.setStyleSheet(f'\n            QFrame#extra_{key} {{\n                background-color: {BG_WHITE};\n                border: 1px solid {BORDER_LIGHT};\n                border-radius: 6px;\n            }}\n        ')
        lay = QVBoxLayout(block)
        lay.setContentsMargins(0, 0, 0, 6)
        lay.setSpacing(0)
        sec_header = QFrame()
        sec_header.setStyleSheet(f'\n            QFrame {{\n                background-color: {BG_TAB_PANE};\n                border: none;\n                border-bottom: 1px solid {BORDER_LIGHT};\n                border-top-left-radius: 6px;\n                border-top-right-radius: 6px;\n            }}\n        ')
        sec_h_lay = QHBoxLayout(sec_header)
        sec_h_lay.setContentsMargins(10, 4, 10, 4)
        sec_title = QLabel(title_text)
        sec_title.setFont(_make_font(font_body, bold=True))
        sec_title.setStyleSheet(f'\n            QLabel {{ color: {color_accent}; border: none;\n                     background: transparent; }}\n        ')
        sec_h_lay.addWidget(sec_title)
        sec_h_lay.addStretch()
        count_lbl = QLabel('')
        count_lbl.setFont(_make_font(font_small))
        count_lbl.setStyleSheet(f'\n            QLabel {{ color: {TEXT_MUTED}; border: none;\n                     background: transparent; }}\n        ')
        sec_h_lay.addWidget(count_lbl)
        self._extra_sections[f'{key}_count'] = count_lbl
        lay.addWidget(sec_header)
        cards_container = QWidget()
        cards_container.setStyleSheet('background: transparent;')
        cards_lay = QVBoxLayout(cards_container)
        cards_lay.setContentsMargins(6, 4, 6, 4)
        cards_lay.setSpacing(3)
        placeholder = QLabel(placeholder_text)
        placeholder.setFont(_make_font(font_small))
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet(f'\n            QLabel {{ color: {TEXT_MUTED}; border: none;\n                     background: transparent; padding: 8px; }}\n        ')
        cards_lay.addWidget(placeholder)
        self._extra_placeholders[key] = placeholder
        self._extra_layouts[key] = cards_lay
        lay.addWidget(cards_container)
        self._extra_sections[key] = block
        return block
    def show_pending_tests(self):
        self._status_label.setText('Pendente')
        for key, card in self._cards.items():
            card.set_state(STATE_PENDING, '')
        for block_id, (lbl, keys) in getattr(self, '_block_count_lbls', {}).items():
            lbl.setText('0/%d' % len(keys))
        self._reset_extra_section('failures', hide_if_empty=True)
        self._reset_extra_section('frequencies', hide_if_empty=False)
        self._reset_extra_section('voltages', hide_if_empty=False)
        self._reset_extra_section('communications', hide_if_empty=False)
        self._reset_extra_section('boot_storage', hide_if_empty=False)
    def mark_all_running(self):
        self._status_label.setText('Analisando...')
        for key, card in self._cards.items():
            if card.get_state() == STATE_PENDING:
                card.set_state(STATE_RUNNING, 'analisando...')
    def clear(self):
        self.show_pending_tests()
    def update_from_state(self, state):
        if not state or not isinstance(state, dict):
            return
        try:
            subsystems = state.get('subsystems', {})
            failures = state.get('failures', {})
            fail_items = failures.get('items', {}) if failures.get('detected') else {}
            fail_map = {'PMIC': 'pmic', 'PMIC OC': 'pmic', 'PMIC Temp': 'pmic', 'SPMI': 'spmi', 'PWRAP': 'pwrap', 'RTC': 'rtc', 'Storage': 'storage', 'RPMB': 'storage', 'DRAM': 'memory', 'DRAM Fatal': 'memory', 'DSI': 'i2c', 'Watchdog': 'watchdog', 'Bootloop': 'boot', 'Boot': 'boot', 'Firmware': 'boot', 'I2C': 'i2c'}
            errored_keys = set()
            warned_keys = set()
            for fname, finfo in fail_items.items():
                sub_key = fail_map.get(fname)
                if sub_key:
                    severity = finfo.get('severity', 'ERR')
                    if severity == 'ERR':
                        errored_keys.add(sub_key)
                    else:
                        warned_keys.add(sub_key)
            parser_to_key = {'battery': 'battery', 'power_key': 'power_key', 'pmic': 'pmic', 'pmic_sec': 'pmic_sec', 'memory': 'memory', 'storage': 'storage', 'i2c': 'i2c', 'rtc': 'rtc', 'cpu': 'cpu', 'pwrap': 'pwrap', 'spmi': 'spmi', 'clocks': 'clocks', 'watchdog': 'watchdog', 'atf': 'atf', 'boot': 'boot'}
            for card_key, card in self._cards.items():
                if card_key in errored_keys:
                    fname = self._find_fail_name(card_key, fail_items, fail_map)
                    detail = fail_items.get(fname, {}).get('detail', 'Erro') if fname else 'Erro'
                    card.set_state(STATE_ERROR, detail)
                    continue
                if card_key in warned_keys:
                    fname = self._find_fail_name(card_key, fail_items, fail_map)
                    detail = fail_items.get(fname, {}).get('detail', 'Aviso') if fname else 'Aviso'
                    card.set_state(STATE_WARN, detail)
                    continue
                detected_detail = ''
                for parser_key, mapped_card in parser_to_key.items():
                    if mapped_card != card_key:
                        continue
                    info = subsystems.get(parser_key)
                    if not isinstance(info, dict):
                        continue
                    if not info.get('detected'):
                        continue
                    detected_detail = info.get('detail', 'OK')
                    break
                if not detected_detail:
                    continue
                card.set_state(STATE_OK, detected_detail)
                continue
            self._refresh_block_counters()
            self._update_failures_block(fail_items)
            self._update_values_block('frequencies', state.get('frequencies', {}))
            self._update_values_block('voltages', state.get('voltages', {}), sort_fn=_voltage_sort_key)
            self._update_values_block('communications', state.get('communications', {}))
            self._update_values_block('boot_storage', state.get('boot_storage', {}))
            total_ok = sum((1 for c in self._cards.values() if c.get_state() in (STATE_OK, STATE_ERROR, STATE_WARN)))
            if total_ok > 0 or fail_items:
                self._status_label.setText('Analisando...')
                return
        except Exception:
            self._status_label.setText('Erro interno')
    def _refresh_block_counters(self):
        block_lbls = getattr(self, '_block_count_lbls', {})
        for block_id, (lbl, keys) in block_lbls.items():
            ok = 0
            for k in keys:
                card = self._cards.get(k)
                if not card:
                    continue
                if card.get_state() == STATE_OK:
                    ok += 1
            lbl.setText('%d/%d' % (ok, len(keys)))
    def _find_fail_name(self, sub_key, fail_items, fail_map):
        for fname, mapped_key in fail_map.items():
            if mapped_key != sub_key:
                continue
            if not fname in fail_items:
                continue
            return fname
    def _reset_extra_section(self, key, hide_if_empty=True):
        layout = self._extra_layouts.get(key)
        section = self._extra_sections.get(key)
        count_lbl = self._extra_sections.get(f'{key}_count')
        placeholder = self._extra_placeholders.get(key)
        if not layout or not section:
            return
        self._clear_layout_except_placeholder(layout, placeholder)
        if placeholder:
            placeholder.setVisible(True)
        if count_lbl:
            count_lbl.setText('')
        section.setVisible(not hide_if_empty)
    def _update_failures_block(self, fail_items):
        p = self._profile
        font_body = p.get('body_font', 11)
        font_small = p.get('small_font', 10)
        layout = self._extra_layouts.get('failures')
        section = self._extra_sections.get('failures')
        count_lbl = self._extra_sections.get('failures_count')
        placeholder = self._extra_placeholders.get('failures')
        if not layout or not section:
            return
        self._clear_layout_except_placeholder(layout, placeholder)
        if not fail_items:
            section.setVisible(False)
            if placeholder:
                placeholder.setVisible(True)
            if count_lbl:
                count_lbl.setText('')
            return
        if placeholder:
            placeholder.setVisible(False)
        count = 0
        for fname, finfo in fail_items.items():
            severity = finfo.get('severity', 'ERR')
            color = RED if severity == 'ERR' else ORANGE
            detail = finfo.get('detail', '')
            occ = finfo.get('count', 1)
            card = QFrame()
            card.setObjectName(f'fail_{fname}')
            card.setStyleSheet(f'\n                QFrame#fail_{fname} {{\n                    background-color: {BG_WHITE};\n                    border: 1px solid {color};\n                    border-left: 4px solid {color};\n                    border-radius: 4px;\n                }}\n            ')
            v = QVBoxLayout(card)
            v.setContentsMargins(8, 4, 8, 4)
            v.setSpacing(2)
            top = QHBoxLayout()
            top.setSpacing(6)
            n_lbl = QLabel(fname)
            n_lbl.setFont(_make_font(font_body, bold=True))
            n_lbl.setStyleSheet(f'QLabel {{ color: {TEXT}; border: none; background: transparent; }}')
            top.addWidget(n_lbl)
            top.addStretch()
            badge = QLabel('ERRO' if severity == 'ERR' else 'AVISO')
            badge.setFont(_make_font(font_small, bold=True))
            badge.setStyleSheet(f'\n                QLabel {{ background: {color}; color: {WHITE};\n                          border-radius: 3px; padding: 1px 8px;\n                          border: none; }}\n            ')
            top.addWidget(badge)
            v.addLayout(top)
            if detail:
                d_lbl = QLabel(detail)
                d_lbl.setFont(_make_font(font_small))
                d_lbl.setStyleSheet(f'QLabel {{ color: {TEXT_MUTED}; border: none; background: transparent; }}')
                d_lbl.setWordWrap(True)
                v.addWidget(d_lbl)
            if occ > 1:
                o_lbl = QLabel('%d ocorrencias' % occ)
                o_lbl.setFont(_make_font(font_small - 1, bold=True))
                o_lbl.setStyleSheet(f'QLabel {{ color: {color}; border: none; background: transparent; }}')
                v.addWidget(o_lbl)
            layout.addWidget(card)
            count += 1
            continue
        section.setVisible(True)
        if count_lbl:
            count_lbl.setText('%d item(s)' % count)
    def _update_values_block(self, section_key, data, sort_fn=None):
        p = self._profile
        font_body = p.get('body_font', 11)
        font_small = p.get('small_font', 10)
        layout = self._extra_layouts.get(section_key)
        section = self._extra_sections.get(section_key)
        count_lbl = self._extra_sections.get(f'{section_key}_count')
        placeholder = self._extra_placeholders.get(section_key)
        if not layout or not section:
            return
        self._clear_layout_except_placeholder(layout, placeholder)
        if not (data.get('detected') and data.get('values')):
            if placeholder:
                placeholder.setVisible(True)
            if count_lbl:
                count_lbl.setText('')
            return
        if placeholder:
            placeholder.setVisible(False)
        values = data['values']
        if sort_fn:
            try:
                sorted_items = sorted(values.items(), key=(lambda kv: sort_fn(kv[0])))
            except Exception:
                sorted_items = list(values.items())
        else:
            sorted_items = list(values.items())
        count = 0
        prev_group = None
        for name, info in sorted_items:
            value = info.get('value', 0)
            unit = info.get('unit', '')
            readings = info.get('readings', 0)
            if sort_fn:
                try:
                    cur_group = sort_fn(name)[0]
                except Exception:
                    cur_group = None
                if prev_group is not None and cur_group != prev_group:
                    sep = QFrame()
                    sep.setFixedHeight(1)
                    sep.setStyleSheet(f'background-color: {BORDER_LIGHT};')
                    layout.addWidget(sep)
                prev_group = cur_group
            safe_name = name.replace(' ', '_').replace('/', '_')
            card = QFrame()
            card.setObjectName(f'val_{section_key}_{safe_name}')
            card.setStyleSheet(f'\n                QFrame#val_{section_key}_{safe_name} {{\n                    background-color: {BG_WHITE};\n                    border: 1px solid {BORDER_LIGHT};\n                    border-radius: 4px;\n                }}\n            ')
            h = QHBoxLayout(card)
            h.setContentsMargins(8, 4, 8, 4)
            h.setSpacing(6)
            n_lbl = QLabel(name)
            n_lbl.setFont(_make_font(max(11, font_body), bold=True))
            n_lbl.setStyleSheet(f'QLabel {{ color: {TEXT}; border: none; background: transparent; }}')
            n_lbl.setToolTip(name)
            n_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            h.addWidget(n_lbl)
            h.addStretch()
            display_text = f'{value!s} {unit!s}' if unit else str(value)
            pill_font_sz = max(12, font_body + 1)
            pill = QLabel(display_text.strip())
            pill.setFont(_make_font(pill_font_sz, bold=True))
            pill.setMinimumHeight(max(26, int(pill_font_sz * 2.2)))
            pill.setStyleSheet(f'\n                QLabel {{ background: #e3f2fd; color: {UNION_BLUE};\n                         border-radius: 10px; padding: 3px 12px;\n                         font-family: "Cascadia Code", "Consolas", monospace;\n                         border: none; }}\n            ')
            pill.setToolTip(display_text.strip())
            h.addWidget(pill)
            if readings > 1:
                r_lbl = QLabel('%dx' % readings)
                r_lbl.setFont(_make_font(font_small - 1))
                r_lbl.setStyleSheet(f'QLabel {{ color: {TEXT_MUTED}; border: none; background: transparent; }}')
                h.addWidget(r_lbl)
            layout.addWidget(card)
            count += 1
            continue
        if count_lbl:
            count_lbl.setText('%d valores' % count)
    def _clear_layout_except_placeholder(self, layout, placeholder):
        if not layout:
            return
        to_remove = []
        for i in range(layout.count()):
            item = layout.itemAt(i)
            w = item.widget()
            if not w:
                continue
            if w is not placeholder:
                to_remove.append(w)
        for w in to_remove:
            layout.removeWidget(w)
            w.setParent(None)
            w.deleteLater()
