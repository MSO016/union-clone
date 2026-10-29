from __future__ import annotations
import os
from typing import (Any, Callable, Dict, List, Optional)
from PyQt5.QtCore import (QEasingCurve, QPropertyAnimation, QSize, Qt, pyqtSignal)
from PyQt5.QtGui import (QColor, QIcon, QPainter, QPixmap)
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget)
SIDEBAR_CONFIG: 'Dict[str, Any]' = {'width_normal': 248, 'width_compact': 220, 'width_rail': 64, 'rail_breakpoint_w': 1100, 'bg_top': '#162032', 'bg_bottom': '#0c1320', 'border_right': '#0a1018', 'logo_bg': '#0D47A1', 'logo_text': '#ffffff', 'section_label_color': '#5a6f88', 'item_text': '#e8eaed', 'item_text_muted': '#9aa7b8', 'item_hover_bg': 'rgba(33, 150, 243, 0.14)', 'item_active_bg': '#0D47A1', 'item_active_text': '#ffffff', 'item_active_marker': '#2196F3', 'subitem_indent_px': 16, 'badge_new_bg': '#f39c12', 'badge_new_text': '#ffffff', 'scroll_handle': '#5a6f88', 'scroll_handle_hover': '#8a9bb0', 'scroll_handle_pressed': '#a8b8c8', 'scroll_track': 'rgba(255, 255, 255, 0.04)', 'font_family': 'Segoe UI', 'font_size_logo_title': 13, 'font_size_logo_subtitle': 9, 'font_size_section': 10, 'font_size_item': 12, 'font_size_subitem': 11, 'font_size_badge': 8, 'logo_height': 78, 'item_height': 36, 'subitem_height': 30, 'section_top_spacing': 14, 'section_bottom_spacing': 4, 'expand_animation_ms': 180, 'expand_easing': QEasingCurve.OutCubic, 'updates_bar_bg': '#0D47A1', 'updates_bar_text_color': '#ffffff', 'updates_bar_height': 32, 'updates_bar_scroll_step_ms': 35}
SIDEBAR_MODEL: 'List[Dict[str, Any]]' = [{'id': 'dashboard', 'label': 'Dashboard', 'label_key': 'sidebar_dashboard', 'icon': 'home', 'type': 'single', 'callback': 'mostrar_dashboard_inicial', 'active_default': True}, {'id': 'principal', 'type': 'section', 'label': 'PRINCIPAL', 'label_key': 'sidebar_section_principal', 'items': [{'id': 'solucoes', 'label': 'Solucoes', 'label_key': 'sidebar_solucoes', 'icon': 'lightbulb', 'callback': 'mostrar_dashboard_inicial'}, {'id': 'samsung', 'label': 'Samsung', 'icon': 'samsung', 'callback': 'abrir_solucoes', 'args': ['SAMSUNG']}, {'id': 'apple', 'label': 'Apple', 'icon': 'apple', 'callback': 'abrir_solucoes', 'args': ['APPLE']}, {'id': 'motorola', 'label': 'Motorola', 'icon': 'motorola', 'callback': 'abrir_solucoes', 'args': ['MOTOROLA']}, {'id': 'xiaomi', 'label': 'Xiaomi', 'icon': 'xiaomi', 'callback': 'abrir_solucoes', 'args': ['XIAOMI']}, {'id': 'esquemas', 'label': 'Esquemas Eletricos', 'label_key': 'sidebar_esquemas_eletricos', 'icon': 'schema', 'callback': 'abrir_solucoes', 'args': ['ESQUEMAS ELETRICO']}, {'id': 'outras_marcas', 'label': 'Outras Marcas', 'label_key': 'sidebar_outras_marcas', 'icon': 'more', 'type': 'expandable', 'subitems': [{'id': 'realme', 'label': 'Realme', 'callback': 'abrir_solucoes', 'args': ['REALME']}, {'id': 'oppo', 'label': 'Oppo', 'callback': 'abrir_solucoes', 'args': ['OPPO']}, {'id': 'vivo', 'label': 'Vivo', 'callback': 'abrir_solucoes', 'args': ['VIVO']}, {'id': 'huawei', 'label': 'Huawei', 'callback': 'abrir_solucoes', 'args': ['HUAWEI']}, {'id': 'infinix', 'label': 'Infinix', 'callback': 'abrir_solucoes', 'args': ['INFINIX']}, {'id': 'tecno', 'label': 'Tecno', 'callback': 'abrir_solucoes', 'args': ['TECNO']}]}, {'id': 'categorias', 'label': 'Categorias', 'label_key': 'sidebar_categorias', 'icon': 'schema', 'type': 'expandable', 'subitems': [{'id': 'cat_android_cmd', 'label': 'Android Comandos', 'label_key': 'sidebar_android_comandos', 'callback': 'abrir_solucoes', 'args': ['ANDROID\nCOMANDOS']}, {'id': 'cat_software', 'label': 'Software', 'label_key': 'sidebar_software', 'callback': 'abrir_solucoes', 'args': ['SOFTWARE']}, {'id': 'cat_cpu', 'label': 'CPU', 'label_key': 'sidebar_cpu', 'callback': 'abrir_solucoes', 'args': ['CPU']}, {'id': 'cat_estudo', 'label': 'Estudo', 'label_key': 'sidebar_estudo', 'callback': 'abrir_solucoes', 'args': ['ESTUDO']}, {'id': 'cat_jumper', 'label': 'Jumper de Telas', 'label_key': 'sidebar_jumper_telas', 'callback': 'abrir_solucoes', 'args': ['JUMPER DE TELAS']}, {'id': 'cat_emmc', 'label': 'EMMC UFS', 'label_key': 'sidebar_emmc_ufs', 'callback': 'abrir_solucoes', 'args': ['EMMC UFS']}, {'id': 'cat_testpoints', 'label': 'Test Points', 'label_key': 'sidebar_test_points', 'callback': 'abrir_solucoes', 'args': ['TEST POINTS']}, {'id': 'cat_desbloqueio', 'label': 'Desbloqueio', 'label_key': 'sidebar_desbloqueio', 'callback': 'abrir_solucoes', 'args': ['DESBLOQUEIO']}]}]}, {'id': 'ferramentas', 'type': 'section', 'label': 'FERRAMENTAS', 'label_key': 'sidebar_section_ferramentas', 'items': [{'id': 'qcom_edl', 'label': 'Qcom EDL', 'label_key': 'sidebar_qcom_edl', 'icon': 'qcom', 'callback': 'abrir_diagnostico_aba_edl', 'badge': 'NOVO'}, {'id': 'mtk_tools', 'label': 'MTK Tools', 'label_key': 'sidebar_mtk_tools', 'icon': 'mtk', 'callback': 'abrir_mtk_flash_tools', 'badge': 'NOVO'}, {'id': 'spd_tools', 'label': 'SPD', 'label_key': 'sidebar_spd_tools', 'icon': 'spd', 'callback': 'abrir_diagnostico_aba_spd', 'badge': 'NOVO'}, {'id': 'exy_tools', 'label': 'Exynos', 'label_key': 'sidebar_exy_tools', 'icon': 'samsung', 'callback': 'abrir_tools_exynos', 'badge': 'PREMIUM'}, {'id': 'frp_tools', 'label': 'FRP Tools', 'label_key': 'sidebar_frp_tools', 'icon': 'frp', 'type': 'expandable', 'subitems': [{'id': 'frp_motorola', 'label': 'Motorola', 'callback': 'abrir_diagnostico_aba_motorola'}, {'id': 'frp_xiaomi', 'label': 'Xiaomi', 'callback': 'abrir_diagnostico_aba_xiaomi'}, {'id': 'frp_samsung', 'label': 'Samsung', 'callback': 'abrir_diagnostico_aba_samsung'}]}, {'id': 'tira_virus', 'label': 'Tira Virus', 'label_key': 'sidebar_tira_virus', 'icon': 'virus', 'callback': 'abrir_tira_virus'}, {'id': 'monitor_uart', 'label': 'Monitor UART', 'label_key': 'sidebar_monitor_uart', 'icon': 'uart', 'callback': 'abrir_uart_monitor'}, {'id': 'peliculas', 'label': 'Peliculas', 'label_key': 'sidebar_peliculas', 'icon': 'pelicula', 'callback': 'abrir_peliculas', 'badge': 'NOVO'}, {'id': 'hxd_tools', 'label': 'Tools', 'label_key': 'sidebar_hxd_tools', 'icon': 'hxd', 'callback': 'abrir_tools_hxd', 'badge': 'PREMIUM'}, {'id': 'ferramentas_extra', 'label': 'Ferramentas', 'label_key': 'sidebar_ferramentas_extra', 'icon': 'ferramentas', 'type': 'expandable', 'subitems': [{'id': 'diag_geral', 'label': 'Diagnostico', 'label_key': 'sidebar_diagnostico', 'callback': 'abrir_diagnostico'}, {'id': 'flash_moto', 'label': 'Flash Motorola', 'label_key': 'sidebar_flash_motorola', 'callback': 'abrir_flash_motorola'}, {'id': 'flash_xiaomi', 'label': 'Flash Xiaomi', 'label_key': 'sidebar_flash_xiaomi', 'callback': 'abrir_flash_xiaomi'}, {'id': 'flash_samsung', 'label': 'Flash Samsung', 'label_key': 'sidebar_flash_samsung', 'callback': 'abrir_flash_samsung'}, {'id': 'diag_apps', 'label': 'Apps', 'label_key': 'sidebar_apps', 'callback': 'abrir_diagnostico_aba_apps'}, {'id': 'diag_monitor', 'label': 'Monitor', 'label_key': 'sidebar_monitor', 'callback': 'abrir_diagnostico_aba_monitor'}]}]}, {'id': 'sistema', 'type': 'section', 'label': 'SISTEMA', 'label_key': 'sidebar_section_sistema', 'items': [{'id': 'os_manager', 'label': 'OS Manager', 'label_key': 'sidebar_os_manager', 'icon': 'os', 'callback': 'abrir_os_manager', 'badge': 'PREMIUM'}, {'id': 'server_gsm', 'label': 'Server GSM', 'label_key': 'sidebar_server_gsm', 'icon': 'server', 'callback': 'abrir_server_gsm'}, {'id': 'sistema_os', 'label': 'Sistema O.S.', 'label_key': 'sidebar_sistema_os', 'icon': 'tasks', 'callback': 'abrir_sistema_os'}, {'id': 'downloads', 'label': 'Downloads', 'label_key': 'sidebar_downloads', 'icon': 'download', 'callback': 'abrir_downloads'}, {'id': 'minhas_solucoes', 'label': 'Minhas Solucoes', 'label_key': 'sidebar_minhas_solucoes', 'icon': 'bookmark', 'callback': 'abrir_minhas_solucoes'}, {'id': 'assistente_ia', 'label': 'Assistente IA', 'label_key': 'sidebar_assistente_ia', 'icon': 'ai', 'callback': 'abrir_union_assistente'}, {'id': 'ajuda', 'label': 'Ajuda / Suporte', 'label_key': 'sidebar_ajuda', 'icon': 'help', 'callback': 'abrir_ajuda'}]}]
ICON_MAP: 'Dict[str, Dict[str, str]]' = {'home': {'svg': 'graph-up.svg', 'fallback': '#'}, 'lightbulb': {'svg': 'card-checklist.svg', 'fallback': '*'}, 'samsung': {'svg': 'phone-flip.svg', 'fallback': 'S'}, 'apple': {'svg': 'phone-flip.svg', 'fallback': 'A'}, 'motorola': {'svg': 'phone-flip.svg', 'fallback': 'M'}, 'xiaomi': {'svg': 'phone-flip.svg', 'fallback': 'X'}, 'schema': {'svg': 'cpu.svg', 'fallback': '+'}, 'more': {'svg': 'card-checklist.svg', 'fallback': '...'}, 'mtk': {'svg': 'tools.svg', 'fallback': 'T'}, 'qcom': {'svg': 'cpu.svg', 'fallback': 'Q'}, 'spd': {'svg': 'cpu.svg', 'fallback': 'S'}, 'frp': {'svg': 'shield-lock.svg', 'fallback': 'F'}, 'virus': {'svg': 'shield-check.svg', 'fallback': 'V'}, 'uart': {'svg': 'terminal.svg', 'fallback': 'U'}, 'pelicula': {'svg': 'pelicula.svg', 'fallback': 'P'}, 'hxd': {'svg': 'hxd.svg', 'fallback': 'T'}, 'ferramentas': {'svg': 'motherboard.svg', 'fallback': 'M'}, 'os': {'svg': 'card-checklist.svg', 'fallback': 'O'}, 'server': {'svg': 'globe.svg', 'fallback': 'G'}, 'tasks': {'svg': 'folder-check.svg', 'fallback': 'Y'}, 'download': {'svg': 'cloud-arrow-down.svg', 'fallback': 'D'}, 'bookmark': {'svg': 'card-checklist.svg', 'fallback': 'B'}, 'ai': {'svg': 'robot.svg', 'fallback': 'I'}, 'help': {'svg': 'question-circle.svg', 'fallback': '?'}}
def _resources_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, '..', '..', 'resources'))
def _icon_path(svg_filename: Optional[str]) -> Optional[str]:
    if not svg_filename:
        return
    candidate = os.path.join(_resources_dir(), 'icons_svg', svg_filename)
    if os.path.exists(candidate):
        return candidate
