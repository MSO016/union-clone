try:
    from app.views.union_unlock.hxd.gui.tema import (BG, BG_WHITE, PRIMARY, UNION_BLUE, UNION_ACCENT, UNION_LIGHT, TEXT, TEXT_MUTED, TEXT_LABEL, BORDER, BORDER_LIGHT, GREEN, GREEN_DARK, YELLOW, RED, RED_BG, ORANGE, WHITE, PRIMARY_HOVER, BG_DARK, gerar_qss_log)
except ImportError:
    BG = '#f5f5f5'
    BG_WHITE = '#ffffff'
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
    PRIMARY_HOVER = '#0D1B69'
    BG_DARK = '#e8e8e8'
    def gerar_qss_log():
        return "\n            QTextEdit {\n                background-color: #1e1e1e;\n                color: #ffffff;\n                font-family: 'Consolas', 'Courier New', monospace;\n                font-size: 12px;\n                border: 1px solid #2a2a2a;\n                border-radius: 4px;\n                padding: 8px;\n                selection-background-color: #264f78;\n            }\n        "
STATUS_CONNECTED_BG = GREEN
STATUS_DISCONNECTED_BG = RED
BTN_PRIMARY_BG = UNION_ACCENT
BTN_PRIMARY_HOVER = UNION_BLUE
BTN_PRIMARY_PRESSED = PRIMARY
BTN_DISABLED_BG = BORDER
BTN_SUCCESS_BG = GREEN
BTN_SUCCESS_HOVER = '#229954'
BTN_SUCCESS_PRESSED = GREEN_DARK
BTN_DANGER_BG = ORANGE
BTN_DANGER_HOVER = '#F4511E'
BTN_DANGER_PRESSED = '#D84315'
ERROR_DIALOG_BTN = RED
ERROR_DIALOG_BTN_HOVER = '#c82333'
LOG_ERROR_COLOR = '#ff5555'
LOG_WARN_COLOR = '#ffcc00'
GROUP_BORDER = BORDER
GROUP_BG = BG_WHITE
GROUP_TITLE = PRIMARY
LABEL_BG = BG
SCROLL_TRACK = BG
SCROLL_HANDLE = BORDER
SCROLL_HANDLE_HOVER = UNION_ACCENT
def qss_group_box() -> str:
    return f'\n        QGroupBox {{\n            font-size: 12px;\n            font-weight: bold;\n            padding: 8px;\n            margin-top: 3px;\n            border: 1px solid {GROUP_BORDER};\n            border-radius: 3px;\n            background-color: {GROUP_BG};\n        }}\n        QGroupBox::title {{\n            subcontrol-origin: margin;\n            left: 7px;\n            padding: 0 3px;\n            color: {GROUP_TITLE};\n        }}\n    '
def qss_btn_primary(min_width: int=160, min_height: int=40) -> str:
    return f'\n        QPushButton {{\n            padding: 8px;\n            font-size: 12px;\n            min-width: {min_width}px;\n            min-height: {min_height}px;\n            background-color: {BTN_PRIMARY_BG};\n            color: {WHITE};\n            border-radius: 4px;\n            font-weight: bold;\n            border: none;\n        }}\n        QPushButton:hover {{\n            background-color: {BTN_PRIMARY_HOVER};\n        }}\n        QPushButton:pressed {{\n            background-color: {BTN_PRIMARY_PRESSED};\n        }}\n        QPushButton:disabled {{\n            background-color: {BTN_DISABLED_BG};\n            color: {TEXT_MUTED};\n        }}\n    '
def qss_btn_diagnostic() -> str:
    return f'\n        QPushButton {{\n            padding: 7px 6px;\n            font-size: 13px;\n            min-width: 120px;\n            max-width: 180px;\n            min-height: 38px;\n            max-height: 38px;\n            background-color: {BTN_PRIMARY_BG};\n            color: {WHITE};\n            border-radius: 4px;\n            font-weight: bold;\n            border: none;\n        }}\n        QPushButton:hover {{\n            background-color: {BTN_PRIMARY_HOVER};\n        }}\n        QPushButton:pressed {{\n            background-color: {BTN_PRIMARY_PRESSED};\n        }}\n        QPushButton:disabled {{\n            background-color: {BTN_DISABLED_BG};\n            color: {TEXT_MUTED};\n        }}\n    '
def qss_btn_success(min_width: int=140, min_height: int=40) -> str:
    return f'\n        QPushButton {{\n            padding: 8px;\n            font-size: 12px;\n            min-width: {min_width}px;\n            min-height: {min_height}px;\n            background-color: {BTN_SUCCESS_BG};\n            color: {WHITE};\n            border-radius: 4px;\n            font-weight: bold;\n            border: none;\n        }}\n        QPushButton:hover {{\n            background-color: {BTN_SUCCESS_HOVER};\n        }}\n        QPushButton:pressed {{\n            background-color: {BTN_SUCCESS_PRESSED};\n        }}\n        QPushButton:disabled {{\n            background-color: {BTN_DISABLED_BG};\n            color: {TEXT_MUTED};\n        }}\n    '
