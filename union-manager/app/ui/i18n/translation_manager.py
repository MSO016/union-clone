"""Gerenciador de traduções (i18n) — sem backend, dicionários locais.

Fallback: chave no idioma -> texto em pt_br -> a própria chave (SPEC RF-NF-6).
"""
from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import QObject, pyqtSignal

from .pt_br import STRINGS as PT_BR

# Idiomas suportados. EN/ES começam como espelhos do PT e são enriquecidos.
_IDIOMAS = {
    "pt_br": PT_BR,
}


class TranslationManager(QObject):
    mudou = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._idioma = "pt_br"
        self._strings = dict(PT_BR)

    def definir_idioma(self, idioma: str) -> None:
        self._idioma = idioma
        self._strings = dict(_IDIOMAS.get(idioma, PT_BR))
        self.mudou.emit()

    @property
    def idioma(self) -> str:
        return self._idioma

    def t(self, chave: str) -> str:
        return self._strings.get(chave, PT_BR.get(chave, chave))


# Instância única (padrão usado pela UI).
_manager: TranslationManager | None = None


def get_translation() -> TranslationManager:
    global _manager
    if _manager is None:
        _manager = TranslationManager()
    return _manager


def t(chave: str) -> str:
    return get_translation().t(chave)
