"""Union Manager — ponto de entrada.

Responsabilidades:
- criar QApplication e aplicar tema (claro/escuro)
- garantir instância única (QSharedMemory)
- garantir diretório de dados + rodar migrações do SQLite
- abrir a MainWindow (sem login de licença — app offline, uso pessoal)

Uso:
    python main.py [--tema escuro|claro] [--dados CAMINHO]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Permite rodar sem instalar como pacote: garante a raiz do projeto no sys.path.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PyQt6.QtCore import QSharedMemory, Qt
from PyQt6.QtWidgets import QApplication, QMessageBox

from app.core.db.connection import abrir_conexao, garantir_diretorio_dados
from app.core.db.migrations.runner import rodar_migracoes
from app.ui.i18n import get_translation
from app.ui.theme.tema import aplicar_tema
from app.ui.main_window import MainWindow

IDENTIFICADOR_INSTANCIA = "UNION_MANAGER_SINGLE_INSTANCE"


def _dados_dir(custom: str | None) -> Path:
    if custom:
        return Path(custom)
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".union-manager")
    return Path(base) / "UnionManager" / "data"


def _configurar_alto_dpi() -> None:
    # PyQt6 habilita high-DPI por padrão, mas garante o modo de escala.
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )


def _criar_app(argv: list[str]) -> QApplication:
    _configurar_alto_dpi()
    return QApplication(argv)


def _instancia_unica(app: QApplication) -> QSharedMemory | None:
    mem = QSharedMemory(IDENTIFICADOR_INSTANCIA)
    if mem.attach():
        # Já há outra instância ativa.
        return None
    mem.create(1)
    # Mantém a referência viva durante toda a execução.
    app._instancia_unica = mem  # type: ignore[attr-defined]
    return mem


def _chechar_dependencies_pdf() -> bool:
    try:
        import pymupdf  # noqa: F401  (PyMuPDF 2.x)

        return True
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Union Manager")
    parser.add_argument("--tema", choices=["claro", "escuro"], default="escuro")
    parser.add_argument("--dados", default=None, help="diretório de dados (default: LOCALAPPDATA)")
    args, qt_args = parser.parse_known_args()

    app = _criar_app([sys.argv[0], *qt_args])

    if _instancia_unica(app) is None:
        QMessageBox.information(
            None,
            "Union Manager",
            "O Union Manager já está em execução.",
        )
        return 0

    dados = _dados_dir(args.dados)
    garantir_diretorio_dados(dados)

    conexao = abrir_conexao(dados / "union.db")
    try:
        rodar_migracoes(conexao)

        tr = get_translation()
        tr.definir_idioma("pt_br")
        app.traducoes = tr  # type: ignore[attr-defined]
        app.conexao = conexao  # type: ignore[attr-defined]
        app.dados_dir = dados  # type: ignore[attr-defined]

        aplicar_tema(app, args.tema)

        if not _chechar_dependencies_pdf():
            # Não bloqueia: relatórios PDF ficam indisponíveis, mas o app funciona.
            QMessageBox.warning(
                None,
                "PDF indisponível",
                "A biblioteca PyMuPDF não foi encontrada.\n"
                "Relatórios em PDF ficarão indisponíveis até instalá-la "
                "(pip install PyMuPDF).",
            )

        janela = MainWindow(conexao=conexao, caminho_banco=dados / "union.db")
        janela.show()
        return app.exec()
    finally:
        conexao.close()


if __name__ == "__main__":
    raise SystemExit(main())
