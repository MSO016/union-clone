from __future__ import annotations
import logging
import os
from typing import (Any, Dict, List, Optional)
from PyQt5.QtCore import (Qt, QTimer, pyqtSignal)
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget)
try:
    from app.utils.path_manager import PathManager
    _SVG_DIR = PathManager.get_resource_path('icons_svg')
except Exception:
    _SVG_DIR = None
def _resolve_dpi_profile(scale: float) -> Dict[str, int]:
    try:
        s = max(1.0, float(scale))
    except (TypeError, ValueError):
        s = 1.0
    if s >= 1.53:
        return dict(root_margin=7, root_spacing=5, cards_spacing=4, header_spacing=4, toolbar_spacing=4, btn_min_w=118, btn_min_h=26, title_size=12, empty_size=11, ident_size=11, help_size=10, card_padding_v=5, card_padding_h=7, card_radius=8)
    if s >= 1.38:
        return dict(root_margin=8, root_spacing=6, cards_spacing=5, header_spacing=5, toolbar_spacing=5, btn_min_w=128, btn_min_h=28, title_size=12, empty_size=11, ident_size=11, help_size=11, card_padding_v=6, card_padding_h=8, card_radius=8)
    if s >= 1.15:
        return dict(root_margin=9, root_spacing=7, cards_spacing=6, header_spacing=6, toolbar_spacing=6, btn_min_w=138, btn_min_h=30, title_size=13, empty_size=12, ident_size=12, help_size=11, card_padding_v=6, card_padding_h=9, card_radius=8)
    return dict(root_margin=10, root_spacing=8, cards_spacing=6, header_spacing=6, toolbar_spacing=6, btn_min_w=148, btn_min_h=32, title_size=13, empty_size=12, ident_size=12, help_size=11, card_padding_v=6, card_padding_h=9, card_radius=8)
