from datetime import datetime
from typing import (Any, Dict, List, Optional)
from PyQt5.QtCore import (Qt, QTimer, QSettings, pyqtSignal)
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QLabel, QWidget, QSizePolicy, QPushButton, QDialog, QApplication)
ALERTA_REAGENDA_MAX = 12
ALERTA_REAGENDA_MS = 3000
HEADER_CARDS_CONFIG: Dict[str, Any] = {'card_min_width_xs': 110, 'card_min_width_sm': 125, 'card_min_width_md': 140, 'card_min_width_lg': 155, 'card_min_width_xl': 170, 'license_card_extra': 0.25, 'font_main_xs': 10, 'font_sub_xs': 9, 'font_main_sm': 11, 'font_sub_sm': 9, 'font_main_md': 12, 'font_sub_md': 10, 'font_main_lg': 13, 'font_sub_lg': 10, 'font_main_xl': 13, 'font_sub_xl': 11, 'card_padding_xs': '4px 8px', 'card_padding_sm': '5px 10px', 'card_padding_md': '6px 12px', 'card_padding_lg': '7px 12px', 'card_padding_xl': '8px 14px', 'card_border_radius': 8, 'color_lifetime': {'bg': '#1B5E20', 'border': '#43A047', 'text': '#FFFFFF', 'subtext': 'rgba(255,255,255,0.85)', 'icon': '', 'label': 'Licen├ºa Ativa'}, 'color_calmo': {'bg': '#2E7D32', 'border': '#66BB6A', 'text': '#FFFFFF', 'subtext': 'rgba(255,255,255,0.85)', 'icon': '', 'label': '{N} dias'}, 'color_info': {'bg': '#1565C0', 'border': '#42A5F5', 'text': '#FFFFFF', 'subtext': 'rgba(255,255,255,0.85)', 'icon': '', 'label': '{N} dias'}, 'color_atencao': {'bg': '#E64A19', 'border': '#FF7043', 'text': '#FFFFFF', 'subtext': 'rgba(255,255,255,0.92)', 'icon': '', 'label': '{N} dias'}, 'color_alerta': {'bg': '#C62828', 'border': '#E53935', 'text': '#FFFFFF', 'subtext': 'rgba(255,255,255,0.90)', 'icon': '', 'label': '{N} dias'}, 'color_hoje': {'bg': '#B71C1C', 'border': '#FFCDD2', 'text': '#FFFFFF', 'subtext': 'rgba(255,255,255,0.90)', 'icon': '', 'label': '├Ültima hoje'}, 'color_expirada': {'bg': '#37474F', 'border': '#E53935', 'text': '#FFFFFF', 'subtext': 'rgba(255,255,255,0.85)', 'icon': '', 'label': 'Reativar'}, 'color_user': {'bg': 'rgba(255,255,255,0.10)', 'border': 'rgba(255,255,255,0.18)', 'text': '#FFFFFF', 'subtext': 'rgba(255,255,255,0.72)'}, 'color_plan_premium': {'bg': 'rgba(255,193,7,0.18)', 'border': 'rgba(255,193,7,0.55)', 'text': '#FFE082', 'subtext': 'rgba(255,236,179,0.85)'}, 'color_plan_admin': {'bg': 'rgba(76,175,80,0.18)', 'border': 'rgba(76,175,80,0.55)', 'text': '#A5D6A7', 'subtext': 'rgba(200,230,201,0.85)'}, 'color_plan_normal': {'bg': 'rgba(255,255,255,0.10)', 'border': 'rgba(255,255,255,0.22)', 'text': '#FFFFFF', 'subtext': 'rgba(255,255,255,0.78)'}, 'refresh_interval_ms': 1800000, 'boot_check_delay_ms': 5000}
ALERTA_RULES: List[Dict[str, Any]] = [{'min_dias': 31, 'max_dias': 99999, 'max_per_day': 0, 'min_hours': 0, 'tom': 'calmo'}, {'min_dias': 16, 'max_dias': 30, 'max_per_day': 0, 'min_hours': 0, 'tom': 'info'}, {'min_dias': 8, 'max_dias': 15, 'max_per_day': 1, 'min_hours': 0, 'tom': 'novidade'}, {'min_dias': 4, 'max_dias': 7, 'max_per_day': 2, 'min_hours': 6, 'tom': 'continuidade'}, {'min_dias': 1, 'max_dias': 3, 'max_per_day': 2, 'min_hours': 4, 'tom': 'urgencia'}, {'min_dias': 0, 'max_dias': 0, 'max_per_day': 3, 'min_hours': 3, 'tom': 'ultima'}]
ALERTA_RULE_EXPIRADA = {'max_per_day': 1, 'min_hours': 12, 'tom': 'reativacao'}
ALERTA_COPY: Dict[str, Dict[str, str]] = {'novidade': {'titulo': 'Novidades chegando no TECH UNION SOLUTIONS', 'subtitulo': 'Os pr├│ximos lan├ºamentos do ecossistema j├í est├úo sendo preparados.', 'cta': 'Quero continuar recebendo'}, 'continuidade': {'titulo': 'N├úo perca as pr├│ximas atualiza├º├Áes do ecossistema', 'subtitulo': 'Estamos preparando novos m├│dulos e modelos para voc├¬.', 'cta': 'Garantir minha continuidade'}, 'urgencia': {'titulo': 'Garanta sua continuidade no ecossistema TECH UNION', 'subtitulo': 'Para seguir recebendo as novidades sem nenhuma interrup├º├úo.', 'cta': 'Falar com a equipe'}, 'ultima': {'titulo': '├Ültima oportunidade do ciclo atual', 'subtitulo': 'Aproveite hoje para manter o acesso ├ás pr├│ximas funcionalidades.', 'cta': 'Falar com a equipe agora'}, 'reativacao': {'titulo': 'Bem-vindo de volta ao ecossistema TECH UNION', 'subtitulo': 'Reative e continue de onde parou ÔÇö com tudo o que foi lan├ºado.', 'cta': 'Quero reativar'}}
ALERTA_COPY_COMUM: Dict[str, Dict[str, str]] = {'novidade': {'titulo': 'Sua licen├ºa do TECH UNION est├í pr├│xima do vencimento', 'subtitulo': 'Renove antecipadamente e aproveite o upgrade para o PLANO PREMIUM com valor promocional.', 'cta': 'Quero meu upgrade Premium'}, 'continuidade': {'titulo': 'Renova├º├úo antecipada com upgrade Premium dispon├¡vel', 'subtitulo': 'Fa├ºa a renova├º├úo agora e troque para o PLANO PREMIUM por valor promocional.', 'cta': 'Quero meu upgrade Premium'}, 'urgencia': {'titulo': '├Ültima semana ÔÇö upgrade Premium com condi├º├úo especial', 'subtitulo': 'Renovando agora voc├¬ garante mais 1 ano completo + upgrade promocional para Premium.', 'cta': 'Garantir upgrade Premium'}, 'ultima': {'titulo': 'Hoje ├® o ├║ltimo dia para o upgrade promocional', 'subtitulo': 'Fa├ºa hoje a renova├º├úo + upgrade para Premium e garanta o valor especial.', 'cta': 'Falar com a equipe agora'}, 'reativacao': {'titulo': 'Volte ao ecossistema com upgrade direto para Premium', 'subtitulo': 'Reative sua conta com upgrade promocional para o Plano Premium ÔÇö incluindo Union OS Manager.', 'cta': 'Quero reativar com Premium'}}
ALERTA_BENEFICIOS: List[str] = ['Novos modelos e solu├º├Áes publicadas toda semana', 'Atualiza├º├Áes dos m├│dulos MTK, FRP, EDL e OS', 'Acesso a ferramentas exclusivas em desenvolvimento', 'Suporte ao sistema e corre├º├Áes via WhatsApp']
ALERTA_BENEFICIOS_PREMIUM: List[str] = ['Union OS Manager ÔÇö sistema completo de OS e gest├úo de A.T.', 'Aba de Jumper na tela do TECH UNION', '+Modelos nas bases autom├íticas para FRP', 'Atualiza├º├Áes e recursos premium cont├¡nuos']
DESCONTO_INFO: Dict[str, Any] = {'percentual': 20, 'label': 'Renova├º├úo antecipada', 'linha_principal': 'Renove antes do fim do ciclo e a equipe libera at├® {P}% de desconto.', 'linha_calmo': 'Sem pressa: voc├¬ ainda tem tempo. Quanto antes renovar, maior o desconto dispon├¡vel (at├® {P}%).'}
PLANOS_INFO: Dict[str, Any] = {'plano_normal_label': 'Plano 1 (renova├º├úo comum)', 'plano_normal_preco': 147, 'plano_premium_label': 'Plano Premium (valor cheio)', 'plano_premium_preco': 247, 'plano_oferta_label': 'Sua oferta antecipada ÔÇö Plano Premium', 'plano_oferta_preco': 100, 'moeda': 'R$', 'obs_validade': 'Oferta v├ílida apenas antes do t├®rmino do ciclo atual.', 'promo_validade_ate': '2026-07-15'}
def _bucket_para_largura(largura_tela: int) -> str:
    if largura_tela <= 1280:
        return 'xs'
    if largura_tela <= 1366:
        return 'sm'
    if largura_tela <= 1600:
        return 'md'
    if largura_tela <= 1920:
        return 'lg'
    return 'xl'
