from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
import time
from ...utils.translation_manager import TranslationManager
import re
class SolutionFiltersWidget(QWidget):
    filterChanged = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_filter = None
        self.last_filter_time = 0
        self.translation_manager = TranslationManager.get_instance()
        self.translation_manager.language_changed.connect(self.refresh_interface)
        self.safe_keywords = {'power': ['n├úo liga', 'n├úo inicia', 'desliga', 'loop', 'travado', 'consumo', 'curto'], 'charging': ['n├úo carrega', 'carregamento', 'bateria'], 'display': ['tela', 'display', 'touch', 'imagem'], 'signal': ['sinal', 'rede', 'wifi', 'antena'], 'software': ['software', 'android', 'recovery', 'firmware', 'itunes', 'fastboot', 'modo download', 'dm'], 'security': ['conta', 'google', 'frp', 'senha', 'nv data'], 'camera': ['camera', 'foto', 'flash'], 'audio': ['som', 'audio', 'microfone', 'alto-falante'], 'storage': ['emmc', 'ufs', 'memoria', 'storage', 'armazenamento'], 'hardware': ['cpu', 'processador', 'placa', 'componente', 'chip'], 'boot': ['boot', 'bootloop', 'fastboot', 'download mode', 'recovery'], 'performance': ['lento', 'travando', 'lag', 'performance', 'esquenta'], 'backup': ['backup', 'dados', 'restaura├º├úo', 'sincroniza├º├úo', 'nv data'], 'network': ['rede', '3g', '4g', '5g', 'dados m├│veis', 'wifi', 'baseband', 'imei', 'sinal'], 'system': ['sistema', 'os', 'android', 'ios', 'atualiza├º├úo', 'itunes']}
        self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        main_container = QFrame()
        main_container.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border: 1px solid #e9ecef;\n                border-radius: 8px;\n            }\n        ')
        main_layout = QVBoxLayout(main_container)
        header = QFrame()
        header.setStyleSheet('background: transparent; border: none;')
        header_layout = QVBoxLayout(header)
        title = QLabel(self.translation_manager.get_text('filters_title'))
        title.setStyleSheet('\n            font-size: 14px;\n            font-weight: bold;\n            color: #2c3e50;\n            padding: 5px 0;\n        ')
        description = QLabel(self.translation_manager.get_text('filters_description'))
        description.setWordWrap(True)
        description.setStyleSheet('\n            color: #6c757d;\n            font-size: 12px;\n            padding-bottom: 10px;\n        ')
        header_layout.addWidget(title)
        header_layout.addWidget(description)
        main_layout.addWidget(header)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('\n            QScrollArea {\n                border: none;\n                background: transparent;\n            }\n            QScrollBar:vertical {\n                width: 8px;\n                background: #f8f9fa;\n            }\n            QScrollBar::handle:vertical {\n                background: #c1c9d0;\n                border-radius: 4px;\n            }\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                height: 0px;\n            }\n        ')
        filters_container = QWidget()
        filters_layout = QVBoxLayout(filters_container)
        filters_layout.setSpacing(5)
        problem_categories = {'power': (self.translation_manager.get_text('power_issues'), ['n├úo liga', 'n├úo inicia', 'desliga', 'loop', 'travado', 'consumo', 'curto']), 'charging': (self.translation_manager.get_text('charging_issues'), ['n├úo carrega', 'carregamento', 'bateria']), 'display': (self.translation_manager.get_text('display_issues'), ['tela', 'display', 'touch', 'imagem']), 'signal': (self.translation_manager.get_text('signal_issues'), ['sinal', 'rede', 'wifi', 'antena']), 'software': (self.translation_manager.get_text('software_issues'), ['software', 'android', 'recovery', 'firmware', 'itunes', 'fastboot', 'modo download', 'dm']), 'security': (self.translation_manager.get_text('security_issues'), ['conta', 'google', 'frp', 'senha', 'nv data']), 'camera': (self.translation_manager.get_text('camera_issues'), ['camera', 'foto', 'flash']), 'audio': (self.translation_manager.get_text('audio_issues'), ['som', 'audio', 'microfone', 'alto-falante']), 'storage': (self.translation_manager.get_text('storage_issues'), ['emmc', 'ufs', 'memoria', 'storage', 'armazenamento']), 'hardware': (self.translation_manager.get_text('hardware_issues'), ['cpu', 'processador', 'placa', 'componente', 'chip']), 'boot': (self.translation_manager.get_text('boot_issues'), ['boot', 'bootloop', 'fastboot', 'download mode', 'recovery']), 'performance': (self.translation_manager.get_text('performance_issues'), ['lento', 'travando', 'lag', 'performance', 'esquenta']), 'backup': (self.translation_manager.get_text('backup_issues'), ['backup', 'dados', 'restaura├º├úo', 'sincroniza├º├úo', 'nv data']), 'network': (self.translation_manager.get_text('network_issues'), ['rede', '3g', '4g', '5g', 'dados m├│veis', 'wifi', 'baseband', 'imei', 'sinal']), 'system': (self.translation_manager.get_text('system_issues'), ['sistema', 'os', 'android', 'ios', 'atualiza├º├úo', 'itunes'])}
        for key, (label, keywords) in problem_categories.items():
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty('filter_key', key)
            btn.setProperty('keywords', keywords)
            try:
                kws_filtro = self.safe_keywords.get(key, [])
                if kws_filtro:
                    btn.setToolTip('Filtra solucoes contendo: ' + ', '.join(kws_filtro))
                else:
                    btn.setToolTip('Filtro de ' + str(label))
            except Exception:
                pass
            btn.setStyleSheet('\n                QPushButton {\n                    background-color: white;\n                    border: 1px solid #dee2e6;\n                    border-radius: 4px;\n                    padding: 8px 12px;\n                    text-align: left;\n                    font-size: 13px;\n                    color: #495057;\n                }\n                QPushButton:hover {\n                    background-color: #e9ecef;\n                    border-color: #dee2e6;\n                }\n                QPushButton:checked {\n                    background-color: #2196F3;\n                    color: white;\n                    border-color: #1976D2;\n                }\n                QPushButton:checked:hover {\n                    background-color: #1976D2;\n                }\n            ')
            btn.clicked.connect(self.on_filter_clicked)
            filters_layout.addWidget(btn)
        scroll.setWidget(filters_container)
        main_layout.addWidget(scroll)
        btn_clear = QPushButton(self.translation_manager.get_text('clear_filters'))
        btn_clear.setStyleSheet('\n            QPushButton {\n                background-color: transparent;\n                border: 1px solid #dc3545;\n                color: #dc3545;\n                padding: 5px 10px;\n                border-radius: 4px;\n                font-size: 12px;\n            }\n            QPushButton:hover {\n                background-color: #dc3545;\n                color: white;\n            }\n        ')
        btn_clear.clicked.connect(self.clear_filters)
        main_layout.addWidget(btn_clear)
        layout.addWidget(main_container)
    def _sanitizar_keyword(self, keyword):
        '''Sanitiza keyword removendo caracteres perigosos'''
        if not keyword or not isinstance(keyword, str):
            return ''
        keyword_limpo = re.sub('[<>"\\\';\\\\%_]', '', keyword.strip())
        if len(keyword_limpo) > 50:
            keyword_limpo = keyword_limpo[:50]
        return keyword_limpo.lower()
    def _construir_filtro_seguro(self, categoria):
        '''Constr├│i filtro usando apenas keywords predefinidas'''
        if categoria not in self.safe_keywords:
            return
        keywords_seguros = self.safe_keywords[categoria]
        conditions = []
        for keyword in keywords_seguros:
            keyword_sanitizado = self._sanitizar_keyword(keyword)
            if keyword_sanitizado:
                conditions.append(keyword_sanitizado)
        return ','.join(conditions)
    def on_filter_clicked(self):
        current_time = time.time()
        if current_time - self.last_filter_time < 0.5:
            return
        self.last_filter_time = current_time
        btn = self.sender()
        categoria = btn.property('filter_key') or 'unknown'
        for child in self.findChildren(QPushButton):
            if child == btn:
                continue
            if child.isCheckable():
                child.setChecked(False)
        if not btn.isChecked():
            self.current_filter = None
            self.filterChanged.emit('')
            return
        try:
            filter_condition = self._construir_filtro_seguro(categoria)
            if filter_condition:
                self.current_filter = filter_condition
                self.filterChanged.emit(filter_condition)
                return
            self.current_filter = None
            self.filterChanged.emit('')
            return
        except Exception:
            self.current_filter = None
            self.filterChanged.emit('')
    def clear_filters(self):
        '''Limpa todos os filtros ativos'''
        current_time = time.time()
        if current_time - self.last_filter_time < 0.5:
            return
        self.last_filter_time = current_time
        self.current_filter = None
        for btn in self.findChildren(QPushButton):
            if btn.isCheckable():
                btn.setChecked(False)
        self.filterChanged.emit('')
    def refresh_interface(self):
        '''Atualiza a interface com o novo idioma'''
        for label in self.findChildren(QLabel):
            if 'font-weight: bold' in label.styleSheet():
                label.setText(self.translation_manager.get_text('filters_title'))
            elif 'color: #6c757d' in label.styleSheet():
                label.setText(self.translation_manager.get_text('filters_description'))
        problem_categories = {'power': self.translation_manager.get_text('power_issues'), 'charging': self.translation_manager.get_text('charging_issues'), 'display': self.translation_manager.get_text('display_issues'), 'signal': self.translation_manager.get_text('signal_issues'), 'software': self.translation_manager.get_text('software_issues'), 'security': self.translation_manager.get_text('security_issues'), 'camera': self.translation_manager.get_text('camera_issues'), 'audio': self.translation_manager.get_text('audio_issues'), 'storage': self.translation_manager.get_text('storage_issues'), 'hardware': self.translation_manager.get_text('hardware_issues'), 'boot': self.translation_manager.get_text('boot_issues'), 'performance': self.translation_manager.get_text('performance_issues'), 'backup': self.translation_manager.get_text('backup_issues'), 'network': self.translation_manager.get_text('network_issues'), 'system': self.translation_manager.get_text('system_issues')}
        for btn in self.findChildren(QPushButton):
            if btn.property('filter_key'):
                key = btn.property('filter_key')
                if key in problem_categories:
                    btn.setText(problem_categories[key])
            elif 'Limpar Filtros' in btn.text() or 'Clear Filters' in btn.text() or 'Limpiar Filtros' in btn.text():
                btn.setText(self.translation_manager.get_text('clear_filters'))