logger = logging.getLogger(__name__)
_STATE_VISUAL_LIGHT: 'Dict[str, tuple]' = {'device': ('Autorizado', '#1b5e20', '#e8f5e9'), 'unauthorized': ('Aguardando autorizacao', '#e65100', '#fff3e0'), 'offline': ('Offline', '#b71c1c', '#ffebee'), 'no permissions': ('Sem permissao (driver)', '#b71c1c', '#ffebee'), 'recovery': ('Modo Recovery', '#0d47a1', '#e3f2fd'), 'sideload': ('Modo Sideload', '#0d47a1', '#e3f2fd'), 'bootloader': ('Bootloader', '#4a148c', '#f3e5f5')}
_STATE_VISUAL_DARK: 'Dict[str, tuple]' = {'device': ('Autorizado', '#86efac', 'rgba(34,197,94,0.16)'), 'unauthorized': ('Aguardando autorizacao', '#fcd34d', 'rgba(251,146,60,0.16)'), 'offline': ('Offline', '#fca5a5', 'rgba(239,68,68,0.18)'), 'no permissions': ('Sem permissao (driver)', '#fca5a5', 'rgba(239,68,68,0.18)'), 'recovery': ('Modo Recovery', '#93c5fd', 'rgba(59,130,246,0.16)'), 'sideload': ('Modo Sideload', '#93c5fd', 'rgba(59,130,246,0.16)'), 'bootloader': ('Bootloader', '#d8b4fe', 'rgba(168,85,247,0.16)')}
_STATE_VISUAL = _STATE_VISUAL_LIGHT
class UsbDeviceWidget(QFrame):
    request_reset_adb = pyqtSignal()
    request_reauthorize = pyqtSignal(str)
    request_regenerate_keys = pyqtSignal()
    request_open_devices = pyqtSignal()
    devices_updated = pyqtSignal(list)
    def __init__(self, adb_manager: Any=None, parent: Optional[QWidget]=None, dark_mode: bool=False):
        super().__init__(parent)
        self._adb = adb_manager
        self._busy = False
        self._last_devices = []
        self._dark_mode = bool(dark_mode)
        self._state_visual = _STATE_VISUAL_DARK if self._dark_mode else _STATE_VISUAL_LIGHT
        self._dpi_profile = _resolve_dpi_profile(1.0)
        self._build_ui()
    @staticmethod
    def _apply_svg(btn: QPushButton, filename: str) -> None:
        if not _SVG_DIR:
            return
        path = os.path.join(_SVG_DIR, filename)
        if os.path.isfile(path):
            btn.setIcon(QIcon(path))
    def force_refresh(self) -> None:
        if self._busy:
            return
        self._busy = True
        try:
            btn = getattr(self, '_btn_refresh', None)
            if btn is not None:
                self._refresh_btn_text_backup = btn.text()
                btn.setEnabled(False)
                btn.setText('ÔÅ│ Atualizando...')
        except Exception:
            pass
        QTimer.singleShot(0, self._do_refresh)
    def apply_dpi_profile(self, dpi_scale: Optional[float]=None) -> None:
        try:
            scale = dpi_scale
            if scale is None:
                qapp = QApplication.instance()
                if qapp is not None:
                    screen = qapp.primaryScreen()
                    if screen is not None:
                        logical_dpi = screen.logicalDotsPerInch()
                        if logical_dpi and logical_dpi > 0:
                            scale = float(logical_dpi) / 96.0
            if scale is None:
                scale = 1.0
            profile = _resolve_dpi_profile(scale)
            self._dpi_profile = profile
            try:
                m = profile['root_margin']
                self._root_layout.setContentsMargins(m, m, m, m)
                self._root_layout.setSpacing(profile['root_spacing'])
            except Exception:
                pass
            try:
                self._cards_layout.setSpacing(profile['cards_spacing'])
            except Exception:
                pass
            else:
                try:
                    self._header_layout.setSpacing(profile['header_spacing'])
                except Exception:
                    pass
                try:
                    self._toolbar_layout.setSpacing(profile['toolbar_spacing'])
                except Exception:
                    pass
                for btn in getattr(self, '_btn_refresh', None), getattr(self, '_btn_open_devmgr', None), getattr(self, '_btn_reset', None):
                    if btn is not None:
                        pass
        except Exception:
            return
        try:
            self._title_label.setStyleSheet(self._title_label.styleSheet().replace('font-size:13px', f'font-size:{profile['title_size']}px'))
        except Exception:
            pass
        try:
            try:
                if self._last_devices:
                    self._render(self._last_devices)
                    return
            except Exception:
                return
        except Exception:
            return
    def stop(self) -> None:
        self._busy = False
    def get_last_devices(self) -> List[Dict[str, str]]:
        return list(self._last_devices)
    def _build_ui(self) -> None:
        self.setObjectName('usbDeviceWidget')
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        if self._dark_mode:
            frame_bg = 'transparent'
            frame_border = '1px solid rgba(255,255,255,0.10)'
            sec_bg = '#172554'
            sec_color = '#93c5fd'
            sec_border = '1px solid #3b82f6'
            sec_hover_bg = '#1e3a5f'
            sec_hover_color = '#ffffff'
            sec_dis_bg = '#0f172a'
            sec_dis_color = '#64748b'
            sec_dis_border = '1px solid #334155'
            title_color = '#ffffff'
            act_bg = '#172554'
            act_color = '#93c5fd'
            act_border = '1px solid #3b82f6'
            act_hover_bg = '#1e3a5f'
            act_hover_color = '#ffffff'
            act_pressed_bg = '#1e40af'
            act_dis_bg = '#0f172a'
            act_dis_color = '#475569'
        else:
            frame_bg = '#fafafa'
            frame_border = '1px solid #e0e0e0'
            sec_bg = 'white'
            sec_color = '#0D47A1'
            sec_border = '1px solid #0D47A1'
            sec_hover_bg = '#e3f2fd'
            sec_hover_color = '#0D47A1'
            sec_dis_bg = '#f5f5f5'
            sec_dis_color = '#bdbdbd'
            sec_dis_border = '1px solid #e0e0e0'
            title_color = '#0D47A1'
            act_bg = '#0D47A1'
            act_color = 'white'
            act_border = 'none'
            act_hover_bg = '#1565C0'
            act_hover_color = 'white'
            act_pressed_bg = '#0a3680'
            act_dis_bg = '#bdbdbd'
            act_dis_color = '#fafafa'
        self.setStyleSheet(''.join(['\n            QFrame#usbDeviceWidget {\n                background: ', f'{frame_bg}', ';\n                border: ', f'{frame_border}', ';\n                border-radius: 8px;\n            }\n            QPushButton#usbActionBtn {\n                background: ', f'{act_bg}', ';\n                color: ', f'{act_color}', ';\n                padding: 6px 12px;\n                border: ', f'{act_border}', ';\n                border-radius: 4px;\n                font-size: 12px;\n                font-weight: 600;\n            }\n            QPushButton#usbActionBtn:hover  {\n                background: ', f'{act_hover_bg}', ';\n                color: ', f'{act_hover_color}', ';\n            }\n            QPushButton#usbActionBtn:pressed{\n                background: ', f'{act_pressed_bg}', ';\n            }\n            QPushButton#usbActionBtn:disabled {\n                background: ', f'{act_dis_bg}', ';\n                color: ', f'{act_dis_color}', ';\n            }\n            QPushButton#usbSecondaryBtn {\n                background: ', f'{sec_bg}', ';\n                color: ', f'{sec_color}', ';\n                border: ', f'{sec_border}', ';\n                border-radius: 4px;\n                padding: 4px 9px;\n                font-size: 12px;\n            }\n            QPushButton#usbSecondaryBtn:hover {\n                background: ', f'{sec_hover_bg}', ';\n                color: ', f'{sec_hover_color}', ';\n            }\n            QPushButton#usbSecondaryBtn:disabled {\n                background: ', f'{sec_dis_bg}', ';\n                color: ', f'{sec_dis_color}', ';\n                border: ', f'{sec_dis_border}', ';\n            }\n            ']))
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)
        self._root_layout = root
        header = QHBoxLayout()
        header.setSpacing(6)
        self._header_layout = header
        self._title_label = None
        title = QLabel('Aparelhos USB detectados')
        title.setStyleSheet(f'font-weight:600; font-size:13px; color:{title_color}; background:transparent; border:none;')
        self._title_label = title
        header.addWidget(title)
        header.addStretch(1)
        btn_refresh = QPushButton('Atualizar lista')
        btn_refresh.setObjectName('usbSecondaryBtn')
        btn_refresh.setToolTip("Atualiza apenas esta lista (sem mensagens).\nUse depois de:\n- Autorizar 'Permitir' no aparelho\n- Reconectar o cabo USB\n- Trocar de aparelho")
        btn_refresh.clicked.connect(self.force_refresh)
        self._apply_svg(btn_refresh, 'arrow-clockwise.svg')
        header.addWidget(btn_refresh)
        self._btn_refresh = btn_refresh
        root.addLayout(header)
        self._cards_container = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(6)
        root.addWidget(self._cards_container)
        empty_color = '#cbd5e1' if self._dark_mode else '#666'
        self._empty_label = QLabel('Nenhum aparelho detectado.<br>Clique em <b>PASSO 1: Verificar Conexao</b> para checar.')
        self._empty_label.setStyleSheet(f'color:{empty_color}; padding:6px; background:transparent; border:none;')
        self._empty_label.setWordWrap(True)
        self._empty_label.setTextFormat(Qt.RichText)
        root.addWidget(self._empty_label)
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)
        self._toolbar_layout = toolbar
        self._btn_open_devmgr = QPushButton('Gerenciador de Dispositivos')
        self._btn_open_devmgr.setObjectName('usbSecondaryBtn')
        self._btn_open_devmgr.setToolTip('Abre o gerenciador do Windows para inspecionar drivers.')
        self._btn_open_devmgr.clicked.connect(self.request_open_devices.emit)
        self._apply_svg(self._btn_open_devmgr, 'pc-display.svg')
        toolbar.addWidget(self._btn_open_devmgr)
        self._btn_reset = QPushButton('Reiniciar conexao')
        self._btn_reset.setObjectName('usbActionBtn')
        self._btn_reset.setToolTip('Reinicia o servico de comunicacao com aparelhos.')
        self._btn_reset.clicked.connect(self.request_reset_adb.emit)
        self._apply_svg(self._btn_reset, 'arrow-clockwise.svg')
        toolbar.addWidget(self._btn_reset)
        toolbar.addStretch(1)
        root.addLayout(toolbar)
    def _do_refresh(self) -> None:
        try:
            devices = []
        finally:
            self._busy = False
            try:
                btn = getattr(self, '_btn_refresh', None)
                if btn is not None:
                    btn.setEnabled(True)
                    backup = getattr(self, '_refresh_btn_text_backup', None)
                    if backup:
                        btn.setText(backup)
                    btn.setText('­ƒöä Atualizar lista')
            except Exception:
                pass
        try:
            if self._adb is not None:
                if hasattr(self._adb, 'get_device_states_detailed'):
                    raw = self._adb.get_device_states_detailed() or []
                    if isinstance(raw, list):
                        pass
        except Exception as exc:
            try:
                logger.debug('force_refresh: leitura indispon├¡vel (%s)', type(exc).__name__)
            except Exception:
                pass
            devices = []
            try:
                pass
            finally:
                self._busy = False
                try:
                    btn = getattr(self, '_btn_refresh', None)
                    if btn is not None:
                        btn.setEnabled(True)
                        backup = getattr(self, '_refresh_btn_text_backup', None)
                        if backup:
                            btn.setText(backup)
                        btn.setText('­ƒöä Atualizar lista')
                except Exception:
                    pass
        self._render(devices)
        self._last_devices = devices
        try:
            self.devices_updated.emit(devices)
        except Exception:
            pass
        self._busy = False
        try:
            btn = getattr(self, '_btn_refresh', None)
            if btn is not None:
                btn.setEnabled(True)
                backup = getattr(self, '_refresh_btn_text_backup', None)
                if backup:
                    btn.setText(backup)
                    return
                btn.setText('­ƒöä Atualizar lista')
                return
        except Exception:
            return
    def _render(self, devices: List[Dict[str, str]]) -> None:
        try:
            while self._cards_layout.count():
                item = self._cards_layout.takeAt(0)
                w = item.widget() if item is not None else None
                if w is not None:
                    w.setParent(None)
                    w.deleteLater()
        except Exception:
            pass
        if not devices:
            self._empty_label.setText('Nenhum aparelho USB detectado.<br><br>Verifique:<br>ÔÇó Cabo USB original ligado nas duas pontas<br>ÔÇó Drivers do fabricante instalados<br>ÔÇó Modo Depuracao USB ativado no aparelho')
            self._empty_label.setVisible(True)
            return
        self._empty_label.setVisible(False)
        for d in devices:
            try:
                card = self._build_card(d)
                if card is not None:
                    self._cards_layout.addWidget(card)
            except Exception:
                continue
    def _build_card(self, device: Dict[str, str]) -> Optional[QFrame]:
        state_raw = (device.get('state') or '').strip().lower()
        if self._dark_mode:
            unknown = f'{state_raw or 'estado desconhecido'}', '#cbd5e1', 'rgba(148,163,184,0.10)'
            card_border = '1px solid rgba(255,255,255,0.10)'
            text_secondary = '#ffffff'
        else:
            unknown = f'{state_raw or 'estado desconhecido'}', '#555555', '#f5f5f5'
            card_border = '1px solid #e0e0e0'
            text_secondary = '#555'
        label, fg, bg = self._state_visual.get(state_raw, unknown)
        prof = self._dpi_profile or {}
        card_radius = int(prof.get('card_radius', 8))
        card_pad_v = int(prof.get('card_padding_v', 6))
        card_pad_h = int(prof.get('card_padding_h', 9))
        card = QFrame()
        card.setStyleSheet(f'QFrame {{background:{bg}; border:{card_border}; border-radius:{card_radius}px;}}')
        v = QVBoxLayout(card)
        v.setContentsMargins(card_pad_h, card_pad_v, card_pad_h, card_pad_v)
        v.setSpacing(3)
        l_status = QLabel(label)
        l_status.setStyleSheet(f'font-weight:600; color:{fg}; background:transparent; border:none;')
        v.addWidget(l_status)
        ident = self._friendly_ident(device)
        if ident:
            l_id = QLabel(ident)
            l_id.setStyleSheet(f'color:{text_secondary}; background:transparent; border:none; font-size:10pt; font-weight:500;')
            v.addWidget(l_id)
        if state_raw == 'unauthorized':
            row = QHBoxLayout()
            row.setSpacing(6)
            row.setContentsMargins(0, 2, 0, 0)
            serial = (device.get('serial') or '').strip()
            b1 = QPushButton('Reenviar pedido')
            b1.setObjectName('usbActionBtn')
            b1.setToolTip("Reenvia a solicitacao para o aparelho.\nOlhe a tela e toque em 'Permitir'.")
            b1.clicked.connect((lambda _checked=False, s=serial: self.request_reauthorize.emit(s)))
            self._apply_svg(b1, 'usb-plug.svg')
            row.addWidget(b1)
            b2 = QPushButton('Renovar autorizacao')
            b2.setObjectName('usbSecondaryBtn')
            b2.setToolTip('Use quando o aparelho nao mostra mais o pedido de permissao.')
            b2.clicked.connect(self.request_regenerate_keys.emit)
            self._apply_svg(b2, 'shield-lock.svg')
            row.addWidget(b2)
            row.addStretch(1)
            v.addLayout(row)
            return card
        if state_raw == 'offline':
            l_help = QLabel('Desconecte e reconecte o cabo USB.<br>Se persistir, clique em <b>Reiniciar conexao</b>.')
            l_help.setStyleSheet(f'color:{text_secondary}; background:transparent; border:none; font-size:11px;')
            l_help.setTextFormat(Qt.RichText)
            l_help.setWordWrap(True)
            v.addWidget(l_help)
            return card
        if state_raw == 'no permissions':
            l_help = QLabel('Reinstale os drivers do fabricante e troque a porta USB.')
            l_help.setStyleSheet(f'color:{text_secondary}; background:transparent; border:none; font-size:11px;')
            l_help.setWordWrap(True)
            v.addWidget(l_help)
        return card
    @staticmethod
    def _friendly_ident(device: Dict[str, str]) -> str:
        parts = []
        model = (device.get('model') or '').strip()
        product = (device.get('product') or '').strip()
        if model:
            parts.append(model)
        elif product:
            parts.append(product)
        serial = (device.get('serial') or '').strip()
        if serial and not serial.startswith('????'):
            short = serial if len(serial) <= 14 else serial[:5] + 'ÔÇª' + serial[-4:]
            parts.append(f'Serial: {short}')
        if parts:
            return '  ÔÇó  '.join(parts)
        return ''
