"""Ferramentas ADB: listar aparelhos e diagnosticar — SPEC RF-TOL-* / RF-DIA-*."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ....core.device.adb_gateway import AdbGateway
from ....core.device.gateway import DeviceGateway
from ....core.diag.bateria import parse_dumpsys_bateria
from ....core.pdf import gerar_diagnostico_pdf
from ...i18n import t


class FerramentasView(QWidget):
    """Módulo de ferramentas de bancada (ADB)."""

    def __init__(self, gateway: DeviceGateway | None = None, pai=None) -> None:
        super().__init__(pai)
        self._gateway = gateway or AdbGateway()

        layout = QVBoxLayout(self)

        topo = QHBoxLayout()
        titulo = QLabel(t("ferr_titulo"))
        titulo.setObjectName("tituloModulo")
        topo.addWidget(titulo)
        topo.addStretch(1)
        layout.addLayout(topo)

        # Disponibilidade do adb.
        self._status_adb = QLabel()
        layout.addWidget(self._status_adb)

        # Lista de dispositivos.
        dispositivos = QHBoxLayout()
        self._combo = QComboBox()
        btn_atualizar = QPushButton("Atualizar lista")
        btn_atualizar.clicked.connect(self._atualizar_dispositivos)
        dispositivos.addWidget(self._combo, 1)
        dispositivos.addWidget(btn_atualizar)
        layout.addLayout(dispositivos)

        # Ações de diagnóstico.
        acoes = QHBoxLayout()
        btn_bateria = QPushButton(t("diag_bateria"))
        btn_bateria.clicked.connect(self._diagnosticar_bateria)
        btn_identidade = QPushButton(t("diag_identidade"))
        btn_identidade.clicked.connect(self._diagnosticar_identidade)
        btn_pdf = QPushButton("Exportar diagnóstico em PDF")
        btn_pdf.clicked.connect(self._exportar_pdf)
        acoes.addWidget(btn_bateria)
        acoes.addWidget(btn_identidade)
        acoes.addWidget(btn_pdf)
        acoes.addStretch(1)
        layout.addLayout(acoes)

        # Saída.
        self._saida = QPlainTextEdit()
        self._saida.setReadOnly(True)
        self._saida.setPlaceholderText("A saída do diagnóstico aparece aqui.")
        layout.addWidget(self._saida, 1)

        # Último diagnóstico estruturado (usado pelo exportador de PDF).
        self._ultimo_diag: dict[str, str] = {}

        self._atualizar_dispositivos()

    def _atualizar_dispositivos(self) -> None:
        if not self._gateway.disponivel():
            self._status_adb.setText(
                "⚠ adb não encontrado no PATH. Instale os platform-tools do Android."
            )
            self._combo.clear()
            return
        self._status_adb.setText("✓ adb disponível.")
        self._combo.clear()
        for d in self._gateway.listar_dispositivos():
            self._combo.addItem(f"{d.serial}  ({d.estado})", d.serial)
        if self._combo.count() == 0:
            self._combo.addItem("Nenhum dispositivo conectado", None)

    def _serial(self):
        return self._combo.currentData()

    def _diagnosticar_bateria(self) -> None:
        serial = self._serial()
        if not serial:
            QMessageBox.information(self, t("aviso"), "Conecte um dispositivo.")
            return
        saida = self._gateway.executar_shell("dumpsys battery", serial=serial)
        if not saida.strip():
            QMessageBox.warning(self, t("erro"), "Sem resposta do dispositivo.")
            return
        leitura = parse_dumpsys_bateria(saida)
        texto = (
            f"Nível: {leitura.nivel}%\n"
            f"Temperatura: {leitura.temperatura_c} °C\n"
            f"Voltagem: {leitura.voltagem_mv} mV\n"
            f"Status: {leitura.status}\n"
            f"Saúde: {leitura.saude}"
        )
        self._saida.setPlainText(texto)
        self._ultimo_diag = {
            "Dispositivo": serial,
            "Nível da bateria": f"{leitura.nivel}%" if leitura.nivel is not None else "—",
            "Temperatura": f"{leitura.temperatura_c} °C" if leitura.temperatura_c is not None else "—",
            "Voltagem": f"{leitura.voltagem_mv} mV" if leitura.voltagem_mv is not None else "—",
            "Status": leitura.status or "—",
            "Saúde": leitura.saude or "—",
        }

    def _diagnosticar_identidade(self) -> None:
        serial = self._serial()
        if not serial:
            QMessageBox.information(self, t("aviso"), "Conecte um dispositivo.")
            return
        campos = {
            "Marca": "getprop ro.product.brand",
            "Modelo": "getprop ro.product.model",
            "Android": "getprop ro.build.version.release",
            "SDK": "getprop ro.build.version.sdk",
            "Serial": "getprop ro.serialno",
        }
        linhas = []
        diag: dict[str, str] = {"Dispositivo": serial}
        for rotulo, cmd in campos.items():
            valor = self._gateway.executar_shell(cmd, serial=serial).strip() or "—"
            linhas.append(f"{rotulo}: {valor}")
            diag[rotulo] = valor
        self._saida.setPlainText("\n".join(linhas))
        self._ultimo_diag = diag

    def _exportar_pdf(self) -> None:
        if not self._ultimo_diag:
            QMessageBox.information(
                self, t("aviso"), "Execute um diagnóstico antes de exportar."
            )
            return
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar diagnóstico", "diagnostico.pdf", "PDF (*.pdf)"
        )
        if not caminho:
            return
        gerar_diagnostico_pdf(self._ultimo_diag, caminho)
        QMessageBox.information(self, t("ok"), f"Salvo em:\n{caminho}")
