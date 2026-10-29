"""Formulário de cliente (criar/editar) — SPEC RF-CLI-1.

Valida via `ClienteService`; emite `salvo(id)` após gravar com sucesso.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
)

from ....core.models.models import Cliente, TipoCliente
from ....core.services.cliente_service import ClienteService
from ....core.services.ordem_service import ValidacaoError
from ...i18n import t


class ClienteForm(QDialog):
    salvo = pyqtSignal(int)

    def __init__(
        self,
        service: ClienteService,
        cliente: Optional[Cliente] = None,
        user_id: int = 0,
        pai=None,
    ) -> None:
        super().__init__(pai)
        self._service = service
        self._editando = cliente is not None
        self._cliente = cliente
        self._user_id = user_id
        self.setWindowTitle(
            t("acao_editar") if self._editando else t("cliente_novo")
        )
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._nome = QLineEdit()
        self._telefone = QLineEdit()
        self._email = QLineEdit()
        self._tipo = QComboBox()
        self._tipo.addItem("Pessoa Física", TipoCliente.PESSOA_FISICA.value)
        self._tipo.addItem("Lojista", TipoCliente.LOJISTA.value)
        self._rua = QLineEdit()
        self._numero = QLineEdit()
        self._bairro = QLineEdit()
        self._cidade = QLineEdit()
        self._observacoes = QTextEdit()
        self._observacoes.setMaximumHeight(90)

        form.addRow(t("cliente_nome") + "*", self._nome)
        form.addRow(t("cliente_telefone") + "*", self._telefone)
        form.addRow(t("cliente_email"), self._email)
        form.addRow(t("cliente_tipo"), self._tipo)
        form.addRow("Rua", self._rua)
        form.addRow("Número", self._numero)
        form.addRow("Bairro", self._bairro)
        form.addRow("Cidade", self._cidade)
        form.addRow("Observações", self._observacoes)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        botoes.button(QDialogButtonBox.StandardButton.Save).setText(t("acao_salvar"))
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText(t("acao_cancelar"))
        botoes.accepted.connect(self._ao_salvar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

        if self._editando and cliente is not None:
            self._preencher(cliente)

    def _preencher(self, c: Cliente) -> None:
        self._nome.setText(c.nome)
        self._telefone.setText(c.telefone)
        self._email.setText(c.email)
        idx = self._tipo.findData(c.tipo.value)
        if idx >= 0:
            self._tipo.setCurrentIndex(idx)
        self._rua.setText(c.rua)
        self._numero.setText(c.numero)
        self._bairro.setText(c.bairro)
        self._cidade.setText(c.cidade)
        self._observacoes.setPlainText(c.observacoes)

    def _coletar(self) -> Cliente:
        return Cliente(
            id=self._cliente.id if self._editando else None,
            user_id=self._user_id,
            nome=self._nome.text(),
            telefone=self._telefone.text(),
            email=self._email.text(),
            rua=self._rua.text(),
            numero=self._numero.text(),
            bairro=self._bairro.text(),
            cidade=self._cidade.text(),
            tipo=TipoCliente(self._tipo.currentData()),
            observacoes=self._observacoes.toPlainText(),
        )

    def _ao_salvar(self) -> None:
        cliente = self._coletar()
        try:
            if self._editando:
                self._service.editar(cliente)
                novo_id = cliente.id or 0
            else:
                novo_id = self._service.criar(
                    nome=cliente.nome,
                    telefone=cliente.telefone,
                    email=cliente.email,
                    rua=cliente.rua,
                    numero=cliente.numero,
                    bairro=cliente.bairro,
                    cidade=cliente.cidade,
                    tipo=cliente.tipo,
                    observacoes=cliente.observacoes,
                    user_id=self._user_id,
                )
        except ValidacaoError as e:
            QMessageBox.warning(self, t("aviso"), str(e))
            return
        self.salvo.emit(novo_id)
        self.accept()