def _render_svg_pixmap(svg_path: str, size: int, color_hex: Optional[str]=None) -> QPixmap:
    renderer = QSvgRenderer(svg_path)
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    renderer.render(painter)
    if color_hex:
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor(color_hex))
    painter.end()
    return pixmap
def _render_svg_pixmap_size(svg_path: str, width: int, height: int, color_hex: Optional[str]=None) -> QPixmap:
    renderer = QSvgRenderer(svg_path)
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    renderer.render(painter)
    if color_hex:
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor(color_hex))
    painter.end()
    return pixmap
def _build_qss(cfg: Dict[str, Any]) -> str:
    return ''.join(['\n    /* ============= Sidebar (escopo via objectName) ============= */\n    QFrame#sidebarRoot {\n        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n            stop:0 ', f'{cfg['bg_top']}', ', stop:1 ', f'{cfg['bg_bottom']}', ');\n        border: none;\n    }\n\n    QFrame#sidebarLogoBlock {\n        background-color: ', f'{cfg['logo_bg']}', ';\n        border: none;\n    }\n    QLabel#sidebarLogoTitle {\n        color: ', f'{cfg['logo_text']}', ';\n        font-family: "', f'{cfg['font_family']}', '";\n        font-size: ', f'{cfg['font_size_logo_title']}', 'px;\n        font-weight: 700;\n        letter-spacing: 1px;\n        background: transparent;\n    }\n    QLabel#sidebarLogoSubtitle {\n        color: rgba(255,255,255,0.75);\n        font-family: "', f'{cfg['font_family']}', '";\n        font-size: ', f'{cfg['font_size_logo_subtitle']}', 'px;\n        font-weight: 500;\n        letter-spacing: 2px;\n        background: transparent;\n    }\n\n    QLabel#sidebarSectionLabel {\n        color: ', f'{cfg['section_label_color']}', ';\n        font-family: "', f'{cfg['font_family']}', '";\n        font-size: ', f'{cfg['font_size_section']}', 'px;\n        font-weight: 700;\n        letter-spacing: 1.2px;\n        padding-left: 18px;\n        padding-top: ', f'{cfg['section_top_spacing']}', 'px;\n        padding-bottom: ', f'{cfg['section_bottom_spacing']}', 'px;\n        background: transparent;\n    }\n\n    QPushButton#sidebarItem, QPushButton#sidebarSubItem {\n        color: ', f'{cfg['item_text']}', ';\n        background-color: transparent;\n        border: none;\n        border-left: 3px solid transparent;\n        text-align: left;\n        padding-left: 14px;\n        padding-right: 12px;\n        font-family: "', f'{cfg['font_family']}', '";\n        font-size: ', f'{cfg['font_size_item']}', 'px;\n        font-weight: 500;\n    }\n    QPushButton#sidebarSubItem {\n        font-size: ', f'{cfg['font_size_subitem']}', 'px;\n        padding-left: ', f'{14 + cfg['subitem_indent_px']}', 'px;\n        color: ', f'{cfg['item_text_muted']}', ';\n    }\n    QPushButton#sidebarItem:hover, QPushButton#sidebarSubItem:hover {\n        background-color: ', f'{cfg['item_hover_bg']}', ';\n        color: ', f'{cfg['item_active_text']}', ';\n    }\n    QPushButton#sidebarItem[active="true"], QPushButton#sidebarSubItem[active="true"] {\n        background-color: ', f'{cfg['item_active_bg']}', ';\n        color: ', f'{cfg['item_active_text']}', ';\n        border-left: 3px solid ', f'{cfg['item_active_marker']}', ';\n        font-weight: 700;\n    }\n\n    QLabel#sidebarBadge {\n        background-color: ', f'{cfg['badge_new_bg']}', ';\n        color: ', f'{cfg['badge_new_text']}', ';\n        font-family: "', f'{cfg['font_family']}', '";\n        font-size: ', f'{cfg['font_size_badge']}', 'px;\n        font-weight: 800;\n        padding: 2px 6px;\n        border-radius: 7px;\n        letter-spacing: 0.5px;\n    }\n\n    QScrollArea#sidebarScroll {\n        background: transparent;\n        border: none;\n    }\n    QScrollArea#sidebarScroll > QWidget > QWidget {\n        background: transparent;\n    }\n    QScrollBar:vertical {\n        background: ', f'{cfg['scroll_track']}', ';\n        width: 8px;\n        margin: 4px 2px 4px 0px;\n        border-radius: 4px;\n    }\n    QScrollBar::handle:vertical {\n        background: ', f'{cfg['scroll_handle']}', ';\n        border-radius: 4px;\n        min-height: 28px;\n    }\n    QScrollBar::handle:vertical:hover {\n        background: ', f'{cfg['scroll_handle_hover']}', ';\n    }\n    QScrollBar::handle:vertical:pressed {\n        background: ', f'{cfg['scroll_handle_pressed']}', ';\n    }\n    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n        background: none;\n        height: 0;\n    }\n    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {\n        background: none;\n    }\n    '])
