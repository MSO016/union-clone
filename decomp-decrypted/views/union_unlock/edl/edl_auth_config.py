from typing import Optional
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QCheckBox, QComboBox)
from PyQt5.QtGui import (QFont, QPalette, QColor)
from PyQt5.QtCore import Qt
try:
    from app.views.union_unlock.edl.config import SVG_SETA_DOWN
except ImportError:
    from config import SVG_SETA_DOWN
AUTH_TYPES = [('xiaomi', 'Xiaomi (RSA)'), ('oneplus', 'OnePlus (Crypto)'), ('oppo_vip', 'OPPO / Realme (VIP)'), ('oppo_vip2', 'OPPO / Realme (VIP 2)')]
_SVG_PATH = SVG_SETA_DOWN.replace('\\', '/')
class AuthSelectorWidget(QWidget):
    _STYLE = f'\n        AuthSelectorWidget {{ background: transparent; }}\n        QCheckBox {{\n            color: #2c3e50;\n            spacing: 6px;\n        }}\n        QCheckBox::indicator {{\n            width: 16px;\n            height: 16px;\n            border: 2px solid #7f8c8d;\n            border-radius: 3px;\n            background-color: #ffffff;\n        }}\n        QCheckBox::indicator:hover {{\n            border-color: #2471a3;\n        }}\n        QCheckBox::indicator:checked {{\n            border-color: #2471a3;\n            background-color: #2471a3;\n        }}\n        QComboBox {{\n            color: #2c3e50;\n            background-color: #ffffff;\n            border: 1px solid #bdc3c7;\n            border-radius: 4px;\n            padding: 2px 8px 2px 6px;\n            min-width: 130px;\n        }}\n        QComboBox:hover {{ border-color: #2471a3; }}\n        QComboBox::drop-down {{\n            subcontrol-origin: padding;\n            subcontrol-position: top right;\n            width: 22px;\n            border-left: 1px solid #bdc3c7;\n            border-top-right-radius: 4px;\n            border-bottom-right-radius: 4px;\n            background-color: #ecf0f1;\n        }}\n        QComboBox::drop-down:hover {{\n            background-color: #d5dbdb;\n        }}\n        QComboBox::down-arrow {{\n            image: url({_SVG_PATH});\n            width: 10px;\n            height: 10px;\n        }}\n        QComboBox QAbstractItemView {{\n            background-color: #ffffff;\n            color: #2c3e50;\n            border: 1px solid #bdc3c7;\n            selection-background-color: #2471a3;\n            selection-color: #ffffff;\n            outline: none;\n        }}\n    '
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(self._STYLE)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(8)
        self._cb = QCheckBox('Forcar autenticacao')
        self._cb.setFont(QFont('Segoe UI', 9))
        self._cb.setCursor(Qt.PointingHandCursor)
        self._cb.toggled.connect(self._on_toggle)
        lay.addWidget(self._cb)
        self._combo = QComboBox()
        self._combo.setFont(QFont('Segoe UI', 9))
        self._combo.setFixedWidth(160)
        self._combo.setFixedHeight(26)
        for key, label in AUTH_TYPES:
            self._combo.addItem(label, key)
        self._combo.setVisible(False)
        lay.addWidget(self._combo)
        lay.addStretch()
    def _on_toggle(self, checked: bool):
        self._combo.setVisible(checked)
    def is_forced(self) -> bool:
        return self._cb.isChecked()
    def get_auth_type(self) -> Optional[str]:
        if not self._cb.isChecked():
            return
        return self._combo.currentData()
    def set_auth_type(self, tipo: str):
        if not tipo:
            return
        self._cb.setChecked(True)
        for i in range(self._combo.count()):
            if self._combo.itemData(i) == tipo:
                self._combo.setCurrentIndex(i)
                return
        base = tipo.split(':')[0] if ':' in tipo else None
        if base:
            for i in range(self._combo.count()):
                if self._combo.itemData(i) == base:
                    self._combo.setCurrentIndex(i)
                    return
    def reset(self):
        self._cb.setChecked(False)
def resolver_auth_type(requer_auth_db: Optional[str], selector: Optional[AuthSelectorWidget]) -> Optional[str]:
    if selector and selector.is_forced():
        forced = selector.get_auth_type()
        if forced and requer_auth_db and ':' in requer_auth_db:
            base_db = requer_auth_db.split(':')[0]
            if base_db == forced:
                return requer_auth_db
        return forced
    if requer_auth_db:
        return requer_auth_db
def is_oppo_vip(requer_auth: Optional[str]) -> bool:
    if not requer_auth:
        return False
    if requer_auth.startswith('oppo_vip2'):
        return False
    return requer_auth.startswith('oppo_vip')
def is_oppo_vip2(requer_auth: Optional[str]) -> bool:
    return bool(requer_auth) and requer_auth.startswith('oppo_vip2')
def extrair_vip_chipset(requer_auth: Optional[str]) -> Optional[str]:
    if not requer_auth or ':' not in requer_auth:
        return
    try:
        return requer_auth.split(':', 1)[1].strip().lower() or None
    except (IndexError, AttributeError):
        return