def _resolver_estilo_licenca(dias_restantes: str) -> Dict[str, str]:
    cfg = HEADER_CARDS_CONFIG
    if dias_restantes == 'Ôê×':
        return cfg['color_lifetime']
    if dias_restantes == 'EXPIRADA':
        return cfg['color_expirada']
    if dias_restantes == 'HOJE':
        return cfg['color_hoje']
    try:
        n = int(dias_restantes)
    except (TypeError, ValueError):
        return cfg['color_lifetime']
    if n > 30:
        return cfg['color_calmo']
    if n > 15:
        return cfg['color_info']
    if n > 7:
        return cfg['color_atencao']
    return cfg['color_alerta']
def _resolver_regra_alerta(dias_restantes: str) -> Dict[str, Any]:
    if dias_restantes == 'EXPIRADA':
        return ALERTA_RULE_EXPIRADA
    if dias_restantes == 'Ôê×':
        return {'max_per_day': 0, 'min_hours': 0, 'tom': 'calmo'}
    try:
        n = int(dias_restantes) if dias_restantes != 'HOJE' else 0
    except (TypeError, ValueError):
        return {'max_per_day': 0, 'min_hours': 0, 'tom': 'calmo'}
    for regra in ALERTA_RULES:
        if regra['min_dias'] <= n:
            if n <= regra['max_dias']:
                return regra
    return {'max_per_day': 0, 'min_hours': 0, 'tom': 'calmo'}