class SidebarItem(QPushButton):
    def __init__(self, item_id: str, label: str, icon_key: Optional[str]=None, badge_text: Optional[str]=None, sub: bool=False, parent: Optional[QWidget]=None):
        super().__init__(parent)
        self.item_id = item_id
        self._sub = sub
        self.setObjectName('sidebarSubItem' if sub else 'sidebarItem')
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(SIDEBAR_CONFIG['subitem_height'] if sub else SIDEBAR_CONFIG['item_height'])
        self.setProperty('active', 'false')
        self._has_icon = False
        if icon_key and icon_key in ICON_MAP:
            svg_file = ICON_MAP[icon_key]['svg']
            svg_path = _icon_path(svg_file)
            if svg_path:
                size = 16 if sub else 18
                pixmap = _render_svg_pixmap(svg_path, size, SIDEBAR_CONFIG['item_text'])
                self.setIcon(QIcon(pixmap))
                self.setIconSize(QSize(size, size))
                self._has_icon = True
            else:
                fallback = ICON_MAP[icon_key].get('fallback', '')
                self.setText(f'{fallback}  {label}')
                return
        self.setText(f'  {label}' if self._has_icon else label)
        self._badge = None
        if badge_text:
            self._badge = QLabel(badge_text, self)
            self._badge.setObjectName('sidebarBadge')
            self._badge.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self._badge.adjustSize()
    def set_label(self, label: str) -> None:
        if self._has_icon:
            self.setText(f'  {label}')
            return
        self.setText(label)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if getattr(self, '_badge', None):
            self._badge.adjustSize()
            x = self.width() - self._badge.width() - 14
            y = (self.height() - self._badge.height()) // 2
            self._badge.move(max(0, x), max(0, y))
    def set_active(self, active: bool) -> None:
        self.setProperty('active', 'true' if active else 'false')
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
class SidebarExpandable(QWidget):
    sub_clicked = pyqtSignal(str, dict)
    _HEADER_SUFFIX = '   v'
    def __init__(self, item_id: str, label: str, icon_key: Optional[str], subitems: List[Dict[str, Any]], parent: Optional[QWidget]=None):
        super().__init__(parent)
        self.item_id = item_id
        self._expanded = False
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.header = SidebarItem(item_id, label + self._HEADER_SUFFIX, icon_key, parent=self)
        self.header.clicked.connect(self.toggle)
        layout.addWidget(self.header)
        self.sub_container = QWidget(self)
        sub_layout = QVBoxLayout(self.sub_container)
        sub_layout.setContentsMargins(0, 0, 0, 0)
        sub_layout.setSpacing(0)
        self.sub_buttons = {}
        for sub in subitems:
            btn = SidebarItem(item_id=sub['id'], label=sub['label'], icon_key=None, sub=True, parent=self.sub_container)
            btn.clicked.connect((lambda _checked=False, s=sub: self.sub_clicked.emit(self.item_id, s)))
            sub_layout.addWidget(btn)
            self.sub_buttons[sub['id']] = btn
        sub_h = SIDEBAR_CONFIG['subitem_height'] * len(subitems)
        self.sub_container.setMaximumHeight(0)
        self.sub_container.setMinimumHeight(0)
        self._target_height = sub_h
        layout.addWidget(self.sub_container)
        self._anim = QPropertyAnimation(self.sub_container, b'maximumHeight', self)
        self._anim.setDuration(SIDEBAR_CONFIG['expand_animation_ms'])
        self._anim.setEasingCurve(SIDEBAR_CONFIG['expand_easing'])
    def toggle(self):
        self._expanded = not self._expanded
        self._anim.stop()
        if self._expanded:
            self._anim.setStartValue(self.sub_container.maximumHeight())
            self._anim.setEndValue(self._target_height)
        else:
            self._anim.setStartValue(self.sub_container.maximumHeight())
            self._anim.setEndValue(0)
        self._anim.start()
