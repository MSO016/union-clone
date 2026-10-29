"""Pacote i18n — expõe a API pública."""
from .translation_manager import TranslationManager, get_translation, t

__all__ = ["TranslationManager", "get_translation", "t"]