class StatusCard(QFrame):
    clicked = pyqtSignal(str)
    def __init__(self, kind: str, parent: Optional[QWidget]=None):
        super().__init__(parent)
        self.kind = kind
        self.setObjectName(f'statusCard_{kind}')
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFrameShape(QFrame.NoFrame)
        self._main_label = QLabel('', self)
        self._main_label.setAlignment(Qt.AlignCenter)
        self._sub_label = QLabel('', self)
        self._sub_label.setAlignment(Qt.AlignCenter)
        self._sub_label.hide()
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(1)
        v.addWidget(self._main_label)
        v.addWidget(self._sub_label)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self.kind)
        super().mousePressEvent(e)
    def aplicar_estilo(self, bucket: str, estilo: Dict[str, str], width_min: int):
        cfg = HEADER_CARDS_CONFIG
        font_main = cfg[f'font_main_{bucket}']
        font_sub = cfg[f'font_sub_{bucket}']
        padding = cfg[f'card_padding_{bucket}']
        radius = cfg['card_border_radius']
        bg = estilo.get('bg', 'rgba(255,255,255,0.10)')
        border = estilo.get('border', 'rgba(255,255,255,0.20)')
        text = estilo.get('text', '#FFFFFF')
        subtext = estilo.get('subtext', 'rgba(255,255,255,0.72)')
        self.setStyleSheet(f'\n            QFrame#{self.objectName()} {{\n                background: {bg};\n                border: 1px solid {border};\n                border-radius: {radius}px;\n                padding: {padding};\n            }}\n            QFrame#{self.objectName()}:hover {{\n                background: rgba(255, 255, 255, 0.18);\n                border: 1.5px solid rgba(255, 255, 255, 0.85);\n                border-bottom: 2.5px solid rgba(255, 255, 255, 0.45);\n            }}\n            QFrame#{self.objectName()}:pressed {{\n                background: rgba(0, 0, 0, 0.12);\n                border: 1.5px solid rgba(255, 255, 255, 0.50);\n            }}\n        ')
        self._main_label.setStyleSheet(f'color: {text}; font-size: {font_main}px; font-weight: 700; background: transparent; border: none;')
        self._sub_label.setStyleSheet(f'color: {subtext}; font-size: {font_sub}px; font-weight: 500; background: transparent; border: none;')
        self.setMinimumWidth(width_min)
    def setar_textos(self, principal: str, subtitulo: str=''):
        self._main_label.setText(principal)
        if subtitulo:
            self._sub_label.setText(subtitulo)
            self._sub_label.show()
            return
        self._sub_label.hide()
class AlertaRenovacaoManager:
    KEY_LAST = 'alerta/last_renovacao_shown'
    KEY_COUNT = 'alerta/count_today'
    KEY_DATE = 'alerta/last_count_date'
    def __init__(self):
        self._settings = QSettings('TechUnion', 'UNION')
        self._reset_se_dia_mudou()
    def _reset_se_dia_mudou(self):
        hoje = datetime.now().strftime('%Y-%m-%d')
        ultimo_dia = self._settings.value(self.KEY_DATE, '')
        if str(ultimo_dia) != hoje:
            self._settings.setValue(self.KEY_DATE, hoje)
            self._settings.setValue(self.KEY_COUNT, 0)
    def deve_mostrar_agora(self, regra: Dict[str, Any]) -> bool:
        try:
            self._reset_se_dia_mudou()
            max_per_day = int(regra.get('max_per_day', 0) or 0)
            if max_per_day <= 0:
                return False
            count = int(self._settings.value(self.KEY_COUNT, 0) or 0)
            if count >= max_per_day:
                return False
            min_hours = float(regra.get('min_hours', 0) or 0)
            if min_hours > 0:
                last_iso = self._settings.value(self.KEY_LAST, '')
                if last_iso:
                    try:
                        try:
                            last_dt = datetime.fromisoformat(str(last_iso))
                            delta_h = (datetime.now() - last_dt).total_seconds() / 3600.0
                            if delta_h < min_hours:
                                return False
                        except Exception:
                            return True
                    except Exception:
                        return False
                    return True
        except Exception:
            return False
        return True
    def registrar_exibicao(self):
        try:
            self._reset_se_dia_mudou()
            count = int(self._settings.value(self.KEY_COUNT, 0) or 0)
            self._settings.setValue(self.KEY_COUNT, count + 1)
            self._settings.setValue(self.KEY_LAST, datetime.now().isoformat())
            return
        except Exception as e:
            print(f'[AlertaRenovacaoManager] registrar_exibicao: {e}')
