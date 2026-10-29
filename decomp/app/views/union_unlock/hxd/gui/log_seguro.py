'''
TECH UNION SOLUTIONS ÔÇö Log Seguro
Widget QTextEdit readonly com filtragem de seguran├ºa para o HXD Partition Editor.
'''
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
    """Substitui offsets hex por '***' para seguran├ºa."""
    return _PADRAO_HEX.sub('***', texto)
def _filtrar_path(texto: str) -> str:
    '''Trunca caminhos longos para ...\\pasta\\arquivo.'''
    def _truncar(match):
        caminho = match.group(0)
        partes = re.split('[\\\\\\/]', caminho)
        partes = [p for p in partes if p]
        if len(partes) > 2:
            return f'...\\{partes[-2]}\\{partes[-1]}'
        return caminho
    return _PADRAO_PATH.sub(_truncar, texto)
def _sanitizar(texto: str) -> str:
    '''Aplica todas as filtragens de seguran├ºa na mensagem.'''
    texto = _filtrar_hex(texto)
    texto = _filtrar_path(texto)
    return texto
class LogSeguro(QTextEdit):
    '''
    Widget de log seguro com filtragem autom├ítica.
    - Readonly
    - Auto-scroll
    - Filtra offsets hex e paths longos
    - Limite de linhas configur├ível
    '''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet(gerar_qss_log())
        self.setAcceptRichText(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._contagem_linhas = 0
    def _timestamp(self) -> str:
        '''Retorna timestamp no formato [HH:MM:SS].'''
        return datetime.now().strftime('[%H:%M:%S]')
    def _adicionar(self, msg: str, cor: str):
        '''Adiciona mensagem formatada ao log com cor especificada.'''
        msg_segura = _sanitizar(msg)
        ts = self._timestamp()
        html = f'<span style="color: #7a8a9a;">{ts}</span> <span style="color: {cor};">{msg_segura}</span><br>'
        self.moveCursor(QTextCursor.End)
        self.insertHtml(html)
        self._contagem_linhas += 1
        self._verificar_limite()
        self._scroll_final()
    def _scroll_final(self):
        '''Rola para o final do log.'''
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    def _verificar_limite(self):
        '''Remove linhas antigas se exceder o limite.'''
        if self._contagem_linhas > _LIMITE_LINHAS:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, self._contagem_linhas - _LIMITE_LINHAS)
            cursor.removeSelectedText()
            self._contagem_linhas = _LIMITE_LINHAS
    def info(self, msg: str):
        '''Adiciona mensagem informativa (branco).'''
        self._adicionar(msg, '#ffffff')
    def sucesso(self, msg: str):
        '''Adiciona mensagem de sucesso (verde).'''
        self._adicionar(msg, '#43a047')
    def erro(self, msg: str):
        '''Adiciona mensagem de erro (vermelho).'''
        self._adicionar(msg, '#e53935')
    def aviso(self, msg: str):
        '''Adiciona mensagem de aviso (amarelo/laranja).'''
        self._adicionar(msg, '#f39c12')
    def separador(self):
        '''Adiciona linha separadora visual.'''
        html = '<span style="color: #3a4a5a;">ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ</span><br>'
        self.moveCursor(QTextCursor.End)
        self.insertHtml(html)
        self._contagem_linhas += 1
        self._verificar_limite()
        self._scroll_final()
    def prop(self, chave: str, valor: str):
        '''Adiciona propriedade chave: valor com cores diferenciadas.
        Chave em branco, valor em cyan claro.'''
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
        '''Limpa todo o conte├║do do log.'''
        self.clear()
        self._contagem_linhas = 0
