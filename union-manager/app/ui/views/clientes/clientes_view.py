"""Lista de clientes com busca incremental — SPEC RF-CLI-3."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ....core.services.cliente_service import ClienteService
from ....core.services.ordem_service import ValidacaoError
from ...i18n import t
from .cliente_form import ClienteForm


class ClientesView(QWidget):
    """Módulo de cadastro de clientes."""

    def __init__(self, service: ClienteService, user_id: int = 0, pai=None) -> None:
        super().__init__(pai)
        self._service = service
        self._user_id = user_id

        layout = QVBoxLayout(self)

        topo = QHBoxLayout()
        titulo = QLabel(t("cliente_titulo"))
        titulo.setObjectName("tituloModulo")
        topo.addWidget(titulo)
        topo.addStretch(1)
        btn_novo = QPushButton(t("cliente_novo"))
        btn_novo.clicked.connect(self._novo)
        topo.addWidget(btn_novo)
        layout.addLayout(topo)

        self._busca = QLineEdit()
        self._busca.setPlaceholderText(t("acao_buscar") + "…")
        self._busca.textChanged.connect(self._recarregar)
        layout.addWidget(self._busca)

        self._tabela = QTableWidget(0, 5)
        self._tabela.setHorizontalHeaderLabels(
            ["ID", t("cliente_nome"), t("cliente_telefone"), t("cliente_email"), t("cliente_tipo")]
        )
        self._tabela.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._tabela.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self._tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._tabela)

        acoes = QHBoxLayout()
        btn_editar = QPushButton(t("acao_editar"))
        btn_editar.clicked.connect(self._editar)
        btn_excluir = QPushButton(t("acao_excluir"))
        btn_excluir.clicked.connect(self._excluir)
        acoes.addWidget(btn_editar)
        acoes.addWidget(btn_excluir)
        acoes.addStretch(1)
        layout.addLayout(acoes)

        self._recarregar()

    def _recarregar(self) -> None:
        termo = self._busca.text()
        clientes = (
            self._service.buscar(termo) if termo.strip() else self._service.listar_todos()
        )
        self._tabela.setRowCount(len(clientes))
        for r, c in enumerate(clientes):
            itens = [
                str(c.id or ""),
                c.nome,
                c.telefone,
                c.email,
                "Lojista" if c.tipo.value == "lojista" else "Pessoa Física",
            ]
            for col, texto in enumerate(itens):
                item = QTableWidgetItem(texto)
                item.setData(Qt.ItemDataRole.UserRole, c.id)
                self._tabela.setItem(r, col, item)

    def _cliente_selecionado(self):
        linha = self._tabela.currentRow()
        if linha < 0:
            return None
        cid = self._tabela.item(linha, 0).data(Qt.ItemDataRole.UserRole)
        return self._service.por_id(cid) if cid else None

    def _novo(self) -> None:
        form = ClienteForm(self._service, user_id=self._user_id, pai=self)
        form.salvo.connect(lambda _id: self._recarregar())
        form.exec()

    def _editar(self) -> None:
        cliente = self._cliente_selecionado()
        if cliente is None:
            QMessageBox.information(self, t("aviso"), "Selecione um cliente.")
            return
        form = ClienteForm(self._service, cliente=cliente, user_id=self._user_id, pai=self)
        form.salvo.connect(lambda _id: self._recarregar())
        form.exec()

    def _excluir(self) -> None:
        cliente = self._cliente_selecionado()
        if cliente is None:
            QMessageBox.information(self, t("aviso"), "Selecione um cliente.")
            return
        resp = QMessageBox.question(
            self,
            t("acao_excluir"),
            f"Excluir o cliente '{cliente.nome}'?",
        )
        if resp != QMessageBox.StandardButton.Yes:
            return
        try:
            self._service.excluir(cliente.id or 0)
        except ValidacaoError as e:
            QMessageBox.warning(self, t("aviso"), str(e))
            return
        self._recarregar()
