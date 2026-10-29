import re
from datetime import datetime
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtGui import QTextCursor, QColor
from PyQt5.QtCore import Qt
from .tema import gerar_qss_log
_LIMITE_LINHAS = 5000
_PADRAO_HEX = re.compile('0x[0-9a-fA-F]{2,}')
_PADRAO_PATH = re.compile('(?:[A-Za-z]:)?(?:[\\\\\\/][^\\\\\\/:*?"<>|]+){3,}[\\\\\\/]?[^\\\\\\/:*?"<>|\\s]*')
def _filtrar_hex(texto: str) -> str:
    return _PADRAO_HEX.sub('***', texto)
def _filtrar_path(texto: str) -> str:
    def _truncar(match):
        caminho = match.group(0)
        partes = re.split('[\\\\\\/]', caminho)
        partes = [p for p in partes if p]
        if len(partes) > 2:
            return f'...\\{partes[-2]}\\{partes[-1]}'
        return caminho
    return _PADRAO_PATH.sub(_truncar, texto)
def _sanitizar(texto: str) -> str:
    texto = _filtrar_hex(texto)
    texto = _filtrar_path(texto)
    return texto
class LogSeguro(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet(gerar_qss_log())
        self.setAcceptRichText(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._contagem_linhas = 0
    def _timestamp(self) -> str:
        return datetime.now().strftime('[%H:%M:%S]')
    def _adicionar(self, msg: str, cor: str):
        msg_segura = _sanitizar(msg)
        ts = self._timestamp()
        html = f'<span style="color: #7a8a9a;">{ts}</span> <span style="color: {cor};">{msg_segura}</span><br>'
        self.moveCursor(QTextCursor.End)
        self.insertHtml(html)
        self._contagem_linhas += 1
        self._verificar_limite()
        self._scroll_final()
    def _scroll_final(self):
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    def _verificar_limite(self):
        if self._contagem_linhas > _LIMITE_LINHAS:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, self._contagem_linhas - _LIMITE_LINHAS)
            cursor.removeSelectedText()
            self._contagem_linhas = _LIMITE_LINHAS
    def info(self, msg: str):
        self._adicionar(msg, '#ffffff')
    def sucesso(self, msg: str):
        self._adicionar(msg, '#43a047')
    def erro(self, msg: str):
        self._adicionar(msg, '#e53935')
    def aviso(self, msg: str):
        self._adicionar(msg, '#f39c12')
    def separador(self):
        html = '<span style="color: #3a4a5a;">ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ</span><br>'
        self.moveCursor(QTextCursor.End)
        self.insertHtml(html)
        self._contagem_linhas += 1
        self._verificar_limite()
        self._scroll_final()
    def prop(self, chave: str, valor: str):
        chave_safe = _sanitizar(str(chave))
        valor_safe = _sanitizar(str(valor))
        ts = self._timestamp()
        html = f'<span style="color: #7a8a9a;">{ts}</span> <span style="color: #ffffff;">{chave_safe}</span><span style="color: #7a8a9a;">:</span> <span style="color: #4fc3f7;">{valor_safe}</span><br>'
        self.moveCursor(QTextCursor.End)
        self.insertHtml(html)
        self._contagem_linhas += 1
        self._verificar_limite()
        self._scroll_final()
    def limpar(self):
        self.clear()
        self._contagem_linhas = 0