class AlertaRenovacaoDialog(QDialog):
    def __init__(self, dias_restantes, data_expiracao, tom, on_falar_equipe, parent=None, is_premium=False):
        super().__init__(parent)
        self.setObjectName('alertDialog')
        self.setWindowTitle('TECH UNION SOLUTIONS')
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setStyleSheet('\n            QDialog#alertDialog {\n                background: #1A1F2C;\n                border: 1px solid #2A3142;\n            }\n            QWidget#alertContent { background: #1A1F2C; }\n            QLabel#alertTitle    { color: #82B1FF; font-size: 16px; font-weight: 800;\n                                   background: transparent; border: none; }\n            QLabel#alertSub      { color: #B0BEC5; font-size: 12px; font-weight: 500;\n                                   background: transparent; border: none; }\n            QLabel#alertSection  { color: #ECEFF1; font-size: 12px; font-weight: 700;\n                                   background: transparent; border: none;\n                                   padding-top: 4px; }\n            QLabel#alertBenef    { color: #ECEFF1; font-size: 12px; font-weight: 500;\n                                   background: transparent; border: none; }\n            QLabel#alertBenefPremium { color: #FFE082; font-size: 12px; font-weight: 600;\n                                       background: transparent; border: none; }\n            QLabel#alertHigh     { color: #82B1FF; font-size: 12px; font-weight: 600;\n                                   background: transparent; border: none; }\n            QLabel#alertContact  { color: #78909C; font-size: 11px;\n                                   background: transparent; border: none; }\n            QFrame#alertDescBox {\n                background: rgba(255, 193, 7, 0.10);\n                border: 1px solid rgba(255, 193, 7, 0.45);\n                border-radius: 6px;\n            }\n            QLabel#alertDescTitle { color: #FFD54F; font-size: 12px; font-weight: 800;\n                                    background: transparent; border: none; }\n            QLabel#alertDescBody  { color: #FFE082; font-size: 12px; font-weight: 500;\n                                    background: transparent; border: none; }\n            QFrame#alertPremiumBox {\n                background: rgba(255, 193, 7, 0.06);\n                border: 1px solid rgba(255, 193, 7, 0.30);\n                border-radius: 6px;\n            }\n            QLabel#alertPriceTitle  { color: #FFD54F; font-size: 13px; font-weight: 800;\n                                      background: transparent; border: none; }\n            QLabel#alertPriceLine   { color: #ECEFF1; font-size: 12px; font-weight: 500;\n                                      background: transparent; border: none; }\n            QLabel#alertPriceCheap  { color: #B0BEC5; font-size: 12px; font-weight: 500;\n                                      background: transparent; border: none;\n                                      text-decoration: line-through; }\n            /* V0.9/V1.0: caixa do preco-oferta ÔÇö destaque MAXIMO (fonte grande, padding largo) */\n            QLabel#alertPriceHot    { color: #69F0AE; font-size: 26px; font-weight: 900;\n                                      background: rgba(76, 175, 80, 0.16);\n                                      border: 2px solid rgba(76, 175, 80, 0.55);\n                                      border-radius: 8px;\n                                      padding: 14px 18px;\n                                      letter-spacing: 1px; }\n            QLabel#alertPriceEcon   { color: #69F0AE; font-size: 11px; font-weight: 600;\n                                      background: transparent; border: none; }\n            /* V0.9: caixa azul "O que continua chegando" + warning de validade */\n            QFrame#alertContinuaBox {\n                background: rgba(33, 150, 243, 0.08);\n                border: 1px solid rgba(33, 150, 243, 0.35);\n                border-radius: 6px;\n            }\n            QLabel#alertContinuaTitle { color: #82B1FF; font-size: 12px; font-weight: 800;\n                                        background: transparent; border: none; }\n            QFrame#alertWarningBox {\n                background: rgba(255, 152, 0, 0.10);\n                border: 1px solid rgba(255, 152, 0, 0.45);\n                border-radius: 6px;\n            }\n            QLabel#alertWarning     { color: #FFB74D; font-size: 11px; font-weight: 600;\n                                      background: transparent; border: none; }\n            QPushButton#alertCTA {\n                background: #25D366; color: white; padding: 10px 18px;\n                border-radius: 6px; font-weight: 700; font-size: 13px; border: none;\n            }\n            QPushButton#alertCTA:hover    { background: #1FAE52; }\n            QPushButton#alertCTA:pressed  { background: #178A40; }\n            QPushButton#alertLater {\n                background: transparent; color: #B0BEC5; padding: 10px 18px;\n                border-radius: 6px; font-size: 12px; border: 1px solid #455A64;\n                font-weight: 500;\n            }\n            QPushButton#alertLater:hover  { background: rgba(255,255,255,0.06);\n                                            color: #ECEFF1; border-color: #78909C; }\n            QLabel#alertCountdown {\n                color: #FF8A65; font-size: 18px; font-weight: 900;\n                background: rgba(255, 87, 34, 0.12);\n                border: 2px solid rgba(255, 87, 34, 0.50);\n                border-radius: 8px;\n                padding: 10px 14px;\n                letter-spacing: 1px;\n            }\n            QLabel#alertCountdownSub {\n                color: #FFAB91; font-size: 12px; font-weight: 600;\n                background: transparent; border: none;\n                padding-top: 2px;\n            }\n        ')
        copy_dict = ALERTA_COPY if is_premium else ALERTA_COPY_COMUM
        copy = copy_dict.get(tom, copy_dict['novidade'])
        content = QWidget(self)
        content.setObjectName('alertContent')
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(content)
        v = QVBoxLayout(content)
        v.setContentsMargins(22, 20, 22, 18)
        v.setSpacing(8)
        title = QLabel(copy['titulo'], content)
        title.setObjectName('alertTitle')
        title.setWordWrap(True)
        v.addWidget(title)
        sub = QLabel(copy['subtitulo'], content)
        sub.setObjectName('alertSub')
        sub.setWordWrap(True)
        v.addWidget(sub)
        if not is_premium:
            v.addSpacing(6)
            v.addWidget(self._construir_box_comparacao_simples(content))
            v.addSpacing(8)
            v.addWidget(self._construir_box_premium(content))
            v.addSpacing(8)
            v.addWidget(self._construir_box_continua_chegando(content))
            v.addSpacing(6)
            v.addWidget(self._construir_box_warning_validade(content))
        else:
            v.addSpacing(4)
            v.addWidget(self._construir_box_desconto(content, tom))
            v.addSpacing(6)
            sec1 = QLabel('O que continua chegando para voc├¬:', content)
            sec1.setObjectName('alertSection')
            v.addWidget(sec1)
            for b in ALERTA_BENEFICIOS:
                l = QLabel(f'  ÔÇó  {b}', content)
                l.setObjectName('alertBenef')
                l.setWordWrap(True)
                v.addWidget(l)
        v.addSpacing(10)
        if dias_restantes == 'EXPIRADA':
            countdown_txt = 'SUA LICEN├çA EXPIROU'
            countdown_sub = 'Reative agora para continuar de onde parou.'
        elif dias_restantes == 'HOJE':
            countdown_txt = 'EXPIRA HOJE'
            countdown_sub = 'Garanta sua continuidade antes do encerramento!'
        elif dias_restantes == 'Ôê×':
            countdown_txt = ''
            countdown_sub = ''
        else:
            _d = 'DIA' if str(dias_restantes) == '1' else 'DIAS'
            _f = 'FALTA' if str(dias_restantes) == '1' else 'FALTAM'
            countdown_txt = f'{_f} {dias_restantes} {_d}'
            countdown_sub = 'Quanto antes renovar, maior o desconto!'
        if countdown_txt:
            cd_lbl = QLabel(countdown_txt, content)
            cd_lbl.setObjectName('alertCountdown')
            cd_lbl.setAlignment(Qt.AlignCenter)
            cd_lbl.setWordWrap(True)
            v.addWidget(cd_lbl)
            if countdown_sub:
                cd_sub = QLabel(countdown_sub, content)
                cd_sub.setObjectName('alertCountdownSub')
                cd_sub.setAlignment(Qt.AlignCenter)
                cd_sub.setWordWrap(True)
                v.addWidget(cd_sub)
        v.addSpacing(8)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_cta = QPushButton(copy['cta'], content)
        btn_cta.setObjectName('alertCTA')
        btn_cta.setCursor(QCursor(Qt.PointingHandCursor))
        btn_cta.clicked.connect((lambda: (on_falar_equipe(), self.accept())))
        btn_later = QPushButton('Lembrar mais tarde', content)
        btn_later.setObjectName('alertLater')
        btn_later.setCursor(QCursor(Qt.PointingHandCursor))
        btn_later.clicked.connect(self.reject)
        btn_row.addWidget(btn_cta, 1)
        btn_row.addWidget(btn_later, 0)
        v.addLayout(btn_row)
        contact = QLabel('+55 (85) 99746-2977  ÔÇó  fale com a equipe a qualquer momento', content)
        contact.setObjectName('alertContact')
        contact.setAlignment(Qt.AlignCenter)
        v.addWidget(contact)
    def _construir_box_desconto(self, parent: QWidget, tom: str) -> QFrame:
        box = QFrame(parent)
        box.setObjectName('alertDescBox')
        box_v = QVBoxLayout(box)
        box_v.setContentsMargins(14, 10, 14, 10)
        box_v.setSpacing(2)
        pct = DESCONTO_INFO['percentual']
        title_lbl = QLabel(f'{DESCONTO_INFO['label']} ÔÇö at├® {pct}% OFF', box)
        title_lbl.setObjectName('alertDescTitle')
        title_lbl.setWordWrap(True)
        box_v.addWidget(title_lbl)
        if tom == 'calmo':
            body_text = DESCONTO_INFO['linha_calmo'].format(P=pct)
        else:
            body_text = DESCONTO_INFO['linha_principal'].format(P=pct)
        body_lbl = QLabel(body_text, box)
        body_lbl.setObjectName('alertDescBody')
        body_lbl.setWordWrap(True)
        box_v.addWidget(body_lbl)
        return box
    def _construir_box_comparacao_simples(self, parent: QWidget) -> QFrame:
        moeda = PLANOS_INFO['moeda']
        p_normal = PLANOS_INFO['plano_normal_preco']
        p_full = PLANOS_INFO['plano_premium_preco']
        box = QFrame(parent)
        box.setObjectName('alertContinuaBox')
        box_v = QVBoxLayout(box)
        box_v.setContentsMargins(16, 10, 16, 10)
        box_v.setSpacing(3)
        line_normal = QLabel(f'  ÔÇó  Plano Comum:  {moeda} {p_normal}', box)
        line_normal.setObjectName('alertPriceLine')
        line_normal.setWordWrap(True)
        box_v.addWidget(line_normal)
        line_full = QLabel(f'  ÔÇó  Plano Premium:  {moeda} {p_full}', box)
        line_full.setObjectName('alertPriceLine')
        line_full.setWordWrap(True)
        box_v.addWidget(line_full)
        return box
    def _construir_box_premium(self, parent: QWidget) -> QFrame:
        moeda = PLANOS_INFO['moeda']
        p_normal = PLANOS_INFO['plano_normal_preco']
        p_full = PLANOS_INFO['plano_premium_preco']
        p_oferta = PLANOS_INFO['plano_oferta_preco']
        econ_full = p_full - p_oferta
        econ_norm = p_normal - p_oferta
        promo_vigente = self._promocao_vigente()
        box = QFrame(parent)
        box.setObjectName('alertPremiumBox')
        box_v = QVBoxLayout(box)
        box_v.setContentsMargins(16, 12, 16, 12)
        box_v.setSpacing(5)
        title_lbl = QLabel('UPGRADE PROMOCIONAL PREMIUM', box)
        title_lbl.setObjectName('alertPriceTitle')
        title_lbl.setWordWrap(True)
        box_v.addWidget(title_lbl)
        if promo_vigente:
            sub_lbl = QLabel('Renovando antes do vencimento, voc├¬ garante mais 1 ano completo + upgrade Premium por apenas:', box)
            sub_lbl.setObjectName('alertBenefPremium')
            sub_lbl.setWordWrap(True)
            box_v.addWidget(sub_lbl)
            box_v.addSpacing(4)
            hot_lbl = QLabel(f'{moeda} {p_oferta}', box)
            hot_lbl.setObjectName('alertPriceHot')
            hot_lbl.setAlignment(Qt.AlignCenter)
            hot_lbl.setWordWrap(False)
            box_v.addWidget(hot_lbl)
            validade_str = PLANOS_INFO.get('promo_validade_ate', '')
            try:
                dt_val = datetime.strptime(validade_str, '%Y-%m-%d')
                val_fmt = dt_val.strftime('%d/%m/%Y')
            except Exception:
                val_fmt = validade_str
            val_lbl = QLabel(f'Promo├º├úo v├ílida at├® {val_fmt}', box)
            val_lbl.setObjectName('alertPriceEcon')
            val_lbl.setAlignment(Qt.AlignCenter)
            val_lbl.setWordWrap(True)
            box_v.addWidget(val_lbl)
            box_v.addSpacing(4)
            econ1 = QLabel(f'  ÔÇó  {moeda} {econ_full} de desconto no Premium', box)
            econ1.setObjectName('alertPriceEcon')
            econ1.setWordWrap(True)
            box_v.addWidget(econ1)
            econ2 = QLabel(f'  ÔÇó  {moeda} {econ_norm} mais barato que renovar o plano b├ísico', box)
            econ2.setObjectName('alertPriceEcon')
            econ2.setWordWrap(True)
            box_v.addWidget(econ2)
        else:
            sub_lbl = QLabel('Renove antes do vencimento e garante condi├º├úo especial com upgrade Premium incluso!', box)
            sub_lbl.setObjectName('alertBenefPremium')
            sub_lbl.setWordWrap(True)
            box_v.addWidget(sub_lbl)
            box_v.addSpacing(4)
            hot_lbl = QLabel('Consulte sua promo├º├úo exclusiva!', box)
            hot_lbl.setObjectName('alertPriceHot')
            hot_lbl.setAlignment(Qt.AlignCenter)
            hot_lbl.setWordWrap(False)
            box_v.addWidget(hot_lbl)
            box_v.addSpacing(4)
            econ1 = QLabel('  ÔÇó  Desconto garantido para quem renova antecipado', box)
            econ1.setObjectName('alertPriceEcon')
            econ1.setWordWrap(True)
            box_v.addWidget(econ1)
            econ2 = QLabel('  ÔÇó  Acesso imediato a todas as ferramentas Premium', box)
            econ2.setObjectName('alertPriceEcon')
            econ2.setWordWrap(True)
            box_v.addWidget(econ2)
        box_v.addSpacing(6)
        bens_titulo = QLabel('Voc├¬ recebe:', box)
        bens_titulo.setObjectName('alertDescTitle')
        bens_titulo.setWordWrap(True)
        box_v.addWidget(bens_titulo)
        for b in ALERTA_BENEFICIOS_PREMIUM:
            l = QLabel(f'  ÔÇó  {b}', box)
            l.setObjectName('alertBenefPremium')
            l.setWordWrap(True)
            box_v.addWidget(l)
        return box
    @staticmethod
    def _promocao_vigente() -> bool:
        try:
            limite = datetime.strptime(PLANOS_INFO.get('promo_validade_ate', '2026-07-01'), '%Y-%m-%d')
            return datetime.now() <= limite
        except Exception:
            return False
    def _construir_box_continua_chegando(self, parent: QWidget) -> QFrame:
        box = QFrame(parent)
        box.setObjectName('alertContinuaBox')
        box_v = QVBoxLayout(box)
        box_v.setContentsMargins(16, 10, 16, 10)
        box_v.setSpacing(3)
        title_lbl = QLabel('O que continua chegando:', box)
        title_lbl.setObjectName('alertContinuaTitle')
        title_lbl.setWordWrap(True)
        box_v.addWidget(title_lbl)
        for b in ALERTA_BENEFICIOS:
            l = QLabel(f'  ÔÇó  {b}', box)
            l.setObjectName('alertBenef')
            l.setWordWrap(True)
            box_v.addWidget(l)
        return box
    def _construir_box_warning_validade(self, parent: QWidget) -> QFrame:
        box = QFrame(parent)
        box.setObjectName('alertWarningBox')
        box_v = QVBoxLayout(box)
        box_v.setContentsMargins(14, 8, 14, 8)
        box_v.setSpacing(0)
        wlbl = QLabel('Oferta v├ílida somente antes do encerramento da licen├ºa atual.', box)
        wlbl.setObjectName('alertWarning')
        wlbl.setWordWrap(True)
        box_v.addWidget(wlbl)
        return box
