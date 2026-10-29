"""Formulário de nova Ordem de Serviço — SPEC RF-OS-2."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)

from ....core.models.models import Cliente, TipoDispositivo
from ....core.services.ordem_service import OrdemServicoService, ValidacaoError
from ...i18n import t


class OrdemForm(QDialog):
    """Diálogo de criação de OS. Emite `salvo(id)`."""

    salvo = pyqtSignal(int)

    def __init__(
        self,
        service: OrdemServicoService,
        clientes: list[Cliente],
        user_id: int = 0,
        cliente_preselecionado: Optional[int] = None,
        pai=None,
    ) -> None:
        super().__init__(pai)
        self._service = service
        self._user_id = user_id
        self.setWindowTitle(t("os_nova"))
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._cliente = QComboBox()
        for c in clientes:
            self._cliente.addItem(f"{c.nome} — {c.telefone}", c.id)
        if cliente_preselecionado is not None:
            idx = self._cliente.findData(cliente_preselecionado)
            if idx >= 0:
                self._cliente.setCurrentIndex(idx)

        self._tipo = QComboBox()
        for td in TipoDispositivo:
            self._tipo.addItem(td.value, td.value)

        self._marca = QLineEdit()
        self._modelo = QLineEdit()
        self._serie = QLineEdit()
        self._valor = QDoubleSpinBox()
        self._valor.setRange(0, 1_000_000)
        self._valor.setPrefix("R$ ")
        self._problema = QPlainTextEdit()
        self._problema.setMaximumHeight(80)
        self._diagnostico = QPlainTextEdit()
        self._diagnostico.setMaximumHeight(80)

        form.addRow("Cliente*", self._cliente)
        form.addRow("Tipo*", self._tipo)
        form.addRow(t("os_marca") + "*", self._marca)
        form.addRow(t("os_modelo") + "*", self._modelo)
        form.addRow("Série", self._serie)
        form.addRow("Valor", self._valor)
        form.addRow(t("os_problema") + "*", self._problema)
        form.addRow("Diagnóstico inicial", self._diagnostico)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        botoes.button(QDialogButtonBox.StandardButton.Save).setText(t("acao_salvar"))
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText(t("acao_cancelar"))
        botoes.accepted.connect(self._ao_salvar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def _ao_salvar(self) -> None:
        if self._cliente.count() == 0:
            QMessageBox.warning(self, t("aviso"), "Cadastre um cliente antes.")
            return
        cliente_id = self._cliente.currentData()
        valor = self._valor.value() if self._valor.value() > 0 else None
        try:
            novo_id = self._service.criar(
                cliente_id=cliente_id,
                tipo_dispositivo=TipoDispositivo(self._tipo.currentData()),
                marca=self._marca.text(),
                modelo=self._modelo.text(),
                problema=self._problema.toPlainText(),
                serie=self._serie.text(),
                valor=valor,
                diagnostico=self._diagnostico.toPlainText(),
                user_id=self._user_id,
            )
        except ValidacaoError as e:
            QMessageBox.warning(self, t("aviso"), str(e))
            return
        self.salvo.emit(novo_id)
        self.accept()