class SidebarLogo(QFrame):
    def __init__(self, parent: Optional[QWidget]=None):
        super().__init__(parent)
        self.setObjectName('sidebarLogoBlock')
        self.setFixedHeight(SIDEBAR_CONFIG['logo_height'])
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)
        logo_svg = _icon_path('sidebar.svg')
        if logo_svg:
            target = max(48, SIDEBAR_CONFIG['logo_height'] - 12)
            pix = _render_svg_pixmap(logo_svg, target, SIDEBAR_CONFIG['logo_text'])
            self._logo_label = QLabel(self)
            self._logo_label.setPixmap(pix)
            self._logo_label.setAlignment(Qt.AlignCenter)
            self._logo_label.setFixedSize(target, target)
            layout.addWidget(self._logo_label, 0, Qt.AlignVCenter)
            text_box = QVBoxLayout()
            text_box.setSpacing(0)
            text_box.setContentsMargins(0, 0, 0, 0)
            title = QLabel('TECH UNION', self)
            title.setObjectName('sidebarLogoTitle')
            subtitle = QLabel('SOLUTIONS', self)
            subtitle.setObjectName('sidebarLogoSubtitle')
            text_box.addWidget(title)
            text_box.addWidget(subtitle)
            layout.addLayout(text_box, 1)
            return
        icon = QLabel('U', self)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet('QLabel { background: white; color: #0D47A1; font-weight: 900; font-size: 22px; border-radius: 8px; }')
        icon.setFixedSize(40, 40)
        layout.addWidget(icon, 0, Qt.AlignVCenter)
        text_box = QVBoxLayout()
        text_box.setSpacing(0)
        text_box.setContentsMargins(0, 0, 0, 0)
        title = QLabel('TECH UNION', self)
        title.setObjectName('sidebarLogoTitle')
        subtitle = QLabel('SOLUTIONS', self)
        subtitle.setObjectName('sidebarLogoSubtitle')
        text_box.addWidget(title)
        text_box.addWidget(subtitle)
        layout.addLayout(text_box, 1)