def qss_btn_danger(min_width: int=280, min_height: int=55) -> str:
    return f'\n        QPushButton {{\n            padding: 12px;\n            font-size: 14px;\n            min-width: {min_width}px;\n            min-height: {min_height}px;\n            background-color: {BTN_DANGER_BG};\n            color: {WHITE};\n            border-radius: 6px;\n            font-weight: bold;\n            border: none;\n        }}\n        QPushButton:hover {{\n            background-color: {BTN_DANGER_HOVER};\n        }}\n        QPushButton:pressed {{\n            background-color: {BTN_DANGER_PRESSED};\n        }}\n        QPushButton:disabled {{\n            background-color: {BTN_DISABLED_BG};\n            color: {TEXT_MUTED};\n        }}\n    '
def qss_status_label(connected: bool) -> str:
    bg = STATUS_CONNECTED_BG if connected else STATUS_DISCONNECTED_BG
    return f'\n        QLabel {{\n            padding: 10px;\n            border-radius: 5px;\n            background: {bg};\n            color: {WHITE};\n            font-weight: bold;\n            font-size: 12px;\n        }}\n    '
def qss_log_area() -> str:
    return "\n        QTextEdit {\n            font-family: 'Consolas', 'Courier New', monospace;\n            font-size: 14px;\n            background-color: #1e1e1e;\n            color: #ffffff;\n            border: 1px solid #2a2a2a;\n            border-radius: 4px;\n            padding: 8px;\n            min-height: 300px;\n            selection-background-color: #264f78;\n        }\n        QScrollBar:vertical {\n            border: none;\n            background: #1e1e1e;\n            width: 10px;\n            margin: 0px;\n        }\n        QScrollBar::handle:vertical {\n            background: #3a3a3a;\n            min-height: 20px;\n            border-radius: 5px;\n        }\n        QScrollBar::handle:vertical:hover {\n            background: #555;\n        }\n        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n            height: 0px;\n        }\n    "
def qss_scroll_area() -> str:
    return f'\n        QScrollArea {{\n            background: transparent;\n            border: none;\n        }}\n        QScrollArea > QWidget > QWidget {{\n            background: transparent;\n        }}\n        QScrollBar:vertical {{\n            border: none;\n            background: {SCROLL_TRACK};\n            width: 10px;\n            border-radius: 5px;\n        }}\n        QScrollBar::handle:vertical {{\n            background: {SCROLL_HANDLE};\n            min-height: 20px;\n            border-radius: 5px;\n            margin: 2px;\n        }}\n        QScrollBar::handle:vertical:hover {{\n            background: {SCROLL_HANDLE_HOVER};\n        }}\n        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{\n            height: 0px;\n        }}\n        QScrollBar:horizontal {{\n            border: none;\n            background: {SCROLL_TRACK};\n            height: 10px;\n            border-radius: 5px;\n        }}\n        QScrollBar::handle:horizontal {{\n            background: {SCROLL_HANDLE};\n            min-width: 20px;\n            border-radius: 5px;\n            margin: 2px;\n        }}\n        QScrollBar::handle:horizontal:hover {{\n            background: {SCROLL_HANDLE_HOVER};\n        }}\n        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{\n            width: 0px;\n        }}\n    '
def qss_battery_label() -> str:
    return f'\n        QLabel {{\n            font-size: 12px;\n            padding: 5px 10px;\n            background-color: {LABEL_BG};\n            border-radius: 4px;\n        }}\n        QLabel[labelType="title"] {{\n            font-weight: bold;\n            color: {GROUP_TITLE};\n            background-color: transparent;\n            padding: 5px 2px;\n        }}\n        QLabel[labelType="value"] {{\n            background-color: {LABEL_BG};\n            font-weight: bold;\n            color: {TEXT};\n        }}\n    '
def qss_error_dialog() -> str:
    return f'\n        QMessageBox {{\n            background-color: {BG};\n            min-width: 400px;\n        }}\n        QLabel {{\n            color: {TEXT};\n            font-size: 12px;\n            padding: 10px;\n        }}\n        QPushButton {{\n            padding: 8px 16px;\n            background-color: {ERROR_DIALOG_BTN};\n            color: {WHITE};\n            border: none;\n            border-radius: 4px;\n            font-weight: bold;\n        }}\n        QPushButton:hover {{\n            background-color: {ERROR_DIALOG_BTN_HOVER};\n        }}\n    '
def qss_msg_box_info() -> str:
    return f'\n        QMessageBox {{\n            background-color: {BG};\n        }}\n        QLabel {{\n            min-width: 300px;\n            color: {TEXT};\n        }}\n        QPushButton {{\n            padding: 5px 15px;\n            background-color: {BTN_PRIMARY_BG};\n            color: {WHITE};\n            border: none;\n            border-radius: 3px;\n        }}\n        QPushButton:hover {{\n            background-color: {BTN_PRIMARY_HOVER};\n        }}\n    '
