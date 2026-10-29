'''Card de marca/categoria do dashboard principal.
Componente coeso e reutilizavel. Mantem a logica de acesso desacoplada:
o consumidor define o `estado` ("acessivel", "locked_premium", "locked") e
escuta os sinais.
Sinais publicos:
    solucoes_requested(str): emitido quando o usuario clica em "Ver solucoes"
    upgrade_requested():     emitido quando o usuario clica em "Upgrade"
Reversao: este widget e usado apenas quando UI_DASHBOARD_NEW_CARDS=1.
Quando 0, `main_window` segue usando `_criar_card_marca_legado`.
'''
from __future__ import annotations
import os
from typing import Optional
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import (QPixmap, QPainter, QColor)
from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget)
_NOMES_AMIGAVEIS = {'SAMSUNG': 'Samsung', 'APPLE': 'Apple', 'MOTOROLA': 'Motorola', 'XIAOMI': 'Xiaomi', 'REALME': 'Realme', 'OPPO': 'Oppo', 'VIVO': 'Vivo', 'HUAWEI': 'Huawei', 'INFINIX': 'Infinix', 'TECNO': 'Tecno'}
_DESCRICOES_CATEGORIA = {'ANDROID\nCOMANDOS': 'Comandos e atalhos para Android', 'SOFTWARE': 'Softwares, firmwares e ferramentas', 'CPU': 'Informacoes e suporte de CPUs', 'ESTUDO': 'Estudos e materiais tecnicos', 'JUMPER DE TELAS': 'Jumpers e correcoes de display', 'EMMC UFS': 'Memorias eMMC e UFS', 'ESQUEMAS ELETRICO': 'Esquemas eletricos por modelo', 'TEST POINTS': 'Test points e pontos de teste', 'DESBLOQUEIO': 'Desbloqueios e bypass'}
_CATEGORIA_I18N_KEY = {'ANDROID\nCOMANDOS': 'card_desc_android_cmd', 'SOFTWARE': 'card_desc_software', 'CPU': 'card_desc_cpu', 'ESTUDO': 'card_desc_estudo', 'JUMPER DE TELAS': 'card_desc_jumper', 'EMMC UFS': 'card_desc_emmc', 'ESQUEMAS ELETRICO': 'card_desc_esquemas', 'TEST POINTS': 'card_desc_testpoints', 'DESBLOQUEIO': 'card_desc_desbloqueio'}
def _safe_get_text(tm, key, default):
    '''Resolve uma chave no TranslationManager com fallback robusto.
    Aceita TM=None ou objetos sem `get_text` sem quebrar (retorna default).
    '''
    if tm is None:
        return default
    try:
        getter = getattr(tm, 'get_text', None)
        if not callable(getter):
            return default
        valor = getter(key)
        if isinstance(valor, str) and valor and valor != key:
            return valor
        return default
    except Exception:
        return default
def gerar_descricao(marca: str, translation_manager=None) -> str:
    '''Retorna descricao padrao para o card.
Ordem de resolucao:
1. Se marca eh categoria tecnica E ha TM com a chave i18n -> usa TM
2. Se marca eh categoria tecnica -> texto fixo de _DESCRICOES_CATEGORIA
3. Se marca eh conhecida -> "Solucoes e estudos para dispositivos X"
   (templete via TM com chave `card_desc_brand_template` se disponivel)
4. Fallback generico
'''
    if marca in _CATEGORIA_I18N_KEY:
        chave = _CATEGORIA_I18N_KEY[marca]
        default = _DESCRICOES_CATEGORIA[marca]
        return _safe_get_text(translation_manager, chave, default)
    nome = _NOMES_AMIGAVEIS.get(marca)
    if nome:
        default = f'Solucoes e estudos para dispositivos {nome}'
        if translation_manager is not None:
            template = _safe_get_text(translation_manager, 'card_desc_brand_template', 'Solucoes e estudos para dispositivos {nome}')
            try:
                return template.format(nome=nome)
            except Exception:
                return default
        return default
    nome_fmt = marca.replace('\n', ' ').title() if marca else 'este item'
    default = f'Solucoes e estudos para {nome_fmt}'
    if translation_manager is not None:
        template = _safe_get_text(translation_manager, 'card_desc_generic_template', 'Solucoes e estudos para {nome}')
        try:
            return template.format(nome=nome_fmt)
        except Exception:
            return default
