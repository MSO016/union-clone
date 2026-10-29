"""Dashboard + lista de OS em reparo — SPEC RF-OS-8 e RF-OS-1."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ....core.models.models import StatusOrdem
from ....core.pdf import gerar_ordem_a4, gerar_ordem_termica
from ....core.services.cliente_service import ClienteService
from ....core.services.ordem_service import OrdemServicoService, ValidacaoError
from ...i18n import t
from .encerramento_dialog import EncerramentoDialog
from .ordem_form import OrdemForm


def _rotulo_status(valor: str) -> str:
    if valor == StatusOrdem.EM_REPARO.value:
        return t("status_em_reparo")
    if valor == StatusOrdem.CONCLUIDO_SUCESSO.value:
        return t("status_concluido_sucesso")
    return t("status_concluido_sem_solucao")


def _card(rotulo: str, valor: str) -> QFrame:
    frame = QFrame()
    frame.setObjectName("cardOS")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(16, 12, 16, 12)
    num = QLabel(valor)
    num.setObjectName("tituloModulo")
    lab = QLabel(rotulo)
    lay.addWidget(num)
    lay.addWidget(lab)
    return frame


class OrdensView(QWidget):
    """Módulo de ordens de serviço."""

    def __init__(
        self,
        ordem_service: OrdemServicoService,
        cliente_service: ClienteService,
        user_id: int = 0,
        config_repo=None,
        pai=None,
    ) -> None:
        super().__init__(pai)
        self._ordens = ordem_service
        self._clientes = cliente_service
        self._user_id = user_id
        self._config_repo = config_repo

        layout = QVBoxLayout(self)

        topo = QHBoxLayout()
        titulo = QLabel(t("os_titulo"))
        titulo.setObjectName("tituloModulo")
        topo.addWidget(titulo)
        topo.addStretch(1)
        btn_nova = QPushButton(t("os_nova"))
        btn_nova.clicked.connect(self._nova)
        topo.addWidget(btn_nova)
        layout.addLayout(topo)

        # Cards de dashboard (RF-OS-8).
        self._cards = QHBoxLayout()
        layout.addLayout(self._cards)

        self._tabela = QTableWidget(0, 6)
        self._tabela.setHorizontalHeaderLabels(
            ["ID", "Cliente", t("os_marca"), t("os_modelo"), t("os_problema"), t("os_status")]
        )
        self._tabela.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch
        )
        self._tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._tabela)

        acoes = QHBoxLayout()
        btn_encerrar = QPushButton(t("os_encerrar"))
        btn_encerrar.clicked.connect(self._encerrar)
        btn_garantia = QPushButton("Reabrir (Garantia)")
        btn_garantia.clicked.connect(self._garantia)
        btn_excluir = QPushButton(t("acao_excluir"))
        btn_excluir.clicked.connect(self._excluir)
        btn_pdf_a4 = QPushButton("PDF (A4)")
        btn_pdf_a4.clicked.connect(lambda: self._exportar_pdf("a4"))
        btn_pdf_termica = QPushButton("PDF (80 mm)")
        btn_pdf_termica.clicked.connect(lambda: self._exportar_pdf("termica"))
        acoes.addWidget(btn_encerrar)
        acoes.addWidget(btn_garantia)
        acoes.addWidget(btn_excluir)
        acoes.addWidget(btn_pdf_a4)
        acoes.addWidget(btn_pdf_termica)
        acoes.addStretch(1)
        layout.addLayout(acoes)

        self._recarregar()

    def _recarregar(self) -> None:
        contagem = self._ordens.contar_por_status()

        # Reconstrói cards.
        while self._cards.count():
            item = self._cards.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.addWidget(_card(t("os_abertas"), str(contagem.get(StatusOrdem.EM_REPARO.value, 0))))
        self._cards.addWidget(
            _card(t("status_concluido_sucesso"), str(contagem.get(StatusOrdem.CONCLUIDO_SUCESSO.value, 0)))
        )
        self._cards.addWidget(
            _card(t("status_concluido_sem_solucao"), str(contagem.get(StatusOrdem.CONCLUIDO_SEM_SOLUCAO.value, 0)))
        )
        self._cards.addStretch(1)

        abertas = self._ordens.listar_abertas()
        self._tabela.setRowCount(len(abertas))
        for r, o in enumerate(abertas):
            cliente = self._clientes.por_id(o.cliente_id)
            nome_cliente = cliente.nome if cliente else str(o.cliente_id)
            campos = [
                str(o.id or ""),
                nome_cliente,
                o.marca,
                o.modelo,
                o.problema,
                _rotulo_status(o.status.value),
            ]
            for col, texto in enumerate(campos):
                item = QTableWidgetItem(texto)
                item.setData(Qt.ItemDataRole.UserRole, o.id)
                self._tabela.setItem(r, col, item)

    def _ordem_selecionada(self):
        linha = self._tabela.currentRow()
        if linha < 0:
            return None
        oid = self._tabela.item(linha, 0).data(Qt.ItemDataRole.UserRole)
        return self._ordens.por_id(oid) if oid else None

    def _nova(self) -> None:
        form = OrdemForm(
            self._ordens,
            self._clientes.listar_todos(),
            user_id=self._user_id,
            pai=self,
        )
        form.salvo.connect(lambda _id: self._recarregar())
        form.exec()

    def _encerrar(self) -> None:
        ordem = self._ordem_selecionada()
        if ordem is None:
            QMessageBox.information(self, t("aviso"), "Selecione uma ordem.")
            return
        dlg = EncerramentoDialog(self._ordens, ordem, pai=self)
        dlg.encerrado.connect(lambda _id: self._recarregar())
        dlg.exec()

    def _garantia(self) -> None:
        ordem = self._ordem_selecionada()
        if ordem is None:
            QMessageBox.information(self, t("aviso"), "Selecione uma ordem.")
            return
        try:
            self._ordens.reabrir_garantia(ordem.id or 0)
        except ValidacaoError as e:
            QMessageBox.warning(self, t("aviso"), str(e))
            return
        self._recarregar()

    def _excluir(self) -> None:
        ordem = self._ordem_selecionada()
        if ordem is None:
            QMessageBox.information(self, t("aviso"), "Selecione uma ordem.")
            return
        resp = QMessageBox.question(
            self, t("acao_excluir"), f"Excluir a OS #{ordem.id}?"
        )
        if resp != QMessageBox.StandardButton.Yes:
            return
        self._ordens.excluir(ordem.id or 0)
        self._recarregar()

    def _exportar_pdf(self, formato: str) -> None:
        ordem = self._ordem_selecionada()
        if ordem is None:
            QMessageBox.information(self, t("aviso"), "Selecione uma ordem.")
            return
        cliente = self._clientes.por_id(ordem.cliente_id)
        cfg = self._config_repo.obter_empresa(self._user_id) if self._config_repo else None
        sugerido = f"OS-{ordem.id}-{'A4' if formato == 'a4' else '80mm'}.pdf"
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar PDF", sugerido, "PDF (*.pdf)"
        )
        if not caminho:
            return
        try:
            if formato == "a4":
                gerar_ordem_a4(ordem, cliente, cfg, Path(caminho))
            else:
                gerar_ordem_termica(ordem, cliente, cfg, Path(caminho))
        except Exception as e:  # noqa: BLE001 — falha de I/O não pode derrubar a UI
            QMessageBox.warning(self, t("erro"), f"Falha ao gerar o PDF:\n{e}")
            return
        QMessageBox.information(self, t("ok"), f"Salvo em:\n{caminho}")
