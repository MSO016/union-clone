from __future__ import annotations
import os
_C1 = '#0D47A1'
_C2 = '#2196F3'
_C3 = '#f7f9fc'
_C4 = 'rgba(13, 71, 161, 0.14)'
_C5 = '#3a4a63'
_C6 = '#c5d6ec'
_C7 = 'rgba(33, 150, 243, 0.22)'
_C8 = _C1
_C9 = '#ffffff'
_C10 = _C1
_C11 = '#bcd0ea'
_ON1 = 'abas_ferramentas'
_ON2 = 'tabs_ferramentas'
_QSS = ''.join(['\nQTabWidget#', f'{_ON1}', '::pane {\n    border: none;\n    background: ', f'{_C3}', ';\n    border-top: 2px solid ', f'{_C1}', ';\n    padding: 0px;\n    top: -1px;\n}\n\nQTabWidget#', f'{_ON1}', '::tab-bar {\n    alignment: left;\n    left: 8px;\n}\n\nQTabBar#', f'{_ON2}', '::tab {\n    background: ', f'{_C4}', ';\n    color: ', f'{_C5}', ';\n    border: 1px solid ', f'{_C6}', ';\n    border-bottom: none;\n    border-top-left-radius: 8px;\n    border-top-right-radius: 8px;\n    padding: 9px 16px;\n    margin-right: 2px;\n    font-family: "Segoe UI", "Calibri", sans-serif;\n    font-size: 13px;\n    font-weight: 600;\n    min-width: 110px;\n    min-height: 22px;\n}\n\nQTabBar#', f'{_ON2}', '::tab:hover:!selected {\n    background: ', f'{_C7}', ';\n    color: ', f'{_C8}', ';\n    border-color: ', f'{_C11}', ';\n}\n\nQTabBar#', f'{_ON2}', '::tab:selected {\n    background: ', f'{_C9}', ';\n    color: ', f'{_C10}', ';\n    font-weight: 700;\n    border: 1px solid ', f'{_C11}', ';\n    border-bottom: 2px solid ', f'{_C9}', ';\n    border-top: 4px solid ', f'{_C2}', ';\n    margin-top: 0px;\n}\n\nQTabBar#', f'{_ON2}', '::tab:!selected {\n    margin-top: 3px;\n}\n\nQTabBar#', f'{_ON2}', '::tab:focus {\n    outline: none;\n}\n\nQTabBar#', f'{_ON2}', ' QToolButton {\n    background: ', f'{_C4}', ';\n    border: 1px solid ', f'{_C11}', ';\n    border-radius: 6px;\n    padding: 2px;\n    margin: 4px 2px;\n    color: ', f'{_C1}', ';\n}\n\nQTabBar#', f'{_ON2}', ' QToolButton:hover {\n    background: ', f'{_C7}', ';\n    color: ', f'{_C1}', ';\n}\n'])
TOOLS_TABS_QSS = _QSS
UNION_BLUE = _C1
UNION_BLUE_ACCENT = _C2
_SVG_SCROLL_LEFT = 'icons_svg/caret-left-fill.svg'
_SVG_SCROLL_RIGHT = 'icons_svg/caret-right-fill.svg'
def is_modern_enabled() -> bool:
    return os.environ.get('UI_TOOLS_TABS_MODERN', '1') == '1'
def _resolver_svgs_scroller():
    '''Resolve caret left/right via PathManager. (None, None) se faltar.'''
    try:
        from app.utils.path_manager import PathManager
        left = PathManager.get_resource_path(_SVG_SCROLL_LEFT)
        right = PathManager.get_resource_path(_SVG_SCROLL_RIGHT)
        left_ok = left if left and os.path.isfile(left) else None
        right_ok = right if right and os.path.isfile(right) else None
        return left_ok, right_ok
    except Exception:
        return (None, None)
def _url_qss(path):
    return str(path).replace('\\', '/')
def _qss_scroller_nativo():
    '''Scroller nativo a direita; SVG no subcontrole; oculta o tear a esquerda.'''
    left, right = _resolver_svgs_scroller()
    parts = [f'QTabBar#{_ON2}::scroller {{ width: 48px; }}', f'QTabBar#{_ON2}::tear {{ width: 0px; border: none; image: none; }}']
    if left:
        u = _url_qss(left)
        parts.append(f'QTabBar#{_ON2} QToolButton::left-arrow {{ image: url("{u}"); width: 18px; height: 18px; }}')
        parts.append(f'QTabBar#{_ON2} QToolButton::left-arrow:disabled {{ image: url("{u}"); width: 18px; height: 18px; }}')
    if right:
        u = _url_qss(right)
        parts.append(f'QTabBar#{_ON2} QToolButton::right-arrow {{ image: url("{u}"); width: 18px; height: 18px; }}')
        parts.append(f'QTabBar#{_ON2} QToolButton::right-arrow:disabled {{ image: url("{u}"); width: 18px; height: 18px; }}')
    return '\n'.join(parts)
def apply_tools_tabs_theme(tab_widget) -> bool:
    if tab_widget is None:
        return False
    try:
        if not tab_widget.objectName():
            tab_widget.setObjectName(_ON1)
        bar = tab_widget.tabBar()
        if bar is not None:
            if not bar.objectName():
                bar.setObjectName(_ON2)
            bar.setUsesScrollButtons(True)
            bar.setExpanding(False)
        try:
            from PyQt5.QtCore import Qt as _Qt
            bar.setElideMode(_Qt.ElideNone)
        except Exception:
            pass
        else:
            extra = ''
    except Exception:
        return False
    try:
        try:
            extra = _qss_scroller_nativo()
        except Exception:
            extra = ''
    except Exception:
        return False
    tab_widget.setStyleSheet(_QSS + extra)
    return True