class Sidebar(QFrame):
    item_activated = pyqtSignal(str)
    def __init__(self, parent_main_window: Optional[QWidget]=None, parent: Optional[QWidget]=None, translation_manager: Optional[Any]=None):
        super().__init__(parent)
        self.main_window = parent_main_window
        self._tm = translation_manager
        self.setObjectName('sidebarRoot')
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(_build_qss(SIDEBAR_CONFIG))
        self._all_items = {}
        self._items_label_keys = {}
        self._expansor_ids = set()
        self._section_labels = []
        self._active_id = None
        self.setFixedWidth(SIDEBAR_CONFIG['width_normal'])
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(SidebarLogo(self))
        scroll = QScrollArea(self)
        scroll.setObjectName('sidebarScroll')
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root.addWidget(scroll, 1)
        content = QWidget()
        content.setObjectName('sidebarContent')
        content.setAttribute(Qt.WA_StyledBackground, True)
        content.setStyleSheet('QWidget#sidebarContent { background: transparent; }')
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(0, 6, 0, 12)
        c_layout.setSpacing(0)
        self._build_from_model(c_layout)
        c_layout.addStretch(1)
        scroll.setWidget(content)
        for entry in SIDEBAR_MODEL:
            if entry.get('active_default'):
                self.set_active_item(entry['id'])
                return
    def _resolve_label(self, item: Dict[str, Any], registrar_id: bool=True) -> str:
        label = item.get('label', '')
        chave = item.get('label_key')
        if registrar_id and chave and 'id' in item:
            self._items_label_keys[item['id']] = chave
        if not chave or self._tm is None:
            return label
        try:
            valor = self._tm.get_text(chave)
            if isinstance(valor, str) and valor and valor != chave:
                return valor
        except Exception:
            pass
        return label
    def _build_from_model(self, layout: QVBoxLayout) -> None:
        for entry in SIDEBAR_MODEL:
            etype = entry.get('type', 'single')
            if etype == 'single':
                btn = self._make_item(entry)
                layout.addWidget(btn)
                continue
            if etype != 'section':
                continue
            section_lbl = QLabel(self._resolve_label(entry, registrar_id=False), self)
            section_lbl.setObjectName('sidebarSectionLabel')
            layout.addWidget(section_lbl)
            if entry.get('label_key'):
                self._section_labels.append({'widget': section_lbl, 'label_key': entry['label_key'], 'label_default': entry.get('label', '')})
            for it in entry.get('items', []):
                if it.get('type') == 'expandable':
                    layout.addWidget(self._make_expandable(it))
                else:
                    layout.addWidget(self._make_item(it))
            continue
    def _make_item(self, item: Dict[str, Any]) -> SidebarItem:
        btn = SidebarItem(item_id=item['id'], label=self._resolve_label(item), icon_key=item.get('icon'), badge_text=item.get('badge'), parent=self)
        btn.clicked.connect((lambda _checked=False, i=item: self._on_item_clicked(i)))
        self._all_items[item['id']] = btn
        return btn
    def _make_expandable(self, item: Dict[str, Any]) -> SidebarExpandable:
        exp = SidebarExpandable(item_id=item['id'], label=self._resolve_label(item), icon_key=item.get('icon'), subitems=item.get('subitems', []), parent=self)
        for sub in item.get('subitems', []):
            chave = sub.get('label_key')
            if not chave:
                continue
            if 'id' in sub:
                self._items_label_keys[sub['id']] = chave
                if self._tm is None:
                    continue
                if sub['id'] in exp.sub_buttons:
                    novo_label = self._resolve_label(sub, registrar_id=False)
                    exp.sub_buttons[sub['id']].set_label(novo_label)
        self._all_items[item['id']] = exp.header
        self._expansor_ids.add(item['id'])
        for sid, btn in exp.sub_buttons.items():
            self._all_items[sid] = btn
        exp.sub_clicked.connect(self._on_sub_clicked)
        return exp
    def _on_item_clicked(self, item: Dict[str, Any]) -> None:
        self.set_active_item(item['id'])
        self._dispatch_callback(item.get('callback'), item.get('args') or [])
    def _on_sub_clicked(self, parent_id: str, sub: Dict[str, Any]) -> None:
        self.set_active_item(sub['id'])
        self._dispatch_callback(sub.get('callback'), sub.get('args') or [])
    def _dispatch_callback(self, callback_name: Optional[str], args: List[Any]) -> None:
        if not callback_name:
            return
        if self.main_window is None:
            print(f"[Sidebar] main_window nao definida ÔÇö ignorando '{callback_name}'.")
            return
        method = getattr(self.main_window, callback_name, None)
        if method is None or not callable(method):
            print(f"[Sidebar] metodo '{callback_name}' nao encontrado em MainWindow.")
            return
        try:
            method(*args)
            return
        except Exception as exc:
            print(f"[Sidebar] erro ao executar '{callback_name}': {type(exc).__name__}")
    def set_active_item(self, item_id: str) -> None:
        if self._active_id == item_id:
            return
        if self._active_id and self._active_id in self._all_items:
            self._all_items[self._active_id].set_active(False)
        if item_id in self._all_items:
            self._all_items[item_id].set_active(True)
            self._active_id = item_id
            self.item_activated.emit(item_id)
    def update_responsive_width(self, screen_width: int) -> None:
        if screen_width < SIDEBAR_CONFIG['rail_breakpoint_w']:
            self.setFixedWidth(SIDEBAR_CONFIG['width_compact'])
            return
        if screen_width < 1600:
            self.setFixedWidth(SIDEBAR_CONFIG['width_compact'])
            return
        self.setFixedWidth(SIDEBAR_CONFIG['width_normal'])
    def set_badge_visible(self, item_id: str, visible: bool) -> None:
        btn = self._all_items.get(item_id)
        if btn is None:
            return
        try:
            badge = getattr(btn, '_badge', None)
            if badge is not None:
                badge.setVisible(visible)
                return
        except Exception:
            pass
    def set_badge_text(self, item_id: str, text: str) -> None:
        btn = self._all_items.get(item_id)
        if btn is None:
            return
        try:
            badge = getattr(btn, '_badge', None)
            if badge is not None:
                badge.setText(text)
                badge.adjustSize()
                return
        except Exception:
            pass
    def set_translation_manager(self, translation_manager: Optional[Any]) -> None:
        self._tm = translation_manager
        self.refresh_translations()
    def refresh_translations(self) -> None:
        if self._tm is None:
            return
        for entry in self._section_labels:
            try:
                w = entry['widget']
                chave = entry['label_key']
                default = entry.get('label_default', '')
                valor = self._tm.get_text(chave)
                if not isinstance(valor, str) or valor == chave or not valor:
                    valor = default
                w.setText(valor)
            except Exception:
                continue
        for item_id, chave in self._items_label_keys.items():
            btn = self._all_items.get(item_id)
            if btn is not None:
                try:
                    valor = self._tm.get_text(chave)
                    if isinstance(valor, str):
                        if valor == chave or not valor:
                            continue
                        if item_id in self._expansor_ids:
                            btn.set_label(valor + SidebarExpandable._HEADER_SUFFIX)
                        else:
                            btn.set_label(valor)
                    else:
                        return
                except Exception:
                    continue
class _DemoMainWindow(QWidget):
    def __getattr__(self, name: str):
        if name.startswith('abrir_'):
            def _stub(*args, **kwargs):
                print(f'[demo] {name}({args}, {kwargs}) chamado')
            return _stub
        raise AttributeError(name)
def _run_standalone_demo() -> int:
    from PyQt5.QtWidgets import QApplication, QMainWindow
    app = QApplication.instance() or QApplication([])
    win = QMainWindow()
    win.setWindowTitle('Sidebar ÔÇö Demo standalone')
    win.resize(1366, 768)
    central = QWidget()
    h = QHBoxLayout(central)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(0)
    sidebar = Sidebar(parent_main_window=_DemoMainWindow())
    h.addWidget(sidebar)
    placeholder = QLabel("<h2 style='color:#aaa'>Conteudo do dashboard apareceria aqui</h2><p style='color:#888'>Clique nos itens do sidebar para testar a navegacao.</p>")
    placeholder.setAlignment(Qt.AlignCenter)
    placeholder.setStyleSheet('background-color: #1c2533;')
    h.addWidget(placeholder, 1)
    win.setCentralWidget(central)
    win.show()
    return app.exec_()
if __name__ == '__main__':
    raise SystemExit(_run_standalone_demo())
