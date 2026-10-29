"""Tema (claro/escuro) do app via QSS."""
from __future__ import annotations

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

_DARK_QSS = """
QMainWindow, QDialog { background-color: #1e1f24; }
QWidget { color: #e6e6e6; font-size: 13px; }
QPushButton { background-color: #2f3138; border: 1px solid #44464d;
  border-radius: 4px; padding: 5px 12px; }
QPushButton:hover { background-color: #3a3d45; }
QPushButton:disabled { color: #77787e; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {
  background-color: #2a2c32; border: 1px solid #44464d; border-radius: 3px;
  padding: 3px 6px; selection-background-color: #3d6ea8; }
QTableWidget, QTableView, QListView, QTreeView {
  background-color: #232529; alternate-background-color: #2a2c32;
  border: 1px solid #3a3c42; gridline-color: #33353b; }
QHeaderView::section { background-color: #2a2c32; color: #c9c9cf;
  border: none; padding: 4px; }
QMenuBar { background-color: #1a1b1f; }
QMenuBar::item:selected { background-color: #2f3138; }
QMenu { background-color: #232529; border: 1px solid #3a3c42; }
QMenu::item:selected { background-color: #3d6ea8; }
QStatusBar { background-color: #1a1b1f; color: #b7b7bd; }
QScrollBar:vertical { background: #1e1f24; width: 11px; }
QScrollBar::handle:vertical { background: #44464d; border-radius: 5px; min-height: 24px; }
QTabWidget::pane { border: 1px solid #3a3c42; }
QTabBar::tab { background-color: #2a2c32; padding: 5px 12px;
  border: 1px solid #3a3c42; border-bottom: none; }
QTabBar::tab:selected { background-color: #1e1f24; }
QGroupBox { border: 1px solid #3a3c42; border-radius: 4px; margin-top: 8px; padding-top: 8px; }
QLabel#tituloModulo { font-size: 18px; font-weight: bold; color: #ffffff; }
"""

_LIGHT_QSS = """
QMainWindow, QDialog { background-color: #f4f5f7; }
QWidget { color: #1d1e22; font-size: 13px; }
QPushButton { background-color: #ffffff; border: 1px solid #c9cbd1;
  border-radius: 4px; padding: 5px 12px; }
QPushButton:hover { background-color: #eceef1; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {
  background-color: #ffffff; border: 1px solid #c9cbd1; border-radius: 3px;
  padding: 3px 6px; selection-background-color: #b6d4f0; }
QTableWidget, QTableView, QListView, QTreeView {
  background-color: #ffffff; alternate-background-color: #f6f7f9;
  border: 1px solid #d6d8de; gridline-color: #e6e8ec; }
QHeaderView::section { background-color: #eef0f3; color: #3a3c42;
  border: none; padding: 4px; }
QMenuBar { background-color: #ffffff; }
QMenu { background-color: #ffffff; border: 1px solid #d6d8de; }
QMenu::item:selected { background-color: #b6d4f0; }
QStatusBar { background-color: #ffffff; color: #5a5c62; }
QTabBar::tab { background-color: #e9ebee; padding: 5px 12px;
  border: 1px solid #d6d8de; border-bottom: none; }
QTabBar::tab:selected { background-color: #f4f5f7; }
QGroupBox { border: 1px solid #d6d8de; border-radius: 4px; margin-top: 8px; padding-top: 8px; }
QLabel#tituloModulo { font-size: 18px; font-weight: bold; color: #1d1e22; }
"""


def _paleta_escura() -> QPalette:
    p = QPalette()
    bg = QColor("#1e1f24")
    fg = QColor("#e6e6e6")
    p.setColor(QPalette.ColorRole.Window, bg)
    p.setColor(QPalette.ColorRole.WindowText, fg)
    p.setColor(QPalette.ColorRole.Base, QColor("#232529"))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor("#2a2c32"))
    p.setColor(QPalette.ColorRole.Text, fg)
    p.setColor(QPalette.ColorRole.Button, QColor("#2f3138"))
    p.setColor(QPalette.ColorRole.ButtonText, fg)
    p.setColor(QPalette.ColorRole.Highlight, QColor("#3d6ea8"))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    return p


def aplicar_tema(app: QApplication, modo: str = "escuro") -> None:
    if modo == "claro":
        app.setStyleSheet(_LIGHT_QSS)
        app.setPalette(app.style().standardPalette())
    else:
        app.setStyleSheet(_DARK_QSS)
        app.setPalette(_paleta_escura())
