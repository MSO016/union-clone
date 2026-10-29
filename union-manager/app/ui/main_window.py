"""Janela principal: sidebar de navegação + área central (stack de módulos)."""
from __future__ import annotations

import sqlite3

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..core.db.repos.cliente_repo import ClienteRepository
from ..core.db.repos.config_repo import ConfigRepository
from ..core.db.repos.conhecimento_repo import ConhecimentoRepository
from ..core.db.repos.ordem_repo import OrdemRepository
from ..core.services.cliente_service import ClienteService
from ..core.services.ordem_service import OrdemServicoService
from ..core.services.relatorio_service import RelatorioService
from .i18n import t
from .views.clientes.clientes_view import ClientesView
from .views.config.config_view import ConfigView
from .views.conhecimento.conhecimento_view import ConhecimentoView
from .views.ferramentas.ferramentas_view import FerramentasView
from .views.ordens.ordens_view import OrdensView
from .views.relatorios.relatorios_view import RelatoriosView


class _Sidebar(QFrame):
    """Barra lateral com navegação por módulos."""

    def __init__(self, pai: QWidget | None = None) -> None:
        super().__init__(pai)
        self.setFixedWidth(220)
        self.setObjectName("sidebar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        titulo = QLabel(t("app_titulo"))
        titulo.setObjectName("tituloModulo")
        slogan = QLabel(t("slogan"))
        slogan.setWordWrap(True)
        layout.addWidget(titulo)
        layout.addWidget(slogan)
        layout.addSpacing(8)

        self.lista = QListWidget()
        self.lista.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self.lista)

    def adicionar_modulo(self, chave: str, rotulo: str) -> None:
        item = QListWidgetItem(rotulo)
        item.setData(Qt.ItemDataRole.UserRole, chave)
        self.lista.addItem(item)


class MainWindow(QMainWindow):
    def __init__(
        self,
        conexao: sqlite3.Connection | None = None,
        caminho_banco=None,
    ) -> None:
        super().__init__()
        self._conexao = conexao
        self._caminho_banco = caminho_banco
        self.setWindowTitle(t("app_titulo"))
        self.resize(1280, 800)
        self.setMinimumSize(1200, 700)

        central = QWidget()
        self.setCentralWidget(central)
        h = QHBoxLayout(central)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        self._sidebar = _Sidebar()
        h.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        h.addWidget(self._stack, 1)

        # Módulos registrados aqui conforme forem implementados (Fase 6).
        self._registar_modulos()
        self._sidebar.lista.currentRowChanged.connect(self._stack.setCurrentIndex)
        if self._sidebar.lista.count():
            self._sidebar.lista.setCurrentRow(0)

        self.statusBar().showMessage(t("slogan"))

    def _registar_modulos(self) -> None:
        if self._conexao is None:
            # Fallback: painel inicial sem dados (ex.: testes de UI).
            boas_vindas = QLabel(t("slogan"))
            boas_vindas.setAlignment(Qt.AlignmentFlag.AlignCenter)
            boas_vindas.setObjectName("tituloModulo")
            self._stack.addWidget(boas_vindas)
            self._sidebar.adicionar_modulo("dashboard", t("app_titulo"))
            return

        cliente_repo = ClienteRepository(self._conexao)
        ordem_repo = OrdemRepository(self._conexao)
        conhecimento_repo = ConhecimentoRepository(self._conexao)

        cliente_service = ClienteService(cliente_repo)
        ordem_service = OrdemServicoService(ordem_repo, conhecimento_repo)

        clientes_view = ClientesView(cliente_service, pai=self)
        ordens_view = OrdensView(
            ordem_service,
            cliente_service,
            config_repo=ConfigRepository(self._conexao),
            pai=self,
        )
        conhecimento_view = ConhecimentoView(conhecimento_repo, pai=self)
        relatorios_view = RelatoriosView(RelatorioService(self._conexao), pai=self)
        ferramentas_view = FerramentasView(pai=self)
        config_view = ConfigView(
            ConfigRepository(self._conexao),
            conexao=self._conexao,
            caminho_banco=self._caminho_banco,
            pai=self,
        )

        self._stack.addWidget(clientes_view)
        self._sidebar.adicionar_modulo("clientes", t("cliente_titulo"))
        self._stack.addWidget(ordens_view)
        self._sidebar.adicionar_modulo("ordens", t("os_titulo"))
        self._stack.addWidget(conhecimento_view)
        self._sidebar.adicionar_modulo("conhecimento", t("kb_titulo"))
        self._stack.addWidget(relatorios_view)
        self._sidebar.adicionar_modulo("relatorios", t("menu_relatarios"))
        self._stack.addWidget(ferramentas_view)
        self._sidebar.adicionar_modulo("ferramentas", t("ferr_titulo"))
        self._stack.addWidget(config_view)
        self._sidebar.adicionar_modulo("config", t("menu_config"))
