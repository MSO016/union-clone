from app.translations import (pt, en, es)
import json
from PyQt5.QtCore import (QSettings, QObject, pyqtSignal)
class TranslationManager(QObject):
    language_changed = pyqtSignal()
    _instance = None
    _current_language = None
    _translations = None
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = TranslationManager()
        return cls._instance
    def __init__(self):
        super().__init__()
        if TranslationManager._instance is not None:
            raise Exception('This class is a singleton!')
        TranslationManager._instance = self
        self._load_translations()
        self._load_language_preference()
    def _load_translations(self):
        self._translations = {'pt': pt.translations, 'en': en.translations, 'es': es.translations}
    def _load_language_preference(self):
        settings = QSettings('Union', 'ServiceOrderSystem')
        self._current_language = settings.value('language', 'pt')
    def get_text(self, key):
        '''Get translated text for the given key in current language'''
        try:
            return self._translations[self._current_language][key]
        except KeyError:
            return self._translations['pt'].get(key, key)
    def set_language(self, language_code):
        '''Set the current language (pt, en, or es)'''
        if language_code in self._translations:
            self._current_language = language_code
            settings = QSettings('Union', 'ServiceOrderSystem')
            settings.setValue('language', language_code)
            self.language_changed.emit()
            return True
        return False
    def get_current_language(self):
        '''Get the current language code'''
        return self._current_language
    def get_available_languages(self):
        '''Get list of available language codes'''
        return list(self._translations.keys())
    @property
    def current_language_name(self):
        '''Get the name of the current language in that language'''
        names = {'pt': 'Portugu├¬s', 'en': 'English', 'es': 'Espa├▒ol'}
        return names.get(self._current_language, 'Unknown')
    def clear_cache(self):
        '''Limpa o cache de tradu├º├Áes e for├ºa o recarregamento'''
        self._translations = {}
        self._load_translations()
        self.language_changed.emit()
