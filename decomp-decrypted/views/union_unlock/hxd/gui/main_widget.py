import os
import shutil
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QScrollArea, QPushButton, QLabel, QFileDialog, QMessageBox, QFrame, QSizePolicy, QSpacerItem, QComboBox, QLineEdit, QTabWidget)
from PyQt5.QtCore import (Qt, QThread, QSize, pyqtSignal)
from PyQt5.QtGui import (QCursor, QFont, QIcon)
from .tema import (gerar_qss_principal, gerar_qss_botao, gerar_qss_botao_outline, _OBJ_NAME, BG, BG_WHITE, BG_DARK, PRIMARY, PRIMARY_HOVER, UNION_BLUE, UNION_ACCENT, UNION_LIGHT, BORDER, BORDER_LIGHT, TEXT, TEXT_MUTED, TEXT_LABEL, GREEN, GREEN_DARK, RED, RED_BG, YELLOW, ORANGE, WHITE, HEADER_BG)
from .log_seguro import LogSeguro
from ..core.validador import Validador
from ..core.backup_manager import BackupManager
def _aplicar_icone_btn(btn, svg_relativo, tamanho=16):
    try:
        from app.utils.path_manager import PathManager
        caminho = PathManager.get_resource_path(svg_relativo)
        if caminho:
            if os.path.isfile(caminho):
                btn.setIcon(QIcon(caminho))
                btn.setIconSize(QSize(tamanho, tamanho))
                return
            return
    except Exception:
        pass
ProinfoEngine = None
OeminfoEngine = None
PersistEngine = None
OplusEngine = None
Protect1Engine = None
MiscdataEngine = None
try:
    from ..core.engines.proinfo_engine import ProinfoEngine
except Exception:
    pass
try:
    from ..core.engines.oeminfo_engine import OeminfoEngine
except Exception:
    pass
try:
    from ..core.engines.persist_engine import PersistEngine
except Exception:
    pass
try:
    from ..core.engines.oplus_engine import OplusEngine
except Exception:
    pass
try:
    from ..core.engines.protect1_engine import Protect1Engine
except Exception:
    pass
try:
    from ..core.engines.miscdata_engine import MiscdataEngine
except Exception:
    pass
def _diagnostico_engines() -> list[str]:
    import sys
    linhas = []
    for nome, cls in ('proinfo', ProinfoEngine), ('oeminfo', OeminfoEngine), ('persist', PersistEngine), ('oplus', OplusEngine), ('protect1', Protect1Engine), ('miscdata', MiscdataEngine):
        if cls is None:
            linhas.append(f'  {nome}: INDISPONIVEL')
            continue
        mod_name = getattr(cls, '__module__', '')
        mod_obj = sys.modules.get(mod_name)
        arq = getattr(mod_obj, '__file__', '') or ''
        if arq.endswith('.pyd') or arq.endswith('.so'):
            linhas.append(f'  {nome}: .pyd (compilado)')
        else:
            linhas.append(f'  {nome}: .py (fonte)')
    return linhas
_VERSAO = 'v1.0'
_AVISO_LEGAL = 'ATEN├ç├âO: Esta opera├º├úo modifica a parti├º├úo selecionada.\n\nRisco de brick se o arquivo for incorreto.\nUm backup ser├í criado automaticamente.\n\nDeseja continuar?'
_DISCLAIMER = 'AVISO LEGAL: Esta ferramenta ├® destinada a t├®cnicos qualificados. O uso incorreto pode causar danos irrevers├¡veis ao dispositivo. TECH UNION SOLUTIONS n├úo se responsabiliza por uso indevido.'
_LEGALIDADE = 'Dica: Use somente em aparelhos proprios ou com autorizacao do proprietario. Solicite nota fiscal ou termo de responsabilidade ao cliente. Qualquer uso indevido e de inteira responsabilidade do operador.'
class _WorkerThread(QThread):
    finalizado = pyqtSignal(bool, str)
    dados_prontos = pyqtSignal(dict)
    log_emitido = pyqtSignal(str, str)
    def __init__(self, funcao, *args, **kwargs):
        super().__init__()
        self._funcao = funcao
        self._args = args
        self._kwargs = kwargs
    def run(self):
        try:
            resultado = self._funcao(*self._args, **self._kwargs)
            if isinstance(resultado, tuple) and len(resultado) == 3:
                self.dados_prontos.emit(resultado[2])
                self.finalizado.emit(resultado[0], resultado[1])
                return
            if isinstance(resultado, tuple) and len(resultado) == 2:
                self.finalizado.emit(resultado[0], resultado[1])
                return
            self.finalizado.emit(True, 'Opera├º├úo conclu├¡da com sucesso.')
            return
        except Exception:
            self.finalizado.emit(False, 'Erro inesperado durante a opera├º├úo.')
class HxdMainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(_OBJ_NAME)
        self._arquivo_selecionado = None
        self._backup_path = None
        self._worker = None
        self._backup_mgr = BackupManager()
        self._inicializar_ui()
        self._exibir_boas_vindas()
    def _inicializar_ui(self):
        self.setStyleSheet(gerar_qss_principal())
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)
        layout_principal.addWidget(self._criar_header())
        layout_principal.addWidget(self._criar_banner_aviso())
        self._inner_tabs = QTabWidget()
        self._inner_tabs.setDocumentMode(True)
        self._inner_tabs.setStyleSheet(f"\n            QTabWidget::pane {{\n                border: none;\n                border-top: 2px solid {BORDER};\n                background-color: {BG};\n                top: -1px;\n            }}\n            QTabBar {{\n                background: {BG_WHITE};\n                qproperty-drawBase: 0;\n            }}\n            QTabBar::tab {{\n                min-width: 120px;\n                min-height: 28px;\n                margin-right: 4px;\n                padding: 8px 18px;\n                font-size: 12px;\n                font-family: 'Segoe UI';\n                font-weight: bold;\n                color: {TEXT_MUTED};\n                background: {BG};\n                border: 1px solid {BORDER};\n                border-bottom: none;\n                border-top-left-radius: 6px;\n                border-top-right-radius: 6px;\n            }}\n            QTabBar::tab:hover {{\n                color: {PRIMARY};\n                background: {UNION_LIGHT};\n            }}\n            QTabBar::tab:selected {{\n                color: {PRIMARY};\n                background: {BG_WHITE};\n                border: 1px solid {PRIMARY};\n                border-bottom: 2px solid {BG_WHITE};\n                margin-bottom: -2px;\n            }}\n            QTabBar::tab:!selected {{\n                margin-top: 3px;\n            }}\n        ")
        self._inner_tabs.addTab(self._criar_corpo(), 'Partition / ADB')
        try:
            from app.views.union_unlock.honor.honor_frp_widget import HonorFrpWidget
            self._honor_widget = HonorFrpWidget(self)
            self._inner_tabs.addTab(self._honor_widget, 'Honor FRP')
        except Exception:
            self._honor_widget = None
        try:
            from app.views.union_unlock.mit.mit_widget import MitWidget
            self._mit_widget = MitWidget(self)
            self._inner_tabs.addTab(self._mit_widget, 'Meta Mode')
        except Exception:
            self._mit_widget = None
        try:
            from app.views.union_unlock.mit.mit_partition_widget import MitPartitionWidget
            self._mit_part_widget = MitPartitionWidget(self)
            self._inner_tabs.addTab(self._mit_part_widget, 'Meta Partition (teste)')
        except Exception:
            self._mit_part_widget = None
        try:
            from app.views.union_unlock.dmiti.dmiti_widget import DmitiWidget
            self._dmiti_widget = DmitiWidget(self)
            self._inner_tabs.addTab(self._dmiti_widget, 'Diag Mode (SPD)')
        except Exception:
            self._dmiti_widget = None
        self._fmgr_widget = None
        self._fmgr_placeholder = QWidget()
        self._fmgr_tab_idx = self._inner_tabs.addTab(self._fmgr_placeholder, 'File Manager')
        self._inner_tabs.currentChanged.connect(self._on_tab_changed)
        layout_principal.addWidget(self._inner_tabs, stretch=1)
        layout_principal.addWidget(self._criar_status_bar())
    def _on_tab_changed(self, idx):
        if idx == self._fmgr_tab_idx:
            if self._fmgr_widget is None:
                try:
                    from app.views.union_unlock.fmgr.fmgr_widget import FmgrWidget
                    self._fmgr_widget = FmgrWidget(self)
                    self._inner_tabs.removeTab(self._fmgr_tab_idx)
                    self._inner_tabs.insertTab(self._fmgr_tab_idx, self._fmgr_widget, 'File Manager')
                    self._inner_tabs.setCurrentIndex(self._fmgr_tab_idx)
                    self._fmgr_placeholder.deleteLater()
                    self._fmgr_placeholder = None
                except Exception:
                    pass
    def _criar_header(self) -> QFrame:
        frame = QFrame()
        frame.setFixedHeight(48)
        frame.setStyleSheet(f'background-color: {HEADER_BG};')
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 0, 16, 0)
        lbl_titulo = QLabel('TECH UNION SOLUTIONS ÔÇö PARTITION EDITOR / ADB TOOLS')
        lbl_titulo.setFont(QFont('Segoe UI', 14, QFont.Bold))
        lbl_titulo.setStyleSheet(f'color: {WHITE};')
        lbl_titulo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(lbl_titulo)
        layout.addStretch()
        lbl_versao = QLabel(f'[{_VERSAO}]')
        lbl_versao.setStyleSheet('color: rgba(255,255,255,0.7); font-size: 12px;')
        layout.addWidget(lbl_versao)
        return frame
    def _criar_banner_aviso(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f'\n            QFrame {{\n                background-color: {RED_BG};\n                padding: 4px 16px;\n            }}\n        ')
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 3, 16, 3)
        lbl = QLabel('├ürea exclusiva para t├®cnicos qualificados ÔÇö ao trabalhar com parti├º├Áes, fa├ºa backup. Toda opera├º├úo ├® de responsabilidade do operador')
        lbl.setFont(QFont('Segoe UI', 11, QFont.Bold))
        lbl.setStyleSheet(f'color: {WHITE};')
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        return frame
    def _criar_corpo(self) -> QSplitter:
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setChildrenCollapsible(False)
        painel_esquerdo = self._criar_painel_esquerdo()
        splitter.addWidget(painel_esquerdo)
        painel_direito = self._criar_painel_direito()
        splitter.addWidget(painel_direito)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        return splitter
    def _criar_painel_esquerdo(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(f'\n            QScrollArea {{\n                border: none;\n                background-color: {BG_WHITE};\n                border-right: 1px solid {BORDER};\n            }}\n        ')
        scroll.setMinimumWidth(280)
        container = QWidget()
        container.setStyleSheet(f'background-color: {BG_WHITE};')
        container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(self._criar_secao_titulo('ADB TOOLS'))
        _row_top = QHBoxLayout()
        _row_top.setSpacing(10)
        _row_top.addWidget(self._criar_card_newsec(), 1)
        _row_top.addWidget(self._criar_card_fix_playstore(), 1)
        layout.addLayout(_row_top)
        layout.addWidget(self._criar_card_dns_manager())
        layout.addSpacing(12)
        layout.addWidget(self._criar_secao_titulo('MOTOROLA FRP'))
        self._frp_frame = self._criar_frp_frame()
        layout.addWidget(self._frp_frame)
        layout.addSpacing(10)
        layout.addWidget(self._criar_secao_titulo('EDITOR DE PARTI├ç├òES'))
        _part_frame = QFrame()
        _part_frame.setObjectName('card_particoes')
        _part_frame.setStyleSheet(f'\n            QFrame#card_particoes {{\n                background-color: {BG_WHITE};\n                border: 2px solid {UNION_BLUE};\n                border-radius: 8px;\n            }}\n            QFrame#card_particoes:hover {{\n                border: 2px solid {UNION_ACCENT};\n            }}\n        ')
        _part_layout = QVBoxLayout(_part_frame)
        _part_layout.setContentsMargins(14, 10, 14, 10)
        _part_layout.setSpacing(6)
        _lbl_part_sub = QLabel('Selecione o dump de parti├º├úo (.bin / .img) para ler ou gravar')
        _lbl_part_sub.setFont(QFont('Segoe UI', 9))
        _lbl_part_sub.setStyleSheet(f'color: {TEXT_MUTED}; border: none; background: transparent;')
        _lbl_part_sub.setWordWrap(True)
        _part_layout.addWidget(_lbl_part_sub)
        self._btn_selecionar = QPushButton('Selecionar parti├º├úo...')
        self._btn_selecionar.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_selecionar.setStyleSheet(gerar_qss_botao())
        self._btn_selecionar.setMinimumHeight(30)
        self._btn_selecionar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        _aplicar_icone_btn(self._btn_selecionar, 'icons_svg/folder-check.svg')
        self._btn_selecionar.clicked.connect(self._selecionar_arquivo)
        _part_layout.addWidget(self._btn_selecionar)
        self._lbl_arquivo = QLabel('arquivo: nenhum')
        self._lbl_arquivo.setFont(QFont('Segoe UI', 9))
        self._lbl_arquivo.setStyleSheet(f'color: {TEXT_MUTED}; border: none; background: transparent;')
        self._lbl_arquivo.setWordWrap(True)
        _part_layout.addWidget(self._lbl_arquivo)
        layout.addWidget(_part_frame)
        layout.addSpacing(8)
        layout.addWidget(self._criar_secao_titulo('OPERA├ç├òES'))
        self._botoes_operacao = []
        self._botoes_aplicar = []
        layout.addWidget(self._criar_dropdown_operacoes())
        layout.addSpacing(12)
        layout.addWidget(self._criar_secao_titulo('INFORMA├ç├òES'))
        info_frame = QFrame()
        info_frame.setStyleSheet(f'\n            QFrame {{\n                background-color: {BG};\n                border: 1px solid {BORDER};\n                border-radius: 8px;\n                padding: 8px;\n            }}\n        ')
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(12, 8, 12, 8)
        info_layout.setSpacing(4)
        self._lbl_modelo = QLabel('Modelo: ÔÇö')
        self._lbl_modelo.setFont(QFont('Segoe UI', 11))
        self._lbl_modelo.setStyleSheet(f'color: {TEXT};')
        self._lbl_modelo.setWordWrap(True)
        info_layout.addWidget(self._lbl_modelo)
        self._lbl_firmware = QLabel('Firmware: ÔÇö')
        self._lbl_firmware.setFont(QFont('Segoe UI', 11))
        self._lbl_firmware.setStyleSheet(f'color: {TEXT};')
        self._lbl_firmware.setWordWrap(True)
        info_layout.addWidget(self._lbl_firmware)
        self._lbl_status_info = QLabel('Status: ÔÇö')
        self._lbl_status_info.setFont(QFont('Segoe UI', 11, QFont.Bold))
        self._lbl_status_info.setStyleSheet(f'color: {PRIMARY};')
        self._lbl_status_info.setWordWrap(True)
        info_layout.addWidget(self._lbl_status_info)
        layout.addWidget(info_frame)
        layout.addSpacing(12)
        layout_acoes = QHBoxLayout()
        layout_acoes.setSpacing(8)
        self._btn_backup = QPushButton('Backup')
        self._btn_backup.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_backup.setStyleSheet(gerar_qss_botao_outline())
        self._btn_backup.setEnabled(False)
        self._btn_backup.clicked.connect(self._fazer_backup)
        layout_acoes.addWidget(self._btn_backup)
        self._btn_reverter = QPushButton('Reverter')
        self._btn_reverter.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_reverter.setStyleSheet(gerar_qss_botao_outline())
        self._btn_reverter.setEnabled(False)
        self._btn_reverter.setVisible(False)
        _aplicar_icone_btn(self._btn_reverter, 'icons_svg/arrow-clockwise.svg')
        self._btn_reverter.clicked.connect(self._reverter_backup)
        layout_acoes.addWidget(self._btn_reverter)
        layout.addLayout(layout_acoes)
        layout.addStretch()
        scroll.setWidget(container)
        return scroll
    def _criar_painel_direito(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet(f'background-color: {BG};')
        container.setMinimumWidth(300)
        container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 16, 16, 16)
        layout.setSpacing(8)
        lbl_titulo_log = QLabel('Logs do Sistema')
        lbl_titulo_log.setFont(QFont('Segoe UI', 12, QFont.Bold))
        lbl_titulo_log.setStyleSheet(f'color: {TEXT}; padding-bottom: 4px;')
        layout.addWidget(lbl_titulo_log)
        self._log = LogSeguro(self)
        layout.addWidget(self._log, stretch=1)
        layout_btns_log = QHBoxLayout()
        layout_btns_log.setSpacing(8)
        btn_limpar = QPushButton('Limpar Log')
        btn_limpar.setCursor(QCursor(Qt.PointingHandCursor))
        btn_limpar.setStyleSheet(gerar_qss_botao_outline())
        _aplicar_icone_btn(btn_limpar, 'icons_svg/trash.svg')
        btn_limpar.clicked.connect(self._limpar_log)
        layout_btns_log.addWidget(btn_limpar)
        btn_exportar = QPushButton('Exportar Log')
        btn_exportar.setCursor(QCursor(Qt.PointingHandCursor))
        btn_exportar.setStyleSheet(gerar_qss_botao_outline())
        btn_exportar.clicked.connect(self._exportar_log)
        layout_btns_log.addWidget(btn_exportar)
        layout_btns_log.addStretch()
        layout.addLayout(layout_btns_log)
        return container
    def _criar_status_bar(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f'\n            QFrame {{\n                background-color: {BG_WHITE};\n                border-top: 1px solid {BORDER};\n                padding: 4px 16px;\n            }}\n        ')
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 4, 16, 4)
        self._lbl_status = QLabel('Status: Pronto')
        self._lbl_status.setFont(QFont('Segoe UI', 10))
        self._lbl_status.setStyleSheet(f'color: {TEXT_MUTED};')
        layout.addWidget(self._lbl_status)
        layout.addStretch()
        lbl_marca = QLabel(f'TECH UNION SOLUTIONS {_VERSAO}')
        lbl_marca.setFont(QFont('Segoe UI', 10))
        lbl_marca.setStyleSheet(f'color: {TEXT_LABEL};')
        layout.addWidget(lbl_marca)
        return frame
    def _criar_secao_titulo(self, texto: str) -> QLabel:
        lbl = QLabel(texto.upper())
        lbl.setFont(QFont('Segoe UI', 10, QFont.Bold))
        lbl.setStyleSheet(f'color: {TEXT_MUTED}; padding: 4px 0; letter-spacing: 1px;')
        return lbl
    def _criar_frp_frame(self) -> QWidget:
        try:
            from .moto_frp_widget import MotoFrpFrame
            return MotoFrpFrame(parent=self, log_callback=self._log_msg)
        except Exception:
            lbl = QLabel('Modulo FRP indisponivel')
            lbl.setStyleSheet(f'color: {TEXT_MUTED}; padding: 8px;')
            return lbl
    def _log_msg(self, msg: str):
        if hasattr(self, '_log'):
            if self._log:
                self._log.info(msg)
    def _criar_card_operacao(self, titulo: str, subtitulo: str, cb_ler, cb_aplicar=None) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f'\n            QFrame#card_op {{\n                background-color: {BG_WHITE};\n                border: 1px solid {BORDER};\n                border-radius: 8px;\n            }}\n            QFrame#card_op:hover {{\n                border: 1px solid {UNION_ACCENT};\n            }}\n        ')
        card.setObjectName('card_op')
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 10, 14, 10)
        card_layout.setSpacing(6)
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setFont(QFont('Segoe UI', 12, QFont.Bold))
        lbl_titulo.setStyleSheet(f'color: {TEXT}; border: none; background: transparent;')
        card_layout.addWidget(lbl_titulo)
        lbl_sub = QLabel(subtitulo)
        lbl_sub.setFont(QFont('Segoe UI', 9))
        lbl_sub.setStyleSheet(f'color: {TEXT_MUTED}; border: none; background: transparent;')
        card_layout.addWidget(lbl_sub)
        row = QHBoxLayout()
        row.setSpacing(8)
        btn_ler = QPushButton('Ler Info')
        btn_ler.setCursor(QCursor(Qt.PointingHandCursor))
        btn_ler.setMinimumHeight(30)
        btn_ler.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_ler.setStyleSheet(gerar_qss_botao())
        btn_ler.setEnabled(False)
        _aplicar_icone_btn(btn_ler, 'icons_svg/card-checklist.svg')
        btn_ler.clicked.connect(cb_ler)
        row.addWidget(btn_ler)
        self._botoes_operacao.append(btn_ler)
        if cb_aplicar:
            btn_aplicar = QPushButton('Aplicar')
            btn_aplicar.setCursor(QCursor(Qt.PointingHandCursor))
            btn_aplicar.setMinimumHeight(30)
            btn_aplicar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn_aplicar.setStyleSheet(gerar_qss_botao_outline())
            btn_aplicar.setEnabled(False)
            _aplicar_icone_btn(btn_aplicar, 'icons_svg/shield-lock.svg')
            btn_aplicar.clicked.connect(cb_aplicar)
            row.addWidget(btn_aplicar)
            self._botoes_operacao.append(btn_aplicar)
            self._botoes_aplicar.append(btn_aplicar)
        card_layout.addLayout(row)
        return card
    def _criar_dropdown_operacoes(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet('background: transparent;')
        v_layout = QVBoxLayout(container)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(8)
        self._mapa_operacoes = [{'label': 'Region Lock ÔÇö Realme / OPPO (proinfo)', 'ler': self._ler_region_lock, 'aplicar': self._aplicar_region_lock}, {'label': 'PYJ / UserLock ÔÇö Huawei / Honor (oeminfo)', 'ler': self._ler_payjoy, 'aplicar': self._aplicar_payjoy}, {'label': 'Mi Account ÔÇö Xiaomi (persist)', 'ler': self._ler_mi_account, 'aplicar': self._aplicar_mi_account}, {'label': 'SIM Lock ÔÇö MediaTek (protect1)', 'ler': self._ler_simlock, 'aplicar': self._aplicar_simlock}, {'label': 'MDM Bypass ÔÇö SPD / UNISOC (miscdata)', 'ler': self._ler_mdm, 'aplicar': self._aplicar_mdm}, {'label': 'PYJ Bypass SPD ÔÇö Realme SPD (miscdata)', 'ler': self._ler_payj_spd, 'aplicar': self._aplicar_payj_spd}, {'label': 'r-guard ÔÇö SPD / UNISOC (miscdata)', 'ler': self._ler_rguard, 'aplicar': self._aplicar_rguard}, {'label': 'Leitor PCB / FW ÔÇö Realme / OPPO (leitura)', 'ler': self._ler_oplus, 'aplicar': None}]
        self._combo_operacao = QComboBox()
        self._combo_operacao.setCursor(QCursor(Qt.PointingHandCursor))
        for op in self._mapa_operacoes:
            self._combo_operacao.addItem(op['label'])
        _seta_qss = ''
        try:
            _svg = None
            try:
                from app.utils.path_manager import PathManager
                _candidate = PathManager.get_resource_path(os.path.join('icons_svg', 'seta_down.svg'))
                if _candidate and os.path.isfile(_candidate):
                    _svg = os.path.normpath(_candidate).replace('\\', '/')
            except Exception:
                pass
            else:
                if not _svg:
                    _base = os.path.dirname(os.path.abspath(__file__))
                    _svg = os.path.normpath(os.path.join(_base, '..', '..', '..', '..', 'resources', 'icons_svg', 'seta_down.svg')).replace('\\', '/')
                if os.path.isfile(_svg):
                    _seta_qss = f'QComboBox::down-arrow {{  image: url({_svg}); width: 12px; height: 12px;}}'
        except Exception:
            pass
        self._combo_operacao.setStyleSheet(f"\n            QComboBox {{\n                background-color: {BG_WHITE};\n                border: 2px solid {UNION_BLUE};\n                border-radius: 6px;\n                padding: 8px 12px;\n                font-family: 'Segoe UI', sans-serif;\n                font-size: 12px;\n                font-weight: bold;\n                color: {TEXT};\n                min-height: 28px;\n            }}\n            QComboBox:hover {{ border-color: {UNION_ACCENT}; }}\n            QComboBox:disabled {{\n                border-color: {BORDER};\n                color: {TEXT_MUTED};\n                background-color: {BG};\n            }}\n            QComboBox::drop-down {{\n                border: none; width: 28px; padding-right: 6px;\n            }}\n            QComboBox QAbstractItemView {{\n                background-color: {BG_WHITE};\n                border: 1px solid {UNION_BLUE};\n                selection-background-color: {UNION_BLUE};\n                selection-color: {WHITE};\n                padding: 4px;\n                outline: none;\n            }}\n            QComboBox QAbstractItemView::item {{\n                min-height: 28px; padding: 4px 8px;\n            }}\n            QComboBox QAbstractItemView::item:hover {{\n                background-color: {UNION_LIGHT};\n                color: {TEXT};\n            }}\n            {_seta_qss}\n        ")
        self._combo_operacao.currentIndexChanged.connect(self._on_operacao_mudou)
        v_layout.addWidget(self._combo_operacao)
        row = QHBoxLayout()
        row.setSpacing(8)
        self._btn_ler_op = QPushButton('Ler Info')
        self._btn_ler_op.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_ler_op.setMinimumHeight(30)
        self._btn_ler_op.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._btn_ler_op.setStyleSheet(gerar_qss_botao())
        self._btn_ler_op.setEnabled(False)
        _aplicar_icone_btn(self._btn_ler_op, 'icons_svg/card-checklist.svg')
        self._btn_ler_op.clicked.connect(self._ler_operacao_selecionada)
        row.addWidget(self._btn_ler_op)
        self._botoes_operacao.append(self._btn_ler_op)
        self._btn_aplicar_op = QPushButton('Aplicar')
        self._btn_aplicar_op.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_aplicar_op.setMinimumHeight(30)
        self._btn_aplicar_op.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._btn_aplicar_op.setStyleSheet(gerar_qss_botao_outline())
        self._btn_aplicar_op.setEnabled(False)
        _aplicar_icone_btn(self._btn_aplicar_op, 'icons_svg/shield-lock.svg')
        self._btn_aplicar_op.clicked.connect(self._aplicar_operacao_selecionada)
        row.addWidget(self._btn_aplicar_op)
        self._botoes_operacao.append(self._btn_aplicar_op)
        self._botoes_aplicar.append(self._btn_aplicar_op)
        v_layout.addLayout(row)
        self._on_operacao_mudou(0)
        return container
    def _on_operacao_mudou(self, index: int):
        try:
            if 0 <= index < len(self._mapa_operacoes):
                tem_aplicar = self._mapa_operacoes[index]['aplicar'] is not None
                self._btn_aplicar_op.setVisible(tem_aplicar)
                return
        except (AttributeError, IndexError):
            pass
    def _ler_operacao_selecionada(self):
        try:
            idx = self._combo_operacao.currentIndex()
            if 0 <= idx < len(self._mapa_operacoes):
                cb = self._mapa_operacoes[idx]['ler']
                if cb:
                    cb()
                    return
        except (AttributeError, IndexError):
            self._log.erro('Opera├º├úo indispon├¡vel.')
    def _aplicar_operacao_selecionada(self):
        try:
            idx = self._combo_operacao.currentIndex()
            if 0 <= idx < len(self._mapa_operacoes):
                cb = self._mapa_operacoes[idx]['aplicar']
                if cb:
                    cb()
                    return
        except (AttributeError, IndexError):
            self._log.erro('Opera├º├úo indispon├¡vel.')
    def _selecionar_arquivo(self):
        try:
            dir_inicial = str(Path.home() / 'Documents')
            if not os.path.isdir(dir_inicial):
                dir_inicial = str(Path.home())
            caminho, _ = QFileDialog.getOpenFileName(self, 'Selecionar Parti├º├úo', dir_inicial, 'Parti├º├Áes (*.bin *.img);;Todos (*.*)')
            if caminho:
                self._arquivo_selecionado = caminho
                nome_arquivo = os.path.basename(caminho)
                self._lbl_arquivo.setText(f'arquivo: {nome_arquivo}')
                self._lbl_arquivo.setToolTip(caminho)
                self._habilitar_operacoes(True)
                self._btn_backup.setEnabled(True)
                self._log.info(f'Arquivo selecionado: {nome_arquivo}')
                self._log.separador()
                self._atualizar_status('Arquivo carregado')
                self._auto_detectar()
                return
        except Exception:
            self._log.erro('Falha ao selecionar arquivo.')
            self._atualizar_status('Erro na sele├º├úo')
    def _auto_detectar(self):
        if not self._arquivo_selecionado:
            return
        try:
            nome = os.path.basename(self._arquivo_selecionado).lower()
            tamanho = os.path.getsize(self._arquivo_selecionado)
            tipo_detectado = 'Desconhecido'
            if 'proinfo' in nome:
                tipo_detectado = 'proinfo (Realme/OPPO)'
            elif 'oeminfo' in nome:
                tipo_detectado = 'oeminfo (Huawei)'
            elif 'persist' in nome:
                tipo_detectado = 'persist (Xiaomi)'
            elif 'protect' in nome:
                tipo_detectado = 'protect1 (MTK ÔÇö SIM Lock)'
            elif 'miscdata' in nome:
                tipo_detectado = 'miscdata (SPD/UNISOC)'
            elif 'oplusreserve' in nome:
                tipo_detectado = 'oplusreserve (OPPO/Realme)'
            elif 'opporeserve' in nome:
                tipo_detectado = 'opporeserve (OPPO)'
            tamanho_fmt = self._formatar_tamanho(tamanho)
            self._lbl_modelo.setText(f'Modelo: {tipo_detectado}')
            self._lbl_firmware.setText(f'Tamanho: {tamanho_fmt}')
            self._lbl_status_info.setText('Status: Pronto para opera├º├úo')
            self._log.info(f'Tipo detectado: {tipo_detectado}')
            self._log.info(f'Tamanho: {tamanho_fmt}')
            return
        except Exception:
            self._lbl_modelo.setText('Modelo: ÔÇö')
            self._lbl_firmware.setText('Firmware: ÔÇö')
            self._lbl_status_info.setText('Status: Erro na detec├º├úo')
            self._log.aviso('N├úo foi poss├¡vel detectar o tipo automaticamente.')
    def _validar_ou_avisar(self, func_validar, estrito: bool=False) -> bool:
        if not self._arquivo_selecionado:
            self._log.erro('Nenhum arquivo selecionado.')
            return False
        try:
            ok, msg = func_validar(self._arquivo_selecionado, estrito=estrito)
        except TypeError:
            ok, msg = func_validar(self._arquivo_selecionado)
        if not ok:
            self._log.erro(f'Valida├º├úo: {msg}')
        return ok
    def _engine_disponivel(self, engine_cls, nome: str) -> bool:
        if engine_cls is None:
            self._log.erro(f'Motor {nome} indispon├¡vel ÔÇö m├│dulo n├úo carregou. Verifique se a compila├º├úo (.pyd) est├í ├¡ntegra.')
            return False
        return True
    def _confirmar_com_backup(self, nome_op: str) -> bool:
        backup_ok = self._criar_backup_automatico()
        if not backup_ok:
            QMessageBox.critical(self, 'Backup Obrigat├│rio', 'N├úo foi poss├¡vel criar o backup de seguran├ºa.\n\nA opera├º├úo foi cancelada automaticamente.\nVerifique permiss├Áes e espa├ºo em disco.')
            self._log.erro('Opera├º├úo bloqueada: backup obrigat├│rio falhou.')
            return False
        resposta = QMessageBox.warning(self, f'Confirmar: {nome_op}', 'ATEN├ç├âO: Esta opera├º├úo modifica a parti├º├úo selecionada.\n\nRisco de brick se o arquivo for incorreto.\nUm backup j├í foi criado automaticamente.\n\nDeseja aplicar a modifica├º├úo?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resposta != QMessageBox.Yes:
            self._log.info('Opera├º├úo cancelada pelo usu├írio.')
            return False
        return True
    def _executar_em_thread(self, nome: str, funcao_engine):
        if self._worker and self._worker.isRunning():
            self._log.aviso('Aguarde a opera├º├úo anterior finalizar.')
            return
        self._habilitar_operacoes(False)
        self._atualizar_status(f'Executando: {nome}...')
        self._log.separador()
        self._log.info(f'Iniciando opera├º├úo: {nome}')
        self._worker = _WorkerThread(funcao_engine, self._arquivo_selecionado)
        self._worker.finalizado.connect((lambda ok, msg: self._operacao_finalizada(ok, msg, nome)))
        self._worker.start()
    def _operacao_finalizada(self, sucesso: bool, mensagem: str, nome_op: str):
        self._habilitar_operacoes(True)
        if sucesso:
            self._log.sucesso(f'{nome_op}: {mensagem}')
            self._atualizar_status(f'{nome_op} ÔÇö Conclu├¡do')
            if nome_op == 'PYJ Bypass SPD':
                self._log.separador()
                self._log.aviso('INSTRU├ç├òES P├ôS-GRAVA├ç├âO:')
                self._log.info('1. Grave a miscdata no dispositivo')
                self._log.info('2. Erase persist e userdata')
                self._log.info('3. Desative atualiza├º├Áes OTA')
                self._log.aviso('Em caso de brick: restaure backup + format userdata e persist')
            if nome_op != 'Leitor PCB / FW':
                self._btn_reverter.setVisible(True)
                self._btn_reverter.setEnabled(True)
        else:
            self._log.erro(f'{nome_op}: {mensagem}')
            self._atualizar_status(f'{nome_op} ÔÇö Falha')
        self._log.separador()
    def _criar_card_newsec(self) -> QFrame:
        card = QFrame()
        card.setObjectName('card_newsec')
        card.setStyleSheet(f'\n            QFrame#card_newsec {{\n                background-color: {BG_WHITE};\n                border: 2px solid {UNION_BLUE};\n                border-radius: 8px;\n            }}\n            QFrame#card_newsec:hover {{\n                border: 2px solid {UNION_ACCENT};\n            }}\n        ')
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 10, 14, 10)
        card_layout.setSpacing(6)
        lbl_titulo = QLabel('SPD/MTK/SAM New Sec 2026')
        lbl_titulo.setFont(QFont('Segoe UI', 12, QFont.Bold))
        lbl_titulo.setStyleSheet(f'color: {UNION_BLUE}; border: none; background: transparent;')
        card_layout.addWidget(lbl_titulo)
        lbl_sub = QLabel('Prote├º├úo anti-relock via ADB (SPD / MediaTek)')
        lbl_sub.setFont(QFont('Segoe UI', 9))
        lbl_sub.setStyleSheet(f'color: {TEXT_MUTED}; border: none; background: transparent;')
        card_layout.addWidget(lbl_sub)
        self._btn_newsec = QPushButton('Executar')
        self._btn_newsec.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_newsec.setMinimumHeight(30)
        self._btn_newsec.setStyleSheet(f'\n            QPushButton {{\n                background-color: {UNION_BLUE};\n                color: {WHITE};\n                border: none;\n                border-radius: 6px;\n                font-size: 11px;\n                font-weight: 600;\n                padding: 6px 16px;\n            }}\n            QPushButton:hover {{\n                background-color: {UNION_ACCENT};\n            }}\n            QPushButton:pressed {{\n                background-color: #000D40;\n            }}\n            QPushButton:disabled {{\n                background-color: #8a8a8a;\n                color: #cccccc;\n            }}\n        ')
        _aplicar_icone_btn(self._btn_newsec, 'icons_svg/shield-lock.svg')
        self._btn_newsec.clicked.connect(self._executar_newsec)
        card_layout.addWidget(self._btn_newsec, alignment=Qt.AlignLeft)
        return card
    def _executar_newsec(self):
        if self._worker and self._worker.isRunning():
            self._log.aviso('Aguarde a opera├º├úo anterior finalizar.')
            return
        try:
            from app.utils.adb_manager import ADBManager
            from ..core.engines.newsec_engine import NewsecEngine
        except Exception:
            self._log.erro('M├│dulo de prote├º├úo indispon├¡vel.')
        resposta = QMessageBox.warning(self, 'SPD/MTK/SAM New Sec 2026', 'Esta opera├º├úo ir├í:\n\nÔÇó Remover bloqueios de gerenciamento remoto\nÔÇó Ativar prote├º├úo anti-relock permanente\nÔÇó Configurar DNS seguro\n\nCertifique-se que o dispositivo est├í conectado via USB\ncom depura├º├úo USB ativada e sem contas cadastradas.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resposta != QMessageBox.Yes:
            self._log.info('Opera├º├úo cancelada pelo usu├írio.')
            return
        self._btn_newsec.setEnabled(False)
        self._habilitar_operacoes(False)
        self._atualizar_status('Processando...')
        self._log.separador()
        self._log.info('Iniciando operacao...')
        try:
            adb = ADBManager()
            engine = NewsecEngine(adb)
        except Exception:
            self._log.erro('Servi├ºo de comunica├º├úo indispon├¡vel.')
            self._btn_newsec.setEnabled(True)
            self._habilitar_operacoes(True)
            self._atualizar_status('Falha na conex├úo')
        def _tarefa():
            def _log_cb(tipo, msg):
                self._worker.log_emitido.emit(tipo, msg)
            return engine.executar(_log_cb)
        self._worker = _WorkerThread(_tarefa)
        self._worker.log_emitido.connect(self._on_newsec_log)
        self._worker.finalizado.connect(self._on_newsec_finalizado)
        self._worker.start()
    def _on_newsec_log(self, tipo: str, msg: str):
        if tipo == 'info':
            self._log.info(msg)
            return
        if tipo == 'ok':
            self._log.sucesso(msg)
            return
        if tipo == 'erro':
            self._log.erro(msg)
            return
        if tipo == 'aviso':
            self._log.aviso(msg)
            return
        if tipo == 'separador':
            self._log.separador()
            return
        if tipo == 'dados':
            self._log.info(msg)
    def _on_newsec_finalizado(self, sucesso: bool, mensagem: str):
        self._btn_newsec.setEnabled(True)
        self._habilitar_operacoes(True)
        if sucesso:
            self._atualizar_status('SPD/MTK/SAM New Sec 2026 ÔÇö Conclu├¡do')
            return
        self._atualizar_status('SPD/MTK/SAM New Sec 2026 ÔÇö Falha')
    def _criar_card_fix_playstore(self) -> QFrame:
        card = QFrame()
        card.setObjectName('card_fixps')
        card.setStyleSheet(f'\n            QFrame#card_fixps {{\n                background-color: {BG_WHITE};\n                border: 2px solid {GREEN};\n                border-radius: 8px;\n            }}\n            QFrame#card_fixps:hover {{\n                border: 2px solid {GREEN_DARK};\n            }}\n        ')
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 10, 14, 10)
        card_layout.setSpacing(6)
        lbl_titulo = QLabel('Fix Play Store')
        lbl_titulo.setFont(QFont('Segoe UI', 12, QFont.Bold))
        lbl_titulo.setStyleSheet(f'color: {GREEN_DARK}; border: none; background: transparent;')
        card_layout.addWidget(lbl_titulo)
        lbl_sub = QLabel('Restaurar comunica├º├úo com Google Play Services')
        lbl_sub.setFont(QFont('Segoe UI', 9))
        lbl_sub.setStyleSheet(f'color: {TEXT_MUTED}; border: none; background: transparent;')
        card_layout.addWidget(lbl_sub)
        self._btn_fix_ps = QPushButton('Executar')
        self._btn_fix_ps.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_fix_ps.setMinimumHeight(30)
        self._btn_fix_ps.setStyleSheet(f'\n            QPushButton {{\n                background-color: {GREEN};\n                color: {WHITE};\n                border: none;\n                border-radius: 6px;\n                font-size: 11px;\n                font-weight: 600;\n                padding: 6px 16px;\n            }}\n            QPushButton:hover {{\n                background-color: {GREEN_DARK};\n            }}\n            QPushButton:pressed {{\n                background-color: #1a5c2e;\n            }}\n            QPushButton:disabled {{\n                background-color: #8a8a8a;\n                color: #cccccc;\n            }}\n        ')
        _aplicar_icone_btn(self._btn_fix_ps, 'icons_svg/arrow-clockwise.svg')
        self._btn_fix_ps.clicked.connect(self._executar_fix_playstore)
        card_layout.addWidget(self._btn_fix_ps, alignment=Qt.AlignLeft)
        return card
    def _executar_fix_playstore(self):
        if self._worker and self._worker.isRunning():
            self._log.aviso('Aguarde a opera├º├úo anterior finalizar.')
            return
        try:
            from app.utils.adb_manager import ADBManager
            from ..core.engines.newsec_engine import NewsecEngine
        except Exception:
            self._log.erro('M├│dulo de prote├º├úo indispon├¡vel.')
        resposta = QMessageBox.warning(self, 'Fix Play Store', 'Esta opera├º├úo ir├í restaurar a comunica├º├úo com\no Google Play Store no dispositivo.\n\nO WiFi ser├í desligado temporariamente durante\no processo e religado ao final.\n\nCertifique-se que o dispositivo est├í conectado\nvia USB com depura├º├úo USB ativada.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resposta != QMessageBox.Yes:
            self._log.info('Opera├º├úo cancelada pelo usu├írio.')
            return
        self._btn_fix_ps.setEnabled(False)
        self._btn_newsec.setEnabled(False)
        self._habilitar_operacoes(False)
        self._atualizar_status('Restaurando Play Store...')
        self._log.separador()
        self._log.info('Restaurando Play Store...')
        try:
            adb = ADBManager()
            engine = NewsecEngine(adb)
        except Exception:
            self._log.erro('Servi├ºo de comunica├º├úo indispon├¡vel.')
            self._btn_fix_ps.setEnabled(True)
            self._btn_newsec.setEnabled(True)
            self._habilitar_operacoes(True)
            self._atualizar_status('Falha na conex├úo')
        def _tarefa():
            def _log_cb(tipo, msg):
                self._worker.log_emitido.emit(tipo, msg)
            return engine.fix_playstore(_log_cb)
        self._worker = _WorkerThread(_tarefa)
        self._worker.log_emitido.connect(self._on_newsec_log)
        self._worker.finalizado.connect(self._on_fix_ps_finalizado)
        self._worker.start()
    def _on_fix_ps_finalizado(self, sucesso: bool, mensagem: str):
        self._btn_fix_ps.setEnabled(True)
        self._btn_newsec.setEnabled(True)
        self._habilitar_operacoes(True)
        if sucesso:
            self._atualizar_status('Fix Play Store ÔÇö Conclu├¡do')
            return
        self._atualizar_status('Fix Play Store ÔÇö Falha')
    def _criar_card_dns_manager(self) -> QFrame:
        card = QFrame()
        card.setObjectName('card_dns')
        card.setStyleSheet(f'\n            QFrame#card_dns {{\n                background-color: {BG_WHITE};\n                border: 2px solid {ORANGE};\n                border-radius: 8px;\n            }}\n            QFrame#card_dns:hover {{\n                border: 2px solid #cc6600;\n            }}\n        ')
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 10, 14, 10)
        card_layout.setSpacing(6)
        lbl_titulo = QLabel('DNS Manager')
        lbl_titulo.setFont(QFont('Segoe UI', 12, QFont.Bold))
        lbl_titulo.setStyleSheet(f'color: {ORANGE}; border: none; background: transparent;')
        card_layout.addWidget(lbl_titulo)
        self._dns_input = QLineEdit()
        self._dns_input.setPlaceholderText('ex: 7d5cc9.dns.nextdns.io')
        self._dns_input.setFont(QFont('Consolas', 10))
        self._dns_input.setMinimumHeight(32)
        self._dns_input.setStyleSheet(f'\n            QLineEdit {{\n                background-color: {BG_WHITE};\n                border: 1px solid {BORDER};\n                border-radius: 5px;\n                padding: 4px 8px;\n                color: {TEXT};\n            }}\n            QLineEdit:focus {{\n                border: 1px solid {ORANGE};\n            }}\n        ')
        card_layout.addWidget(self._dns_input)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        _btn_style = '\n            QPushButton {{\n                background-color: {cor};\n                color: {branco};\n                border: none;\n                border-radius: 6px;\n                font-size: 11px;\n                font-weight: 600;\n                padding: 6px 10px;\n            }}\n            QPushButton:hover {{ background-color: {hover}; }}\n            QPushButton:disabled {{\n                background-color: #8a8a8a; color: #cccccc;\n            }}\n        '
        self._btn_dns_test = QPushButton('Testar')
        self._btn_dns_test.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_dns_test.setMinimumHeight(30)
        self._btn_dns_test.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._btn_dns_test.setStyleSheet(_btn_style.format(cor=UNION_BLUE, branco=WHITE, hover=UNION_ACCENT))
        self._btn_dns_test.clicked.connect(self._dns_on_test)
        self._btn_dns_apply = QPushButton('Aplicar')
        self._btn_dns_apply.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_dns_apply.setMinimumHeight(30)
        self._btn_dns_apply.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._btn_dns_apply.setStyleSheet(_btn_style.format(cor=GREEN, branco=WHITE, hover=GREEN_DARK))
        self._btn_dns_apply.clicked.connect(self._dns_on_apply)
        self._btn_dns_remove = QPushButton('Remover')
        self._btn_dns_remove.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_dns_remove.setMinimumHeight(30)
        self._btn_dns_remove.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._btn_dns_remove.setStyleSheet(_btn_style.format(cor=RED, branco=WHITE, hover='#c0392b'))
        self._btn_dns_remove.clicked.connect(self._dns_on_remove)
        btn_row.addWidget(self._btn_dns_test)
        btn_row.addWidget(self._btn_dns_apply)
        btn_row.addWidget(self._btn_dns_remove)
        card_layout.addLayout(btn_row)
        self._lbl_dns_status = QLabel('')
        self._lbl_dns_status.setFont(QFont('Segoe UI', 8))
        self._lbl_dns_status.setStyleSheet(f'color: {TEXT_MUTED}; border: none; background: transparent;')
        self._lbl_dns_status.setWordWrap(True)
        card_layout.addWidget(self._lbl_dns_status)
        return card
    def _dns_set_busy(self, busy: bool):
        self._btn_dns_test.setEnabled(not busy)
        self._btn_dns_apply.setEnabled(not busy)
        self._btn_dns_remove.setEnabled(not busy)
        self._dns_input.setEnabled(not busy)
        self._btn_newsec.setEnabled(not busy)
        self._btn_fix_ps.setEnabled(not busy)
        if busy:
            self._habilitar_operacoes(False)
            return
        self._habilitar_operacoes(True)
    def _dns_get_engine(self):
        try:
            from app.utils.adb_manager import ADBManager
            from ..core.engines.newsec_engine import NewsecEngine
            return NewsecEngine(ADBManager())
        except Exception:
            self._log.erro('Servi├ºo de comunica├º├úo indispon├¡vel.')
    def _dns_on_test(self):
        hostname = self._dns_input.text().strip()
        if not hostname:
            self._lbl_dns_status.setText('Digite um hostname DNS.')
            return
        engine = self._dns_get_engine()
        if not engine:
            return
        if self._worker and self._worker.isRunning():
            self._log.aviso('Aguarde a opera├º├úo anterior finalizar.')
            return
        self._dns_set_busy(True)
        self._atualizar_status('DNS ÔÇö Testando...')
        def _tarefa():
            def _cb(tipo, msg):
                self._worker.log_emitido.emit(tipo, msg)
            return engine.dns_test(hostname, _cb)
        self._worker = _WorkerThread(_tarefa)
        self._worker.log_emitido.connect(self._on_newsec_log)
        self._worker.finalizado.connect(self._on_dns_done)
        self._worker.start()
    def _dns_on_apply(self):
        hostname = self._dns_input.text().strip()
        if not hostname:
            self._lbl_dns_status.setText('Digite um hostname DNS.')
            return
        resp = QMessageBox.question(self, 'DNS Manager', 'Aplicar DNS no dispositivo?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        engine = self._dns_get_engine()
        if not engine:
            return
        if self._worker and self._worker.isRunning():
            self._log.aviso('Aguarde a opera├º├úo anterior finalizar.')
            return
        self._dns_set_busy(True)
        self._atualizar_status('DNS ÔÇö Aplicando...')
        def _tarefa():
            def _cb(tipo, msg):
                self._worker.log_emitido.emit(tipo, msg)
            return engine.dns_apply(hostname, _cb)
        self._worker = _WorkerThread(_tarefa)
        self._worker.log_emitido.connect(self._on_newsec_log)
        self._worker.finalizado.connect(self._on_dns_done)
        self._worker.start()
    def _dns_on_remove(self):
        resp = QMessageBox.question(self, 'DNS Manager', 'Remover DNS privado do dispositivo?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        engine = self._dns_get_engine()
        if not engine:
            return
        if self._worker and self._worker.isRunning():
            self._log.aviso('Aguarde a opera├º├úo anterior finalizar.')
            return
        self._dns_set_busy(True)
        self._atualizar_status('DNS ÔÇö Removendo...')
        def _tarefa():
            def _cb(tipo, msg):
                self._worker.log_emitido.emit(tipo, msg)
            return engine.dns_remove(_cb)
        self._worker = _WorkerThread(_tarefa)
        self._worker.log_emitido.connect(self._on_newsec_log)
        self._worker.finalizado.connect(self._on_dns_done)
        self._worker.start()
    def _on_dns_done(self, sucesso: bool, mensagem: str):
        self._dns_set_busy(False)
        if sucesso:
            self._atualizar_status('DNS ÔÇö Conclu├¡do')
            self._lbl_dns_status.setText(mensagem)
            return
        self._atualizar_status('DNS ÔÇö Falha')
        self._lbl_dns_status.setText(mensagem)
    def _ler_region_lock(self):
        if not self._engine_disponivel(ProinfoEngine, 'proinfo'):
            return
        if not self._validar_ou_avisar(Validador.validar_proinfo):
            return
        try:
            self._log.separador()
            self._log.info('Lendo informa├º├Áes da parti├º├úo proinfo...')
            info = ProinfoEngine.ler_info(self._arquivo_selecionado)
            status = ProinfoEngine.ler_status(self._arquivo_selecionado)
            self._lbl_modelo.setText(f'Modelo: {info.get('modelo') or 'ÔÇö'}')
            self._lbl_firmware.setText(f'Firmware: {info.get('build') or 'ÔÇö'}')
            self._lbl_status_info.setText(f'Status: {status}')
            if info.get('modelo'):
                self._log.info(f'Modelo: {info['modelo']}')
            if info.get('firmware'):
                self._log.info(f'Firmware: {info['firmware']}')
            if info.get('build'):
                self._log.info(f'Build: {info['build']}')
            if status == 'BLOQUEADO':
                self._log.aviso(f'Region Lock: {status}')
            elif status == 'DESBLOQUEADO':
                self._log.sucesso(f'Region Lock: {status}')
            else:
                self._log.info(f'Region Lock: {status}')
            self._log.separador()
            self._atualizar_status('Leitura proinfo conclu├¡da')
            return
        except Exception:
            self._log.erro('Falha ao ler informa├º├Áes da parti├º├úo.')
    def _aplicar_region_lock(self):
        if not self._engine_disponivel(ProinfoEngine, 'proinfo'):
            return
        if not self._validar_ou_avisar(Validador.validar_proinfo, estrito=True):
            return
        if not self._confirmar_com_backup('Region Lock'):
            return
        self._executar_em_thread('Region Lock', ProinfoEngine.aplicar_patch)
    def _ler_payjoy(self):
        if not self._engine_disponivel(OeminfoEngine, 'oeminfo'):
            return
        if not self._validar_ou_avisar(Validador.validar_oeminfo):
            return
        try:
            self._log.separador()
            self._log.info('Lendo informa├º├Áes da parti├º├úo oeminfo...')
            info = OeminfoEngine.ler_info(self._arquivo_selecionado)
            status = OeminfoEngine.ler_status(self._arquivo_selecionado)
            self._lbl_modelo.setText('Modelo: Huawei / Honor (oeminfo)')
            self._lbl_firmware.setText('Tipo: PYJ / UserLock')
            self._lbl_status_info.setText(f'Status: {status}')
            tamanho = info.get('tamanho')
            if tamanho:
                self._log.info(f'Tamanho: {self._formatar_tamanho(tamanho)}')
            if 'ATIVO' in status:
                self._log.aviso(f'Status: {status}')
            elif 'DESBLOQUEADO' in status:
                self._log.sucesso(f'Status: {status}')
            else:
                self._log.info(f'Status: {status}')
            self._log.separador()
            self._atualizar_status('Leitura oeminfo conclu├¡da')
            return
        except Exception:
            self._log.erro('Falha ao ler informa├º├Áes da parti├º├úo.')
    def _aplicar_payjoy(self):
        if not self._engine_disponivel(OeminfoEngine, 'oeminfo'):
            return
        if not self._validar_ou_avisar(Validador.validar_oeminfo, estrito=True):
            return
        if not self._confirmar_com_backup('PYJ / UserLock'):
            return
        self._executar_em_thread('PYJ / UserLock', OeminfoEngine.aplicar_patch_completo)
    def _ler_mi_account(self):
        if not self._engine_disponivel(PersistEngine, 'persist'):
            return
        if not self._validar_ou_avisar(Validador.validar_persist):
            return
        try:
            self._log.separador()
            self._log.info('Lendo informa├º├Áes da parti├º├úo persist...')
            info = PersistEngine.ler_info(self._arquivo_selecionado)
            status = PersistEngine.ler_status(self._arquivo_selecionado)
            self._lbl_modelo.setText('Modelo: Xiaomi (persist)')
            self._lbl_firmware.setText(f'Conta: {info.get('email') or 'ÔÇö'}')
            self._lbl_status_info.setText(f'Status: {status}')
            if info.get('email'):
                self._log.info(f'Conta vinculada: {info['email']}')
            if info.get('user_id'):
                self._log.info(f'User ID: {info['user_id']}')
            if info.get('display_id'):
                self._log.info(f'Display ID: {info['display_id']}')
            if info.get('versao_fds'):
                self._log.info(f'Vers├úo FDS: {info['versao_fds']}')
            if 'ATIVO' in status:
                self._log.aviso(f'Mi Account: {status}')
            elif 'REMOVIDO' in status:
                self._log.sucesso(f'Mi Account: {status}')
            else:
                self._log.info(f'Mi Account: {status}')
            self._log.separador()
            self._atualizar_status('Leitura persist conclu├¡da')
            return
        except Exception:
            self._log.erro('Falha ao ler informa├º├Áes da parti├º├úo.')
    def _aplicar_mi_account(self):
        if not self._engine_disponivel(PersistEngine, 'persist'):
            return
        if not self._validar_ou_avisar(Validador.validar_persist):
            return
        if not self._confirmar_com_backup('Mi Account'):
            return
        self._executar_em_thread('Mi Account', PersistEngine.aplicar_patch)
    def _ler_simlock(self):
        if not self._engine_disponivel(Protect1Engine, 'protect1'):
            return
        if not self._validar_ou_avisar(Validador.validar_protect1):
            return
        if self._worker and self._worker.isRunning():
            self._log.aviso('Aguarde a opera├º├úo anterior finalizar.')
            return
        self._habilitar_operacoes(False)
        self._atualizar_status('Lendo parti├º├úo protect1...')
        self._log.separador()
        self._log.info('Lendo informa├º├Áes da parti├º├úo protect1...')
        self._worker = _WorkerThread(self._executar_leitura_simlock, self._arquivo_selecionado)
        self._worker.dados_prontos.connect(self._exibir_info_simlock)
        self._worker.finalizado.connect((lambda ok, msg: self._operacao_finalizada(ok, msg, 'Leitor SIM Lock')))
        self._worker.start()
    @staticmethod
    def _executar_leitura_simlock(caminho: str) -> tuple:
        info = Protect1Engine.ler_info(caminho)
        if info.get('erro'):
            return False, info['erro']
        info['status'] = Protect1Engine.ler_status(caminho)
        return True, 'Leitura conclu├¡da', info
    def _exibir_info_simlock(self, info: dict):
        status = info.get('status', 'DESCONHECIDO')
        self._lbl_modelo.setText('Modelo: MediaTek (protect1)')
        self._lbl_firmware.setText(f'Inodes: {info.get('inodes', 0)} | Blocos com dados: {info.get('blocos_dados', 0)}')
        self._lbl_status_info.setText(f'Status: {status}')
        self._log.info(f'Inodes: {info.get('inodes', 0)}')
        self._log.info(f'Blocos totais: {info.get('blocks', 0)}')
        self._log.info(f'Blocos com dados: {info.get('blocos_dados', 0)}')
        self._log.info(f'Block size: {info.get('block_size', 0)} bytes')
        self._log.info(f'Labels SELinux: {info.get('labels_selinux', 0)}')
        self._log.info(f'Mount point: {'Presente' if info.get('mount_point') else 'Ausente'}')
        if status == 'BLOQUEADO':
            self._log.aviso(f'SIM Lock: {status}')
            return
        if status == 'DESBLOQUEADO':
            self._log.sucesso(f'SIM Lock: {status}')
            return
        self._log.info(f'SIM Lock: {status}')
    def _aplicar_simlock(self):
        if not self._engine_disponivel(Protect1Engine, 'protect1'):
            return
        if not self._validar_ou_avisar(Validador.validar_protect1, estrito=True):
            return
        info = Protect1Engine.ler_info(self._arquivo_selecionado)
        status = Protect1Engine.ler_status(self._arquivo_selecionado)
        self._log.separador()
        self._log.aviso('ÔÜá OPERA├ç├âO DESTRUTIVA ÔÇö Substitui├º├úo completa do filesystem')
        self._log.info(f'Status atual: {status}')
        self._log.info(f'Inodes: {info.get('inodes', 0)} | Labels: {info.get('labels_selinux', 0)}')
        if not self._confirmar_com_backup('SIM Lock (protect1)'):
            return
        self._executar_em_thread('SIM Lock', Protect1Engine.aplicar_patch)
    def _ler_mdm(self):
        if not self._engine_disponivel(MiscdataEngine, 'miscdata'):
            return
        if not self._validar_ou_avisar(Validador.validar_miscdata):
            return
        try:
            self._log.separador()
            self._log.info('Lendo informa├º├Áes da parti├º├úo miscdata...')
            info = MiscdataEngine.ler_info(self._arquivo_selecionado)
            status = MiscdataEngine.ler_status(self._arquivo_selecionado)
            self._lbl_modelo.setText(f'Plataforma: {info.get('plataforma') or 'ÔÇö'}')
            self._lbl_firmware.setText(f'Serial: {info.get('serial') or 'ÔÇö'}')
            cal = info.get('calibracao')
            self._lbl_status_info.setText(f'Status: {status}')
            self._log.info(f'Plataforma: {info.get('plataforma') or 'ÔÇö'}')
            if info.get('serial'):
                self._log.info(f'Serial: {info['serial']}')
            if cal:
                self._log.info(f'Calibra├º├úo: {cal}')
            if status == 'MDM ATIVO':
                self._log.aviso(f'MDM: {status}')
            elif status == 'DESBLOQUEADO':
                self._log.sucesso(f'MDM: {status}')
            else:
                self._log.info(f'MDM: {status}')
            tam_mb = (info.get('tamanho') or 0) / 1048576
            self._log.info(f'Tamanho: {tam_mb:.1f} MB')
            self._log.separador()
            self._atualizar_status('Leitura miscdata conclu├¡da')
            return
        except Exception:
            self._log.erro('Falha ao ler informa├º├Áes da parti├º├úo.')
    def _aplicar_mdm(self):
        if not self._engine_disponivel(MiscdataEngine, 'miscdata'):
            return
        if not self._validar_ou_avisar(Validador.validar_miscdata):
            return
        status = MiscdataEngine.ler_status(self._arquivo_selecionado)
        self._log.separador()
        self._log.info(f'Status atual: {status}')
        if not self._confirmar_com_backup('MDM Bypass (miscdata)'):
            return
        self._executar_em_thread('MDM Bypass', MiscdataEngine.aplicar_patch)
    def _ler_payj_spd(self):
        if not self._engine_disponivel(MiscdataEngine, 'miscdata'):
            return
        if not self._validar_ou_avisar(Validador.validar_miscdata):
            return
        try:
            self._log.separador()
            self._log.info('Lendo informa├º├Áes da parti├º├úo miscdata...')
            info = MiscdataEngine.ler_info(self._arquivo_selecionado)
            status_pj = MiscdataEngine.ler_status_pj(self._arquivo_selecionado)
            self._lbl_modelo.setText(f'Plataforma: {info.get('plataforma') or 'ÔÇö'}')
            self._lbl_firmware.setText(f'PYJ: {status_pj}')
            self._lbl_status_info.setText(f'Status: {status_pj}')
            self._log.info(f'Plataforma: {info.get('plataforma') or 'ÔÇö'}')
            if info.get('serial'):
                self._log.info(f'Serial: {info['serial']}')
            cal = info.get('calibracao')
            if cal:
                self._log.info(f'Calibra├º├úo: {cal}')
            tam = info.get('tamanho') or 0
            self._log.info(f'Tamanho: {tam / 1048576:.1f} MB')
            if status_pj == 'NAO PROCESSADO':
                self._log.aviso('PYJ: Parti├º├úo n├úo processada')
            elif status_pj == 'PROCESSADO':
                self._log.sucesso('PYJ: Parti├º├úo j├í processada')
            else:
                self._log.info(f'PYJ: {status_pj}')
            self._log.separador()
            self._log.info('Incompat├¡vel com: Note 70 e C71. Testado em: Note 50 e outros Realme SPD.')
            self._log.separador()
            self._atualizar_status('Leitura PYJ conclu├¡da')
            return
        except Exception:
            self._log.erro('Falha ao ler informa├º├Áes da parti├º├úo.')
    def _aplicar_payj_spd(self):
        if not self._engine_disponivel(MiscdataEngine, 'miscdata'):
            return
        if not self._validar_ou_avisar(Validador.validar_miscdata):
            return
        status_pj = MiscdataEngine.ler_status_pj(self._arquivo_selecionado)
        self._log.separador()
        self._log.info(f'Status atual: {status_pj}')
        if status_pj == 'PROCESSADO':
            self._log.sucesso('Parti├º├úo j├í processada. Nenhuma a├º├úo necess├íria.')
            return
        if not self._confirmar_payj_spd():
            return
        self._executar_em_thread('PYJ Bypass SPD', MiscdataEngine.aplicar_bypass_pj)
    def _confirmar_payj_spd(self) -> bool:
        backup_ok = self._criar_backup_automatico()
        if not backup_ok:
            QMessageBox.critical(self, 'Backup Obrigat├│rio', 'N├úo foi poss├¡vel criar o backup de seguran├ºa.\n\nA opera├º├úo foi cancelada automaticamente.\nVerifique permiss├Áes e espa├ºo em disco.')
            self._log.erro('Opera├º├úo bloqueada: backup obrigat├│rio falhou.')
            return False
        resposta = QMessageBox.warning(self, 'Confirmar: PYJ Bypass SPD', 'ATEN├ç├âO: Esta opera├º├úo SUBSTITUI TODO o conte├║do da miscdata.\n\nIncompat├¡vel com: Realme Note 70 e C71\nTestado em: Note 50 e outros Realme SPD (patch maio/2026)\n\nINSTRU├ç├òES P├ôS-GRAVA├ç├âO:\n1. Grave a miscdata modificada no dispositivo\n2. Apague (erase) persist e userdata\n3. Desative atualiza├º├Áes OTA ap├│s o boot\n\nEM CASO DE BRICK:\nÔÇó Restaure a miscdata original (backup criado)\nÔÇó Formate userdata e persist novamente\n\nTECH UNION SOLUTIONS n├úo se responsabiliza por bricks.\nUm backup j├í foi criado automaticamente.\n\nDeseja aplicar a modifica├º├úo?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resposta != QMessageBox.Yes:
            self._log.info('Opera├º├úo cancelada pelo usu├írio.')
            return False
        return True
    def _ler_rguard(self):
        if not self._engine_disponivel(MiscdataEngine, 'miscdata'):
            return
        if not self._validar_ou_avisar(Validador.validar_miscdata):
            return
        try:
            self._log.separador()
            self._log.info('Lendo informa├º├Áes da parti├º├úo miscdata...')
            info = MiscdataEngine.ler_info(self._arquivo_selecionado)
            status_rg = MiscdataEngine.ler_status_rg(self._arquivo_selecionado)
            self._lbl_modelo.setText(f'Plataforma: {info.get('plataforma') or 'ÔÇö'}')
            self._lbl_firmware.setText(f'r-guard: {status_rg}')
            self._lbl_status_info.setText(f'Status: {status_rg}')
            self._log.info(f'Plataforma: {info.get('plataforma') or 'ÔÇö'}')
            if info.get('serial'):
                self._log.info(f'Serial: {info['serial']}')
            cal = info.get('calibracao')
            if cal:
                self._log.info(f'Calibra├º├úo: {cal}')
            tam = info.get('tamanho') or 0
            self._log.info(f'Tamanho: {tam / 1048576:.1f} MB')
            if status_rg == 'r-guard ATIVO':
                self._log.aviso('r-guard: ATIVO ÔÇö verifica├º├úo de seguran├ºa habilitada')
            elif status_rg == 'r-guard REMOVIDO':
                self._log.sucesso('r-guard: REMOVIDO')
            else:
                self._log.info(f'r-guard: {status_rg}')
            self._log.separador()
            self._log.info('Testado em: Note 60, Note 60x e outros Realme SPD (maio/2026).')
            self._log.separador()
            self._atualizar_status('Leitura r-guard conclu├¡da')
            return
        except Exception:
            self._log.erro('Falha ao ler informa├º├Áes da parti├º├úo.')
    def _aplicar_rguard(self):
        if not self._engine_disponivel(MiscdataEngine, 'miscdata'):
            return
        if not self._validar_ou_avisar(Validador.validar_miscdata):
            return
        status_rg = MiscdataEngine.ler_status_rg(self._arquivo_selecionado)
        self._log.separador()
        self._log.info(f'Status atual: {status_rg}')
        if status_rg == 'r-guard REMOVIDO':
            self._log.sucesso('r-guard j├í removido. Nenhuma a├º├úo necess├íria.')
            return
        if not self._confirmar_com_backup('r-guard (miscdata)'):
            return
        self._executar_em_thread('r-guard', MiscdataEngine.aplicar_rguard)
    def _ler_oplus(self):
        if not self._engine_disponivel(OplusEngine, 'oplus'):
            return
        if not self._validar_ou_avisar(Validador.validar_oplusreserve2):
            return
        if self._worker and self._worker.isRunning():
            self._log.aviso('Aguarde a opera├º├úo anterior finalizar.')
            return
        self._habilitar_operacoes(False)
        self._atualizar_status('Lendo parti├º├úo oplusreserve2...')
        self._log.separador()
        self._log.info('Iniciando leitura de PCB e Firmware...')
        self._worker = _WorkerThread(self._executar_leitura_pcb, self._arquivo_selecionado)
        self._worker.dados_prontos.connect(self._exibir_info_oplus)
        self._worker.finalizado.connect((lambda ok, msg: self._operacao_finalizada(ok, msg, 'Leitor PCB / FW')))
        self._worker.start()
    @staticmethod
    def _executar_leitura_pcb(caminho: str) -> tuple:
        info = OplusEngine.ler_info(caminho)
        if info.get('erro'):
            return False, info['erro']
        return True, 'Leitura conclu├¡da', info
    def _exibir_info_oplus(self, info: dict):
        plat = info.get('plataforma') or 'ÔÇö'
        self._lbl_modelo.setText(f'Project: {info.get('nProject') or 'ÔÇö'}')
        self._lbl_firmware.setText(f'PCB: {info.get('nPCB') or 'ÔÇö'}')
        self._lbl_status_info.setText(f'Plataforma: {plat}')
        self._log.info(f'ÔöÇÔöÇ IDENTIFICA├ç├âO CDT ({plat}) ÔöÇÔöÇ')
        self._log.info(f'nProject: {info.get('nProject') or 'ÔÇö'}')
        self._log.info(f'nPCB: {info.get('nPCB') or 'ÔÇö'}')
        self._log.info(f'nRF: {info.get('nRF') or 'ÔÇö'}')
        self._log.info(f'nPrj: {info.get('nPrj') or 'ÔÇö'}')
        self._log.info(f'nDtsi: {info.get('nDtsi') or 'ÔÇö'}')
        self._log.info(f'nAudio: {info.get('nAudio') or 'ÔÇö'}')
        if info.get('q_board'):
            self._log.info(f'Board: {info['q_board']}')
        if info.get('q_pcb_label'):
            self._log.info(f'PCB Label: {info['q_pcb_label']}')
        eng_v = info.get('eng_version')
        conf = info.get('confidential')
        if eng_v is not None:
            self._log.info(f'Engenharia: {'Sim' if eng_v != '0' else 'Release'}')
        if conf is not None:
            self._log.info(f'Confidencial: {'Sim' if conf != '0' else 'P├║blico'}')
        builds = info.get('rom_builds', [])
        if builds:
            self._log.separador()
            self._log.info(f'ÔöÇÔöÇ FIRMWARE ({len(builds)} vers├úo/├Áes) ÔöÇÔöÇ')
            for b in sorted(set(builds)):
                self._log.info(f'  {b}')
        if info.get('rom_version'):
            self._log.info(f'Vers├úo ROM: {info['rom_version']}')
        if info.get('fab_nv') or info.get('fab_tool'):
            self._log.separador()
            self._log.info('ÔöÇÔöÇ DADOS DE F├üBRICA ÔöÇÔöÇ')
            if info.get('fab_nv'):
                self._log.info(f'NV: {info['fab_nv']}')
            if info.get('fab_tool'):
                self._log.info(f'Ferramenta: {info['fab_tool']}')
            if info.get('fab_mac'):
                self._log.info(f'MAC: {info['fab_mac']}')
            if info.get('fab_ip'):
                self._log.info(f'IP grava├º├úo: {info['fab_ip']}')
            if info.get('fab_time'):
                self._log.info(f'Data grava├º├úo: {info['fab_time']}')
    def _criar_backup_automatico(self) -> bool:
        try:
            if not self._arquivo_selecionado:
                return False
            if not self._backup_mgr.pronto:
                self._log.erro('Pasta de backups inacess├¡vel.')
                return False
            nome_bk = self._backup_mgr.criar_backup(self._arquivo_selecionado, 'auto')
            if nome_bk:
                self._backup_path = os.path.join(self._backup_mgr.pasta, nome_bk)
                self._log.sucesso(f'Backup criado: {nome_bk}')
                return True
            self._log.erro('Falha ao criar backup ÔÇö verifique espa├ºo em disco.')
            return False
        except Exception:
            self._log.erro('Falha ao criar backup autom├ítico.')
            return False
    def _fazer_backup(self):
        if not self._arquivo_selecionado:
            self._log.aviso('Nenhum arquivo para backup.')
            return
        self._criar_backup_automatico()
        self._atualizar_status('Backup manual criado')
    def _reverter_backup(self):
        if not self._backup_path or not os.path.isfile(self._backup_path):
            self._log.erro('Nenhum backup dispon├¡vel para revers├úo.')
            return
        try:
            resposta = QMessageBox.question(self, 'Reverter Backup', 'Deseja reverter o arquivo para o ├║ltimo backup?\nA vers├úo atual ser├í sobrescrita.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if resposta == QMessageBox.Yes:
                shutil.copy2(self._backup_path, self._arquivo_selecionado)
                self._log.sucesso('Arquivo revertido com sucesso.')
                self._btn_reverter.setVisible(False)
                self._atualizar_status('Revertido para backup')
                self._auto_detectar()
                return
        except Exception:
            self._log.erro('Falha ao reverter backup.')
    def _limpar_log(self):
        self._log.limpar()
        self._log.info('Log limpo.')
    def _exportar_log(self):
        try:
            dir_inicial = str(Path.home() / 'Documents')
            if not os.path.isdir(dir_inicial):
                dir_inicial = str(Path.home())
            caminho, _ = QFileDialog.getSaveFileName(self, 'Exportar Log', os.path.join(dir_inicial, f'hxd_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt'), 'Texto (*.txt);;Todos (*.*)')
            if caminho:
                conteudo = self._log.toPlainText()
                with open(caminho, 'w', encoding='utf-8') as f:
                    f.write(conteudo)
                self._log.sucesso('Log exportado com sucesso.')
                return
        except Exception:
            self._log.erro('Falha ao exportar log.')
    def _habilitar_operacoes(self, estado: bool):
        for btn in self._botoes_operacao:
            btn.setEnabled(estado)
    def _atualizar_status(self, texto: str):
        self._lbl_status.setText(f'Status: {texto}')
    def _exibir_boas_vindas(self):
        self._log.separador()
        self._log.info(f'TECH UNION SOLUTIONS ÔÇö Partition Editor {_VERSAO} Ferramenta para edi├º├úo de parti├º├Áes e prote├º├úo de smartphones.')
        self._log.aviso(_DISCLAIMER)
        self._log.separador()
        self._log.aviso(_LEGALIDADE)
        self._log.separador()
        self._log.separador()
        self._log.info('Pronto para opera├º├úo')
    @staticmethod
    def _formatar_tamanho(bytes_val: int) -> str:
        for unidade in ('B', 'KB', 'MB', 'GB'):
            if bytes_val < 1024:
                return f'{bytes_val:.1f} {unidade}'
            bytes_val /= 1024
        return f'{bytes_val:.1f} TB'
