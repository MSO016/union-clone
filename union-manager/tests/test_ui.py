"""Smoke test da UI (offscreen) — garante que a MainWindow constrói sem erro.

Executar: python -m tests.test_ui
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def main() -> int:
    from PyQt6.QtWidgets import QApplication

    from app.core.db.connection import abrir_conexao
    from app.core.db.migrations.runner import rodar_migracoes
    from app.ui.i18n import get_translation
    from app.ui.main_window import MainWindow

    app = QApplication(sys.argv)

    get_translation().definir_idioma("pt_br")

    with tempfile.TemporaryDirectory() as td:
        conn = abrir_conexao(Path(td) / "ui.db")
        rodar_migracoes(conn)

        janela = MainWindow(conexao=conn)
        janela.show()
        app.processEvents()

        assert janela.windowTitle(), "título vazio"
        assert janela._stack.count() == 6, f"esperava 6 módulos, veio {janela._stack.count()}"
        assert janela._sidebar.lista.count() == 6, "sidebar sem os 6 módulos"

        conn.close()

    print("OK — MainWindow constrói e exibe (offscreen).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
