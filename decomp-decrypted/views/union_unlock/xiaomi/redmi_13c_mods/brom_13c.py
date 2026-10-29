import os
from PyQt5.QtWidgets import QCheckBox, QMessageBox
from PyQt5.QtGui import QFont
from ..brom_base import BromBaseWidget, CoresUnion
class Brom13CWidget(BromBaseWidget):
    MODELO = 'Redmi 13C'
    VARIANTE = 'Variantes sem DAA (MT6768/MT6769)'
    ANDROID = 'Android 15 | HyperOS 2'
    LOADER = 'Redmi_13C.bin'
    INSTRUCAO = '1. Conecte o aparelho desligado\n2. Assim que aparecer o logo, segure o bot├úo Power\n   por 4 segundos'
    def setup_ui(self):
        super().setup_ui()
        try:
            self.chk_mdm = QCheckBox('MDM/PAYJ')
            self.chk_mdm.setFont(QFont('Segoe UI', 9))
            self.chk_mdm.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
            layout = self.btn_parar.parentWidget().layout()
            idx = layout.indexOf(self.btn_parar)
            layout.insertWidget(idx + 1, self.chk_mdm)
            return
        except Exception:
            self.chk_mdm = None
    def remove_frp(self):
        try:
            mdm_aviso = '\n\nÔÜá´©Å Alguns MDMs n├úo s├úo suportados.' if self.chk_mdm and self.chk_mdm.isChecked() else ''
        except Exception:
            mdm_aviso = ''
        if self.em_execucao:
            return
        mtk_path = os.path.join(self._get_tools_path(), 'mtk.exe')
        loader_path = self._get_loader_path()
        if not os.path.exists(mtk_path):
            QMessageBox.critical(self, 'Erro', 'Componente n├úo encontrado!\n\nReinstale o programa ou entre em contato com o suporte.')
            return
        if loader_path is not None and not os.path.exists(loader_path):
            QMessageBox.critical(self, 'Erro', 'Componente n├úo encontrado!\n\nReinstale o programa ou entre em contato com o suporte.')
            return
        reply = QMessageBox.question(self, 'Confirmar', f'Iniciar remo├º├úo de FRP do {self.MODELO}?\n\nInstru├º├Áes:\n{self.INSTRUCAO}{mdm_aviso}', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.em_execucao = True
        self.label_status.setText('Aguardando dispositivo...')
        self.label_phone_status.setText('Conecte o celular em modo BROM')
        self._start_spinner()
        self.barra_progresso.setValue(5)
        from ..brom_base import BromWorker
        self.worker = BromWorker(mtk_path, loader_path, self.MODELO)
        self.worker.progress_signal.connect(self.barra_progresso.setValue)
        self.worker.status_signal.connect(self._on_status)
        self.worker.finished_signal.connect(self._on_finished)
        self.btn_frp.setEnabled(False)
        self.worker.start()
