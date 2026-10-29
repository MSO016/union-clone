import os
import sys
import logging
import subprocess
from PyQt5.QtCore import (Qt, QThread, pyqtSignal)
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton)
from app.utils import _upd_core
logger = logging.getLogger(__name__)
def lancar(caminho: str) -> bool:
    try:
        if sys.platform != 'win32':
            return False
        if not os.path.isfile(caminho):
            return False
        subprocess.Popen([caminho, '/NORESTART'], close_fds=True)
        return True
    except Exception as exc:
        logger.error('upd: falha ao iniciar (%s)', type(exc).__name__)
        return False
class _Worker(QThread):
    progresso = pyqtSignal(int, str)
    concluido = pyqtSignal(bool, str)
    def run(self):
        try:
            def _cb(pct, msg):
                try:
                    self.progresso.emit(int(pct), str(msg))
                    return
                except Exception:
                    return
            caminho = _upd_core.preparar_atualizacao(progress_callback=_cb)
            self.concluido.emit(bool(caminho), caminho or '')
            return
        except Exception as exc:
            logger.error('upd: worker falhou (%s)', type(exc).__name__)
            self.concluido.emit(False, '')
class _UpdDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sucesso = False
        self.caminho_instalador = ''
        self._cancelado = False
        self._worker = None
        self._setup_ui()
        self._iniciar()
    def _setup_ui(self):
        self.setWindowTitle('Atualizacao Automatica')
        self.setModal(True)
        self.setFixedWidth(440)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        titulo = QLabel('Baixando atualizacao')
        titulo.setStyleSheet('font-size:16px; font-weight:bold; color:#0D47A1;')
        layout.addWidget(titulo)
        self.lbl_status = QLabel('Preparando...')
        self.lbl_status.setStyleSheet('color:#607D8B; font-size:12px;')
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        layout.addWidget(self.progress)
        self.lbl_aviso = QLabel('Mantenha o programa aberto ate o download terminar.')
        self.lbl_aviso.setStyleSheet('color:#90A4AE; font-size:11px;')
        self.lbl_aviso.setWordWrap(True)
        layout.addWidget(self.lbl_aviso)
        linha = QHBoxLayout()
        linha.addStretch()
        self.btn_cancelar = QPushButton('Cancelar')
        self.btn_cancelar.clicked.connect(self._cancelar)
        linha.addWidget(self.btn_cancelar)
        layout.addLayout(linha)
    def _iniciar(self):
        self._worker = _Worker()
        self._worker.progresso.connect(self._on_progresso)
        self._worker.concluido.connect(self._on_concluido)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()
    def _on_progresso(self, pct, msg):
        if self._cancelado:
            return
        self.progress.setValue(max(0, min(100, int(pct))))
        if msg:
            self.lbl_status.setText(msg)
    def _on_concluido(self, ok, caminho):
        if self._cancelado:
            return
        self.sucesso = bool(ok)
        self.caminho_instalador = caminho or ''
        if self.sucesso:
            self.progress.setValue(100)
            self.lbl_status.setText('Download concluido com sucesso.')
            self.accept()
            return
        self.reject()
    def _cancelar(self):
        self._cancelado = True
        self.sucesso = False
        self.btn_cancelar.setEnabled(False)
        self.lbl_status.setText('Cancelando...')
        self.reject()
    def closeEvent(self, event):
        try:
            if self._worker is not None and self._worker.isRunning():
                self._cancelado = True
                self._worker.wait(100)
        except Exception:
            pass
        super().closeEvent(event)
