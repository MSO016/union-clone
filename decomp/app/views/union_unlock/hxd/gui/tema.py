'''
TECH UNION SOLUTIONS ÔÇö Design Tokens e QSS
Tema LIGHT seguindo padr├úo de produ├º├úo (edl_main, tools_tabs_theme).
'''
BG = '#f5f5f5'
BG_WHITE = '#ffffff'
BG_TAB_PANE = '#f7f9fc'
PRIMARY = '#1428A0'
UNION_BLUE = '#0D47A1'
UNION_ACCENT = '#2196F3'
UNION_LIGHT = '#bcd0ea'
TEXT = '#2c3e50'
TEXT_MUTED = '#7f8c8d'
TEXT_LABEL = '#3a4a63'
BORDER = '#bdc3c7'
BORDER_LIGHT = '#c5d6ec'
GREEN = '#27ae60'
GREEN_DARK = '#1e8449'
YELLOW = '#f39c12'
RED = '#e53935'
RED_BG = '#B71C1C'
ORANGE = '#FF9800'
WHITE = '#ffffff'
HEADER_BG = PRIMARY
_OBJ_NAME = 'hxd_main_widget'
def gerar_qss_principal() -> str:
    '''QSS escopado por objectName ÔÇö n├úo vaza para widgets externos.'''
    s = f'#{_OBJ_NAME}'
    return ''.join(['\n        ', f'{s}', ' {\n            background-color: ', f'{BG}', ';\n            color: ', f'{TEXT}', ";\n            font-family: 'Segoe UI', 'Calibri', sans-serif;\n            font-size: 13px;\n        }\n        ", f'{s}', ' QLabel {\n            color: ', f'{TEXT}', ';\n            background: transparent;\n        }\n        ', f'{s}', ' QGroupBox {\n            border: 1px solid ', f'{BORDER}', ';\n            border-radius: 6px;\n            margin-top: 12px;\n            padding: 14px 10px 10px 10px;\n            font-weight: bold;\n            color: ', f'{TEXT_MUTED}', ';\n            background-color: ', f'{BG_WHITE}', ';\n        }\n        ', f'{s}', ' QGroupBox::title {\n            subcontrol-origin: margin;\n            left: 12px;\n            padding: 0 6px;\n            color: ', f'{PRIMARY}', ';\n        }\n        ', f'{s}', ' QScrollArea {\n            border: none;\n            background: transparent;\n        }\n        ', f'{s}', ' QScrollBar:vertical {\n            background: ', f'{BG}', ';\n            width: 8px;\n            border-radius: 4px;\n        }\n        ', f'{s}', ' QScrollBar::handle:vertical {\n            background: ', f'{BORDER}', ';\n            border-radius: 4px;\n            min-height: 30px;\n        }\n        ', f'{s}', ' QScrollBar::handle:vertical:hover {\n            background: ', f'{UNION_ACCENT}', ';\n        }\n        ', f'{s}', ' QScrollBar::add-line:vertical, ', f'{s}', ' QScrollBar::sub-line:vertical {\n            height: 0px;\n        }\n        ', f'{s}', ' QScrollBar:horizontal {\n            background: ', f'{BG}', ';\n            height: 8px;\n            border-radius: 4px;\n        }\n        ', f'{s}', ' QScrollBar::handle:horizontal {\n            background: ', f'{BORDER}', ';\n            border-radius: 4px;\n            min-width: 30px;\n        }\n        ', f'{s}', ' QScrollBar::handle:horizontal:hover {\n            background: ', f'{UNION_ACCENT}', ';\n        }\n        ', f'{s}', ' QScrollBar::add-line:horizontal, ', f'{s}', ' QScrollBar::sub-line:horizontal {\n            width: 0px;\n        }\n        ', f'{s}', ' QSplitter::handle {\n            background: ', f'{BORDER}', ';\n            width: 1px;\n        }\n    '])
def gerar_qss_log() -> str:
    '''QSS para o terminal de log (fundo escuro ÔÇö padr├úo Logs do Sistema).'''
    return "\n        QTextEdit {\n            background-color: #1e1e1e;\n            color: #ffffff;\n            font-family: 'Consolas', 'Courier New', monospace;\n            font-size: 12px;\n            border: 1px solid #2a2a2a;\n            border-radius: 4px;\n            padding: 8px;\n            selection-background-color: #264f78;\n        }\n        QTextEdit QScrollBar:vertical {\n            background: #1e1e1e;\n            width: 8px;\n            border-radius: 4px;\n        }\n        QTextEdit QScrollBar::handle:vertical {\n            background: #3a3a3a;\n            border-radius: 4px;\n            min-height: 30px;\n        }\n        QTextEdit QScrollBar::handle:vertical:hover {\n            background: #555;\n        }\n        QTextEdit QScrollBar::add-line:vertical,\n        QTextEdit QScrollBar::sub-line:vertical {\n            height: 0px;\n        }\n    "
PRIMARY_HOVER = '#0D1B69'
BG_DARK = '#e8e8e8'
def gerar_qss_botao(cor_bg: str=None, cor_fg: str='white') -> str:
    '''QSS para bot├úo padr├úo ÔÇö estilo produ├º├úo EDL.'''
    bg = cor_bg or PRIMARY
    return f"\n        QPushButton {{\n            background-color: {bg};\n            color: {cor_fg};\n            border: none;\n            border-radius: 6px;\n            padding: 6px 12px;\n            font-family: 'Segoe UI', sans-serif;\n            font-size: 12px;\n            font-weight: bold;\n        }}\n        QPushButton:hover {{\n            background-color: {PRIMARY_HOVER};\n        }}\n        QPushButton:pressed {{\n            background-color: {UNION_BLUE};\n        }}\n        QPushButton:disabled {{\n            background-color: {BORDER};\n            color: {TEXT_MUTED};\n        }}\n    "
def gerar_qss_botao_outline() -> str:
    '''QSS para bot├úo secund├írio (outline) ÔÇö a├º├úo cautelosa.'''
    return f"\n        QPushButton {{\n            background-color: {BG_DARK};\n            color: {TEXT};\n            border: 1px solid {BORDER};\n            border-radius: 6px;\n            padding: 6px 12px;\n            font-family: 'Segoe UI', sans-serif;\n            font-size: 12px;\n            font-weight: bold;\n        }}\n        QPushButton:hover {{\n            background-color: {BORDER};\n        }}\n        QPushButton:pressed {{\n            background-color: {PRIMARY};\n            color: white;\n        }}\n        QPushButton:disabled {{\n            background-color: {BG};\n            color: {BORDER};\n            border: 1px solid {BG_DARK};\n        }}\n    "