def nome_exibicao(marca: str) -> str:
    '''Retorna o nome amigavel de exibicao (capitalizado em pt-BR).'''
    if marca in _NOMES_AMIGAVEIS:
        return _NOMES_AMIGAVEIS[marca]
    return marca.replace('\n', ' ').title()
def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Converte '#RRGGBB' em 'rgba(R, G, B, A)' para uso em QSS."""
    try:
        h = hex_color.lstrip('#')
        if len(h) == 3:
            h = ''.join((ch * 2 for ch in h))
        if len(h) != 6:
            return f'rgba(100, 116, 139, {alpha})'
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        a = max(0.0, min(1.0, float(alpha)))
        return f'rgba({r}, {g}, {b}, {a})'
    except Exception:
        return f'rgba(100, 116, 139, {alpha})'
class BrandCardWidget(QFrame):
    '''Card horizontal de marca/categoria do dashboard.
Layout:
    [ICONE]  TITULO              [BADGE opcional]
             descricao curta
    [-----  BOTAO (largura cheia)  -----]
Estados aceitos:
    - "acessivel"        botao "Ver solucoes" pastel da marca
    - "locked_premium"   badge "Premium" + botao "Upgrade" pastel ambar
    - "locked"           opacidade reduzida + label informativo
'''
    solucoes_requested = pyqtSignal(str)
    upgrade_requested = pyqtSignal()
    _ESTADOS_VALIDOS = ('acessivel', 'locked_premium', 'locked')
    def __init__(self, marca: str, cor_marca: str, icon_path: str, descricao: Optional[str]=None, nome_exibir: Optional[str]=None, estado: str='acessivel', texto_botao_solucoes: str='Ver solucoes', texto_botao_upgrade: str='Ô¡É Fazer Upgrade', translation_manager=None, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        if estado not in self._ESTADOS_VALIDOS:
            estado = 'acessivel'
        self._marca = marca
        self._cor_marca = cor_marca or '#64748b'
        self._icon_path = icon_path
        self._tm = translation_manager
        self._descricao_fixa = descricao is not None
        self._descricao = descricao if self._descricao_fixa else gerar_descricao(marca, translation_manager)
        self._nome_exibir = nome_exibir or nome_exibicao(marca)
        self._estado = estado
        self._texto_solucoes_default = texto_botao_solucoes
        self._texto_upgrade_default = texto_botao_upgrade
        self._texto_solucoes = _safe_get_text(translation_manager, 'see_solutions', texto_botao_solucoes)
        self._texto_upgrade = _safe_get_text(translation_manager, 'card_btn_upgrade', texto_botao_upgrade)
        self._title_label = None
        self._desc_label = None
        self._badge_label = None
        self._info_label = None
        self._action_btn = None
        self._build_ui()
    @property
    def estado(self) -> str:
        return self._estado
    @property
    def marca(self) -> str:
        return self._marca
    def _build_ui(self) -> None:
        self.setObjectName('brandCard')
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(152)
        self.setMinimumWidth(240)
        self.setMaximumWidth(320)
        self._aplicar_qss_card()
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)
        topo = QHBoxLayout()
        topo.setSpacing(12)
        topo.setContentsMargins(0, 0, 0, 0)
        topo.addWidget(self._build_icone(), 0, Qt.AlignTop)
        textos = QVBoxLayout()
        textos.setSpacing(2)
        textos.setContentsMargins(0, 0, 0, 0)
        titulo_box = QHBoxLayout()
        titulo_box.setContentsMargins(0, 0, 0, 0)
        titulo_box.setSpacing(6)
        self._title_label = QLabel(self._nome_exibir)
        self._title_label.setObjectName('brandCardTitle')
        self._title_label.setStyleSheet('QLabel#brandCardTitle{  color:#1e293b;  font-size:15px;  font-weight:700;  background:transparent;  border:none;}')
        self._title_label.setWordWrap(True)
        self._title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        titulo_box.addWidget(self._title_label, 1)
        if self._estado == 'locked_premium':
            badge_text = _safe_get_text(self._tm, 'card_premium_badge', '­ƒöÆ Premium')
            badge = QLabel(badge_text)
            badge.setObjectName('brandCardBadge')
            badge.setStyleSheet('QLabel#brandCardBadge{  color:#b45309;  background:rgba(245,158,11,0.18);  padding:2px 7px;  border-radius:8px;  font-size:9px;  font-weight:700;}')
            badge.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
            titulo_box.addWidget(badge, 0, Qt.AlignRight | Qt.AlignTop)
            self._badge_label = badge
        textos.addLayout(titulo_box)
        self._desc_label = QLabel(self._descricao)
        self._desc_label.setObjectName('brandCardDesc')
        self._desc_label.setStyleSheet('QLabel#brandCardDesc{  color:#64748b;  font-size:12px;  background:transparent;  border:none;}')
        self._desc_label.setWordWrap(True)
        self._desc_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        textos.addWidget(self._desc_label)
        textos.addStretch(1)
        topo.addLayout(textos, 1)
        root.addLayout(topo)
        self._action_btn = self._build_action_button()
        if self._action_btn is not None:
            root.addWidget(self._action_btn)
            return
        info_text = _safe_get_text(self._tm, 'card_locked_info', '­ƒöÆ Disponivel apenas para usuarios autorizados')
        info = QLabel(info_text)
        info.setStyleSheet('color:#64748b;font-size:10px;background:rgba(100,116,139,0.10);border-radius:6px;padding:6px 8px;')
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        root.addWidget(info)
        self._info_label = info
    def _build_icone(self) -> QWidget:
        wrap = QFrame()
        wrap.setObjectName('brandCardIconWrap')
        wrap.setFixedSize(84, 84)
        wrap.setStyleSheet('QFrame#brandCardIconWrap{  background:#f1f5f9;  border-radius:14px;  border:1px solid rgba(100,116,139,0.10);}')
        v = QVBoxLayout(wrap)
        v.setContentsMargins(6, 6, 6, 6)
        v.setSpacing(0)
        v.setAlignment(Qt.AlignCenter)
        lbl = QLabel()
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setFixedSize(72, 72)
        try:
            if self._icon_path and os.path.exists(self._icon_path):
                pix = QPixmap(self._icon_path)
                if self._estado != 'acessivel':
                    pix = self._aplicar_opacidade(pix)
                lbl.setPixmap(pix.scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception:
            pass
        v.addWidget(lbl)
        return wrap
    def _build_action_button(self) -> Optional[QPushButton]:
        if self._estado == 'acessivel':
            base = self._cor_marca
            bg = _hex_to_rgba(base, 0.14)
            bg_hover = _hex_to_rgba(base, 0.22)
            bg_pressed = _hex_to_rgba(base, 0.3)
            border = _hex_to_rgba(base, 0.3)
            btn = QPushButton(self._texto_solucoes)
            btn.setObjectName('brandCardActionBtn')
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(32)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setStyleSheet(f'QPushButton#brandCardActionBtn{{  background:{bg};  color:{base};  border:1px solid {border};  border-radius:8px;  padding:6px 12px;  font-size:12px;  font-weight:600;}}QPushButton#brandCardActionBtn:hover{{  background:{bg_hover};}}QPushButton#brandCardActionBtn:pressed{{  background:{bg_pressed};}}')
            btn.clicked.connect((lambda: self.solucoes_requested.emit(self._marca)))
            return btn
        if self._estado == 'locked_premium':
            btn = QPushButton(self._texto_upgrade)
            btn.setObjectName('brandCardUpgradeBtn')
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(32)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setStyleSheet('QPushButton#brandCardUpgradeBtn{  background:rgba(245,158,11,0.18);  color:#b45309;  border:1px solid rgba(245,158,11,0.40);  border-radius:8px;  padding:6px 12px;  font-size:12px;  font-weight:700;}QPushButton#brandCardUpgradeBtn:hover{  background:rgba(245,158,11,0.28);}QPushButton#brandCardUpgradeBtn:pressed{  background:rgba(245,158,11,0.36);}')
            btn.clicked.connect(self.upgrade_requested.emit)
            return btn
    def _aplicar_qss_card(self) -> None:
        if self._estado == 'locked':
            self.setStyleSheet('QFrame#brandCard{  background:#f8fafc;  border:1px solid rgba(100,116,139,0.18);  border-radius:12px;}')
            return
        if self._estado == 'locked_premium':
            self.setStyleSheet('QFrame#brandCard{  background:#fffbeb;  border:1px solid rgba(245,158,11,0.35);  border-radius:12px;}QFrame#brandCard:hover{  background:#fff8e1;  border:1px solid rgba(245,158,11,0.55);  border-bottom:2.5px solid rgba(245,158,11,0.30);}')
            return
        self.setStyleSheet('QFrame#brandCard{  background:#ffffff;  border:1px solid rgba(15,23,42,0.08);  border-radius:12px;}QFrame#brandCard:hover{  background:rgba(33,150,243,0.03);  border:1px solid rgba(15,23,42,0.18);  border-bottom:2.5px solid rgba(13,71,161,0.18);}')
    def set_translation_manager(self, translation_manager) -> None:
        '''Atualiza o TM associado e re-aplica os textos.
        Util quando o card ja foi construido sem TM e a aplicacao
        depois descobriu o singleton (ex.: testes integrados).
        '''
        self._tm = translation_manager
        self.refresh_translations()
    def refresh_translations(self) -> None:
        '''Reaplica os textos traduzidos sem recriar o widget.
        Chamado pelo dono (MainWindow) ao receber `language_changed`.
        Comportamento defensivo: se algum filho ja foi destruido por
        algum motivo, ignora silenciosamente esse trecho.
        '''
        try:
            if not self._descricao_fixa and self._desc_label is not None:
                nova_desc = gerar_descricao(self._marca, self._tm)
                self._descricao = nova_desc
                self._desc_label.setText(nova_desc)
        except Exception:
            pass
        try:
            if self._badge_label is not None:
                self._badge_label.setText(_safe_get_text(self._tm, 'card_premium_badge', '­ƒöÆ Premium'))
        except Exception:
            pass
        try:
            if self._info_label is not None:
                self._info_label.setText(_safe_get_text(self._tm, 'card_locked_info', '­ƒöÆ Disponivel apenas para usuarios autorizados'))
        except Exception:
            pass
        try:
            if self._action_btn is not None:
                if self._estado == 'acessivel':
                    self._texto_solucoes = _safe_get_text(self._tm, 'see_solutions', self._texto_solucoes_default)
                    self._action_btn.setText(self._texto_solucoes)
                    return
                if self._estado == 'locked_premium':
                    self._texto_upgrade = _safe_get_text(self._tm, 'card_btn_upgrade', self._texto_upgrade_default)
                    self._action_btn.setText(self._texto_upgrade)
                    return
                return
        except Exception:
            pass
    @staticmethod
    def _aplicar_opacidade(pix: QPixmap) -> QPixmap:
        '''Retorna uma copia do pixmap com 60% de opacidade (estado bloqueado).'''
        try:
            if pix is None or pix.isNull():
                return pix
            out = QPixmap(pix.size())
            out.fill(Qt.transparent)
            painter = QPainter(out)
            painter.setOpacity(0.6)
            painter.drawPixmap(0, 0, pix)
            painter.end()
            return out
        except Exception:
            return pix