class HeaderStatusBar(QWidget):
    def __init__(self, parent_main_window, translation_manager=None):
        super().__init__()
        self.main_window = parent_main_window
        self._tm = translation_manager
        self._card_user = StatusCard('user', self)
        self._card_license = StatusCard('license', self)
        self._card_plan = StatusCard('plan', self)
        for c in self._card_user, self._card_license, self._card_plan:
            c.clicked.connect(self._on_card_clicked)
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        h.addStretch(1)
        h.addWidget(self._card_user)
        h.addWidget(self._card_license)
        h.addWidget(self._card_plan)
        self._alerta_mgr = AlertaRenovacaoManager()
        self.refresh()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start(HEADER_CARDS_CONFIG['refresh_interval_ms'])
        QTimer.singleShot(HEADER_CARDS_CONFIG['boot_check_delay_ms'], self.verificar_alerta)
    def _t(self, chave: str, default: str) -> str:
        if self._tm is None:
            return default
        try:
            getter = getattr(self._tm, 'get_text', None)
            if not callable(getter):
                return default
            valor = getter(chave)
            if isinstance(valor, str) and valor and valor != chave:
                return valor
        except Exception:
            pass
        return default
    def set_translation_manager(self, translation_manager) -> None:
        self._tm = translation_manager
        try:
            self.refresh()
            return
        except Exception as exc:
            print(f'[header_status_cards] refresh apos set TM falhou: {type(exc).__name__}')
    def refresh(self):
        try:
            largura = QApplication.primaryScreen().geometry().width()
        except Exception:
            largura = 1366
        bucket = _bucket_para_largura(largura)
        cfg = HEADER_CARDS_CONFIG
        base_w = cfg[f'card_min_width_{bucket}']
        license_w = int(base_w * (1 + cfg['license_card_extra']))
        username = self._safe_username()
        papel = self._safe_papel()
        self._card_user.aplicar_estilo(bucket, cfg['color_user'], base_w)
        self._card_user.setar_textos(username, self._formatar_saldo_header())
        self._card_user.setToolTip(papel)
        try:
            dias = self.main_window.calcular_dias_restantes()
        except Exception:
            dias = 'N/A'
        try:
            data_exp = self.main_window.obter_data_expiracao_formatada()
        except Exception:
            data_exp = ''
        estilo_lic = _resolver_estilo_licenca(dias)
        self._card_license.aplicar_estilo(bucket, estilo_lic, license_w)
        self._card_license.setar_textos(self._formatar_label_licenca(dias, estilo_lic), self._formatar_sub_licenca(dias, data_exp))
        plan_kind, plan_label, plan_sub = self._resolver_plano()
        self._card_plan.aplicar_estilo(bucket, cfg[plan_kind], base_w)
        self._card_plan.setar_textos(plan_label, plan_sub)
    def verificar_alerta(self, _tentativa: int=0):
        try:
            mw_visivel = bool(self.main_window) and self.main_window.isVisible()
        except Exception:
            mw_visivel = True
        try:
            modal_ativo = QApplication.activeModalWidget() is not None
        except Exception:
            modal_ativo = False
        if (not mw_visivel or modal_ativo) and _tentativa < ALERTA_REAGENDA_MAX:
            QTimer.singleShot(ALERTA_REAGENDA_MS, (lambda: self.verificar_alerta(_tentativa + 1)))
            return
        self._exibir_alerta_seguro()
    def _exibir_alerta_seguro(self):
        try:
            dias = self.main_window.calcular_dias_restantes()
        except Exception:
            return
        if getattr(self.main_window, '_alerta_renovacao_ja_exibido', False):
            return
        regra = _resolver_regra_alerta(dias)
        max_per_day = int(regra.get('max_per_day', 0) or 0)
        if max_per_day <= 0:
            return
        try:
            data_exp = self.main_window.obter_data_expiracao_formatada()
        except Exception:
            data_exp = ''
        is_premium = bool(getattr(self.main_window, 'is_premium_user', False) or getattr(self.main_window, 'is_admin', False))
        try:
            dlg = AlertaRenovacaoDialog(dias_restantes=dias, data_expiracao=data_exp, tom=regra.get('tom', 'novidade'), on_falar_equipe=self._abrir_renovacao, parent=self.main_window, is_premium=is_premium)
            self._alerta_mgr.registrar_exibicao()
            self.main_window._alerta_renovacao_ja_exibido = True
            dlg.exec_()
        except Exception as exc:
            print(f'[header_status_cards] alerta renovacao: {type(exc).__name__}')
    def verificar_alerta_forcado(self):
        try:
            dias = self.main_window.calcular_dias_restantes()
            data_exp = self.main_window.obter_data_expiracao_formatada()
        except Exception:
            dias, data_exp = 'N/A', ''
        if dias == 'Ôê×':
            getattr(self.main_window, 'mostrar_status_licenca', (lambda: None))()
            return
        regra = _resolver_regra_alerta(dias)
        tom = regra.get('tom', 'novidade') or 'novidade'
        is_premium = bool(getattr(self.main_window, 'is_premium_user', False) or getattr(self.main_window, 'is_admin', False))
        dlg = AlertaRenovacaoDialog(dias_restantes=dias, data_expiracao=data_exp, tom=tom, on_falar_equipe=self._abrir_renovacao, parent=self.main_window, is_premium=is_premium)
        dlg.exec_()
    def _abrir_renovacao(self):
        try:
            getattr(self.main_window, 'abrir_renovacao_licenca')()
            return
        except Exception as e:
            print(f'[header_status_cards] abrir_renovacao_licenca: {type(e).__name__}')
    def _on_card_clicked(self, kind: str):
        try:
            if kind == 'license':
                self.verificar_alerta_forcado()
                return
            if kind == 'user':
                getattr(self.main_window, 'ver_perfil', (lambda: None))()
                return
            getattr(self.main_window, 'mostrar_status_licenca', (lambda: None))()
            return
        except Exception as e:
            print(f'[header_status_cards] click {kind}: {type(e).__name__}')
    def _formatar_label_licenca(self, dias: str, estilo: Dict[str, str]) -> str:
        icon = estilo.get('icon', '') or ''
        prefix = f'{icon}  ' if icon else ''
        if dias == 'Ôê×':
            label = self._t('header_lic_label_active', 'Licen├ºa Ativa')
            return f'{prefix}{label}'
        if dias == 'HOJE':
            label = self._t('header_lic_label_today', '├Ültima hoje')
            return f'{prefix}{label}'
        if dias == 'EXPIRADA':
            label = self._t('header_lic_label_reactivate', 'Reativar')
            return f'{prefix}{label}'
        if isinstance(dias, str) and dias.isdigit():
            tpl = self._t('header_lic_label_days', '{N} dias')
            try:
                texto = tpl.format(N=dias)
            except Exception:
                texto = f'{dias} dias'
            return f'{prefix}{texto}'
        label_tpl = estilo.get('label', '{N} dias')
        return f'{prefix}{label_tpl}'
    def _formatar_sub_licenca(self, dias: str, data_exp: str) -> str:
        if dias == 'Ôê×':
            return self._t('header_lic_sub_no_expire', 'Acesso dispon├¡vel')
        if dias == 'EXPIRADA':
            return self._t('header_lic_sub_reactivate', 'Reative seu acesso')
        if dias == 'HOJE':
            return self._t('header_lic_sub_today', 'Encerra hoje')
        if data_exp:
            tpl = self._t('header_lic_sub_expires_at', 'Encerra: {data}')
            try:
                return tpl.format(data=data_exp)
            except Exception:
                return f'Encerra: {data_exp}'
    def _formatar_saldo_header(self) -> str:
        fallback = self._t('header_credits_unavailable', 'Saldo --')
        getter = getattr(self.main_window, 'obter_saldo_creditos_header', None)
        if not callable(getter):
            return fallback
        try:
            saldo = getter()
        except Exception:
            return fallback
        if saldo is None:
            return fallback
        try:
            return f'R$ {float(saldo):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        except (TypeError, ValueError):
            return fallback
    def _safe_username(self) -> str:
        try:
            email = getattr(self.main_window, 'user_email', None)
            if email and '@' in email:
                return email.split('@')[0]
        except Exception:
            pass
        return self._t('header_user_fallback', 'Usu├írio')
    def _safe_papel(self) -> str:
        if getattr(self.main_window, 'is_admin', False):
            return self._t('header_role_admin', 'Administrador')
        if getattr(self.main_window, 'is_premium_user', False):
            return self._t('header_role_premium', 'Premium')
        return self._t('header_role_common', 'Comum')
    def _resolver_plano(self):
        if getattr(self.main_window, 'is_admin', False):
            return 'color_plan_admin', self._t('header_plan_admin', 'Administrador'), self._t('header_plan_admin_sub', 'Acesso total')
        if getattr(self.main_window, 'is_premium_user', False):
            return 'color_plan_premium', self._t('header_plan_premium', 'Plano Premium'), self._t('header_plan_premium_sub', 'Acesso completo')
        return 'color_plan_normal', self._t('header_plan_common', 'Plano Comum'), self._t('header_plan_common_sub', '')
