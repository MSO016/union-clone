"""Base de Conhecimento: busca, cadastro e detalhes — SPEC RF-KB-*."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ....core.db.repos.conhecimento_repo import ConhecimentoRepository
from ....core.models.models import Conhecimento, OrigemConhecimento, TipoDispositivo
from ...i18n import t


class ConhecimentoForm(QDialog):
    """Diálogo de cadastro manual de solução."""

    def __init__(
        self,
        repo: ConhecimentoRepository,
        entrada: Optional[Conhecimento] = None,
        user_id: int = 0,
        pai=None,
    ) -> None:
        super().__init__(pai)
        self._repo = repo
        self._entrada = entrada
        self._user_id = user_id
        self.setWindowTitle(t("acao_editar") if entrada else t("kb_nova"))
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._tipo = QComboBox()
        for td in TipoDispositivo:
            self._tipo.addItem(td.value, td.value)
        self._marca = QLineEdit()
        self._modelo = QLineEdit()
        self._problema = QPlainTextEdit()
        self._problema.setMaximumHeight(70)
        self._solucao = QPlainTextEdit()
        self._solucao.setMaximumHeight(70)
        self._passos = QPlainTextEdit()
        self._passos.setMaximumHeight(70)

        form.addRow("Tipo*", self._tipo)
        form.addRow(t("os_marca") + "*", self._marca)
        form.addRow(t("os_modelo") + "*", self._modelo)
        form.addRow(t("kb_problema") + "*", self._problema)
        form.addRow(t("kb_solucao") + "*", self._solucao)
        form.addRow("Passos", self._passos)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        botoes.button(QDialogButtonBox.StandardButton.Save).setText(t("acao_salvar"))
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText(t("acao_cancelar"))
        botoes.accepted.connect(self._ao_salvar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

        if entrada is not None:
            idx = self._tipo.findData(entrada.tipo_dispositivo.value)
            if idx >= 0:
                self._tipo.setCurrentIndex(idx)
            self._marca.setText(entrada.marca)
            self._modelo.setText(entrada.modelo)
            self._problema.setPlainText(entrada.problema)
            self._solucao.setPlainText(entrada.solucao)
            self._passos.setPlainText(entrada.passos)

    def _ao_salvar(self) -> None:
        if not self._marca.text().strip() or not self._modelo.text().strip():
            QMessageBox.warning(self, t("aviso"), "Informe marca e modelo.")
            return
        if not self._problema.toPlainText().strip() or not self._solucao.toPlainText().strip():
            QMessageBox.warning(self, t("aviso"), "Informe problema e solução.")
            return

        if self._entrada is not None:
            k = self._entrada
            k.tipo_dispositivo = TipoDispositivo(self._tipo.currentData())
            k.marca = self._marca.text().strip()
            k.modelo = self._modelo.text().strip()
            k.problema = self._problema.toPlainText().strip()
            k.solucao = self._solucao.toPlainText().strip()
            k.passos = self._passos.toPlainText().strip()
            self._repo.atualizar(k)
        else:
            k = Conhecimento(
                user_id=self._user_id,
                tipo_dispositivo=TipoDispositivo(self._tipo.currentData()),
                marca=self._marca.text().strip(),
                modelo=self._modelo.text().strip(),
                problema=self._problema.toPlainText().strip(),
                solucao=self._solucao.toPlainText().strip(),
                passos=self._passos.toPlainText().strip(),
                origem=OrigemConhecimento.MANUAL,
            )
            self._repo.criar(k)
        self.accept()


class ConhecimentoView(QWidget):
    """Módulo da base de conhecimento (auto-aprendizado + manual)."""

    def __init__(self, repo: ConhecimentoRepository, user_id: int = 0, pai=None) -> None:
        super().__init__(pai)
        self._repo = repo
        self._user_id = user_id

        layout = QVBoxLayout(self)

        topo = QHBoxLayout()
        titulo = QLabel(t("kb_titulo"))
        titulo.setObjectName("tituloModulo")
        topo.addWidget(titulo)
        topo.addStretch(1)
        btn_novo = QPushButton(t("kb_nova"))
        btn_novo.clicked.connect(self._novo)
        topo.addWidget(btn_novo)
        layout.addLayout(topo)

        filtros = QHBoxLayout()
        self._busca = QLineEdit()
        self._busca.setPlaceholderText(t("acao_buscar") + " (marca, modelo, problema)…")
        self._busca.textChanged.connect(self._recarregar)
        self._tipo = QComboBox()
        self._tipo.addItem("Todos os tipos", None)
        for td in TipoDispositivo:
            self._tipo.addItem(td.value, td.value)
        self._tipo.currentIndexChanged.connect(self._recarregar)
        filtros.addWidget(self._busca, 1)
        filtros.addWidget(self._tipo)
        layout.addLayout(filtros)

        self._tabela = QTableWidget(0, 6)
        self._tabela.setHorizontalHeaderLabels(
            [
                "ID",
                "Tipo",
                t("os_marca"),
                t("os_modelo"),
                t("kb_problema"),
                "Origem",
            ]
        )
        self._tabela.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch
        )
        self._tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tabela.itemDoubleClicked.connect(self._detalhes)
        layout.addWidget(self._tabela)

        acoes = QHBoxLayout()
        btn_detalhes = QPushButton("Ver solução")
        btn_detalhes.clicked.connect(self._detalhes)
        btn_editar = QPushButton(t("acao_editar"))
        btn_editar.clicked.connect(self._editar)
        btn_excluir = QPushButton(t("acao_excluir"))
        btn_excluir.clicked.connect(self._excluir)
        acoes.addWidget(btn_detalhes)
        acoes.addWidget(btn_editar)
        acoes.addWidget(btn_excluir)
        acoes.addStretch(1)
        layout.addLayout(acoes)

        self._recarregar()

    def _recarregar(self) -> None:
        tipo = self._tipo.currentData()
        td = TipoDispositivo(tipo) if tipo else None
        entradas = self._repo.buscar(self._busca.text(), tipo_dispositivo=td)
        self._tabela.setRowCount(len(entradas))
        for r, k in enumerate(entradas):
            origem = "Ordem #" + str(k.ordem_origem_id) if k.origem == OrigemConhecimento.OS_ENCERRADA else "Manual"
            campos = [
                str(k.id or ""),
                k.tipo_dispositivo.value,
                k.marca,
                k.modelo,
                k.problema,
                origem,
            ]
            for col, texto in enumerate(campos):
                item = QTableWidgetItem(texto)
                item.setData(Qt.ItemDataRole.UserRole, k.id)
                self._tabela.setItem(r, col, item)

    def _selecionado(self) -> Optional[Conhecimento]:
        linha = self._tabela.currentRow()
        if linha < 0:
            return None
        kid = self._tabela.item(linha, 0).data(Qt.ItemDataRole.UserRole)
        return self._repo.por_id(kid) if kid else None

    def _novo(self) -> None:
        ConhecimentoForm(self._repo, user_id=self._user_id, pai=self).exec()
        self._recarregar()

    def _editar(self) -> None:
        k = self._selecionado()
        if k is None:
            QMessageBox.information(self, t("aviso"), "Selecione uma solução.")
            return
        ConhecimentoForm(self._repo, entrada=k, user_id=self._user_id, pai=self).exec()
        self._recarregar()

    def _detalhes(self) -> None:
        k = self._selecionado()
        if k is None:
            QMessageBox.information(self, t("aviso"), "Selecione uma solução.")
            return
        texto = (
            f"{k.tipo_dispositivo.value} — {k.marca} {k.modelo}\n\n"
            f"{t('kb_problema')}:\n{k.problema}\n\n"
            f"{t('kb_solucao')}:\n{k.solucao}\n\n"
            f"Passos:\n{k.passos or '—'}"
        )
        QMessageBox.information(self, f"{t('kb_titulo')} #{k.id}", texto)

    def _excluir(self) -> None:
        k = self._selecionado()
        if k is None:
            QMessageBox.information(self, t("aviso"), "Selecione uma solução.")
            return
        resp = QMessageBox.question(
            self, t("acao_excluir"), f"Excluir a solução #{k.id} ({k.marca} {k.modelo})?"
        )
        if resp == QMessageBox.StandardButton.Yes:
            self._repo.excluir(k.id or 0)
            self._recarregar()
