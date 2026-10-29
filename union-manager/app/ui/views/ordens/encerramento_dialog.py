"""Diálogo de encerramento de OS — SPEC RF-OS-4.

Regras: sucesso exige solução; todos exigem passos; sem solução exige motivo.
"""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)

from ....core.models.models import OrdemServico, StatusOrdem
from ....core.services.ordem_service import OrdemServicoService, ValidacaoError
from ...i18n import t


class EncerramentoDialog(QDialog):
    encerrado = pyqtSignal(int)  # id da OS

    def __init__(self, service: OrdemServicoService, ordem: OrdemServico, pai=None) -> None:
        super().__init__(pai)
        self._service = service
        self._ordem = ordem
        self.setWindowTitle(t("os_encerrar"))
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._status = QComboBox()
        self._status.addItem(
            t("status_concluido_sucesso"), StatusOrdem.CONCLUIDO_SUCESSO.value
        )
        self._status.addItem(
            t("status_concluido_sem_solucao"), StatusOrdem.CONCLUIDO_SEM_SOLUCAO.value
        )
        self._solucao = QPlainTextEdit()
        self._solucao.setMaximumHeight(80)
        self._passos = QPlainTextEdit()
        self._passos.setMaximumHeight(80)
        self._motivo = QPlainTextEdit()
        self._motivo.setMaximumHeight(60)
        self._valor_final = QDoubleSpinBox()
        self._valor_final.setRange(0, 1_000_000)
        self._valor_final.setPrefix("R$ ")

        form.addRow(t("os_status"), self._status)
        form.addRow(t("kb_solucao"), self._solucao)
        form.addRow("Passos realizados*", self._passos)
        form.addRow("Motivo da falha", self._motivo)
        form.addRow("Valor final", self._valor_final)

        self._status.currentIndexChanged.connect(self._ajustar_campos)
        self._ajustar_campos()

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        botoes.button(QDialogButtonBox.StandardButton.Save).setText(t("acao_salvar"))
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText(t("acao_cancelar"))
        botoes.accepted.connect(self._ao_salvar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def _sucesso(self) -> bool:
        return self._status.currentData() == StatusOrdem.CONCLUIDO_SUCESSO.value

    def _ajustar_campos(self) -> None:
        # Sucesso: solução obrigatória, motivo oculto. Sem solução: motivo obrigatório.
        self._solucao.setEnabled(self._sucesso())
        self._motivo.setVisible(not self._sucesso())

    def _ao_salvar(self) -> None:
        status_final = StatusOrdem(self._status.currentData())
        vf = self._valor_final.value() if self._valor_final.value() > 0 else None
        try:
            self._service.encerrar(
                self._ordem.id or 0,
                status_final=status_final,
                solucao=self._solucao.toPlainText(),
                passos=self._passos.toPlainText(),
                motivo_falha=self._motivo.toPlainText(),
                valor_final=vf,
            )
        except ValidacaoError as e:
            QMessageBox.warning(self, t("aviso"), str(e))
            return
        self.encerrado.emit(self._ordem.id or 0)
        self.accept()
