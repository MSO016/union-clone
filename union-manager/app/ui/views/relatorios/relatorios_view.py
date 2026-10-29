"""Relatórios diário e mensal — SPEC RF-REP-1 / RF-REP-2."""
from __future__ import annotations

from datetime import date

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ....core.services.relatorio_service import RelatorioService
from ...i18n import t


def _card(rotulo: str, valor: str) -> QFrame:
    frame = QFrame()
    frame.setObjectName("cardOS")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(16, 12, 16, 12)
    num = QLabel(valor)
    num.setObjectName("tituloModulo")
    lay.addWidget(num)
    lay.addWidget(QLabel(rotulo))
    return frame


class RelatoriosView(QWidget):
    """Módulo de relatórios: resumo do dia e do mês."""

    def __init__(self, service: RelatorioService, pai=None) -> None:
        super().__init__(pai)
        self._service = service

        layout = QVBoxLayout(self)

        titulo = QLabel(t("menu_relatarios"))
        titulo.setObjectName("tituloModulo")
        layout.addWidget(titulo)

        # --- diário (RF-REP-1) --------------------------------------------
        bloco_diario = QHBoxLayout()
        rotulo = QLabel(t("rel_diario"))
        rotulo.setObjectName("tituloModulo")
        self._data = QDateEdit(QDate.currentDate())
        self._data.setCalendarPopup(True)
        btn = QPushButton("Gerar")
        btn.clicked.connect(self._gerar_diario)
        bloco_diario.addWidget(rotulo)
        bloco_diario.addWidget(self._data)
        bloco_diario.addWidget(btn)
        bloco_diario.addStretch(1)
        layout.addLayout(bloco_diario)

        self._cards_diario = QGridLayout()
        layout.addLayout(self._cards_diario)

        # --- mensal (RF-REP-2) --------------------------------------------
        bloco_mensal = QHBoxLayout()
        rotulo_m = QLabel(t("rel_mensal"))
        rotulo_m.setObjectName("tituloModulo")
        self._ano = QComboBox()
        anoAtual = date.today().year
        self._ano.addItems([str(a) for a in range(anoAtual - 3, anoAtual + 1)])
        self._ano.setCurrentText(str(anoAtual))
        self._mes = QComboBox()
        nomes = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
        ]
        for i, nome in enumerate(nomes, start=1):
            self._mes.addItem(nome, i)
        self._mes.setCurrentIndex(date.today().month - 1)
        btn_m = QPushButton("Gerar")
        btn_m.clicked.connect(self._gerar_mensal)
        bloco_mensal.addWidget(rotulo_m)
        bloco_mensal.addWidget(self._mes)
        bloco_mensal.addWidget(self._ano)
        bloco_mensal.addWidget(btn_m)
        bloco_mensal.addStretch(1)
        layout.addLayout(bloco_mensal)

        self._cards_mensal = QGridLayout()
        layout.addLayout(self._cards_mensal)

        layout.addStretch(1)

    def _limpar(self, grid: QGridLayout) -> None:
        while grid.count():
            item = grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _gerar_diario(self) -> None:
        qd = self._data.date()
        r = self._service.resumo_diario(date(qd.year(), qd.month(), qd.day()))
        self._limpar(self._cards_diario)
        valores = [
            (t("os_abertas"), str(r.abertas)),
            (t("status_concluido_sucesso"), str(r.concluidas_sucesso)),
            (t("status_concluido_sem_solucao"), str(r.concluidas_sem_solucao)),
            (t("rel_faturamento"), f"R$ {r.faturamento:,.2f}"),
        ]
        for col, (rot, val) in enumerate(valores):
            self._cards_diario.addWidget(_card(rot, val), 0, col)

    def _gerar_mensal(self) -> None:
        r = self._service.resumo_mensal(int(self._ano.currentText()), self._mes.currentData())
        self._limpar(self._cards_mensal)
        valores = [
            ("Total de OS", str(r.total)),
            (t("status_concluido_sucesso"), str(r.concluidas_sucesso)),
            (t("status_concluido_sem_solucao"), str(r.concluidas_sem_solucao)),
            (t("os_abertas"), str(r.em_reparo)),
            ("Taxa de sucesso", f"{r.taxa_sucesso:.0f}%"),
            (t("rel_faturamento"), f"R$ {r.faturamento:,.2f}"),
        ]
        for col, (rot, val) in enumerate(valores):
            self._cards_mensal.addWidget(_card(rot, val), 0, col)
