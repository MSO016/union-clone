from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QFrame, QGridLayout, QMenuBar, QAction, QMessageBox, QApplication, QDialog, QProgressDialog, QSplashScreen)
from PyQt5.QtCore import (Qt, QCoreApplication, QTimer, QSize, QSettings, QThread, pyqtSignal)
from PyQt5.QtGui import (QIcon, QPixmap, QColor, QPainter)
from app.views.login_window import LoginWindow
from app.views.service_order_window import ServiceOrderWindow
from app.utils.translation_manager import TranslationManager
from app.views.language_selector import LanguageSelectorDialog
from app.utils.window_protection import protect_window_from_capture_extended
import sqlite3
import os
from ..utils.path_manager import PathManager
from datetime import datetime
import pymysql
import time
from app.utils._app_cfg import db_config, REFS
from app.utils._security_crypto import encrypt_blob
from app.utils._ci_sentinel import SectorSentinel
import webbrowser
try:
    from app.utils.web_view_widget import is_webengine_available, get_web_view_manager
    NAVEGADOR_INTERNO_DISPONIVEL = True
except ImportError:
    NAVEGADOR_INTERNO_DISPONIVEL = False
    is_webengine_available = lambda: False
    get_web_view_manager = lambda: None
class PopupAnuncioDialog(QDialog):
    def __init__(self, anuncio_data, parent=None):
        super().__init__(parent)
        self.anuncio_data = anuncio_data
        self.parent = parent
        self.tempo_restante = 15
        self.is_admin = parent.is_admin if hasattr(parent, 'is_admin') else False
        self.setup_ui()
        self.setup_timer()
        if not self.pode_gravar_tela():
            protect_window_from_capture_extended(self, True)
    def pode_gravar_tela(self):
        '''Verifica se o usu├írio pode gravar a tela baseado no dom├¡nio ou se ├® admin'''
        from app.utils.screen_protection_config import pode_gravar_tela as config_pode_gravar
        return config_pode_gravar(is_admin=self.is_admin, user_domain=getattr(self.parent, 'user_domain', None) if self.parent else None)
    def setup_ui(self):
        '''Configura popup ULTRA MINIMALISTA - s├│ a imagem clic├ível com X para fechar'''
        self._imagem_carregada = False
        self.setWindowTitle('')
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setModal(True)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        if self.anuncio_data.get('arquivo_blob') and len(self.anuncio_data['arquivo_blob']) > 100:
            try:
                self.imagem_label = QLabel()
                self.imagem_label.setStyleSheet('\n                    QLabel {\n                        border: none;\n                        background-color: transparent;\n                        padding: 0px;\n                        margin: 0px;\n                    }\n                    QLabel:hover {\n                        opacity: 0.95;\n                    }\n                ')
                pixmap = QPixmap()
                if pixmap.loadFromData(self.anuncio_data['arquivo_blob']):
                    screen = QApplication.primaryScreen().geometry()
                    screen_width = screen.width()
                    screen_height = screen.height()
                    max_width = int(screen_width * 0.7)
                    max_height = int(screen_height * 0.7)
                    scaled_pixmap = pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.imagem_label.setPixmap(scaled_pixmap)
                    self.imagem_label.setAlignment(Qt.AlignCenter)
                    self.setFixedSize(scaled_pixmap.size())
                    self.move((screen_width - scaled_pixmap.width()) // 2, (screen_height - scaled_pixmap.height()) // 2)
                    self.imagem_label.mousePressEvent = self.clicar_na_imagem
                    self.imagem_label.setCursor(Qt.PointingHandCursor)
                    if self.anuncio_data.get('link'):
                        self.imagem_label.setToolTip('Clique para aproveitar esta oferta')
                    else:
                        self.imagem_label.setToolTip('Clique para fechar')
                    image_container = QWidget()
                    image_container.setFixedSize(scaled_pixmap.size())
                    image_container_layout = QVBoxLayout(image_container)
                    image_container_layout.setContentsMargins(0, 0, 0, 0)
                    image_container_layout.setSpacing(0)
                    image_container_layout.addWidget(self.imagem_label)
                    close_btn = QPushButton('Ô£ò')
                    close_btn.setFixedSize(30, 30)
                    close_btn.setStyleSheet('\n                        QPushButton {\n                            background-color: rgba(255, 0, 0, 0.8);\n                            color: white;\n                            border: none;\n                            border-radius: 15px;\n                            font-size: 16px;\n                            font-weight: bold;\n                        }\n                        QPushButton:hover {\n                            background-color: rgba(255, 0, 0, 1.0);\n                        }\n                        QPushButton:pressed {\n                            background-color: rgba(200, 0, 0, 1.0);\n                        }\n                    ')
                    close_btn.setCursor(Qt.PointingHandCursor)
                    close_btn.setToolTip('Fechar')
                    close_btn.clicked.connect(self.close)
                    close_btn.setParent(image_container)
                    close_btn.move(scaled_pixmap.width() - 35, 5)
                    close_btn.raise_()
                    main_layout.addWidget(image_container)
                    self._imagem_carregada = True
                    return
            except Exception as e:
                print(f'Erro ao carregar banner: {e}')
            return
        print('Popup sem imagem v├ílida - n├úo ser├í exibido')
    def setup_timer(self):
        '''Configura timer silencioso para fechamento autom├ítico'''
        self.timer = QTimer()
        self.timer.timeout.connect(self.atualizar_tempo_silencioso)
        self.timer.start(1000)
    def atualizar_tempo_silencioso(self):
        '''Timer silencioso - apenas fecha ap├│s 15 segundos'''
        self.tempo_restante -= 1
        if self.tempo_restante <= 0:
            self.timer.stop()
            self.close()
    def clicar_na_imagem(self, event):
        '''Clique na imagem vai direto para o link ou fecha o popup'''
        try:
            if self.anuncio_data.get('link'):
                self.abrir_link()
                return
            self.close()
            return
        except Exception as e:
            print(f'Erro ao processar clique na imagem: {str(e)}')
            self.close()
    def abrir_link(self):
        '''Abre o link da oferta no navegador'''
        try:
            webbrowser.open(self.anuncio_data['link'])
            if self.anuncio_data.get('id') and hasattr(self.parent, 'registrar_click_popup'):
                self.parent.registrar_click_popup(self.anuncio_data['id'])
            QMessageBox.information(self, 'Oferta Acessada', f'Sua oferta especial foi aberta no navegador.\n\nDica: n├úo perca tempo ÔÇö ofertas especiais s├úo por tempo limitado.\n\nLink: {self.anuncio_data['link']}')
            self.close()
            return
        except Exception as e:
            QMessageBox.warning(self, 'Ops! Algo deu errado', f'N├úo foi poss├¡vel abrir automaticamente.\n\nCopie este link e cole no seu navegador:\n{self.anuncio_data['link']}\n\nErro t├®cnico: {str(e)}')
    def closeEvent(self, event):
        '''Para o timer ao fechar'''
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
        super().closeEvent(event)
_LIC_HARD_BLOCK_MAP = {'SUSPENDED': 'LIC-201', 'BANNED': 'LIC-202', 'PRODUCT_SCOPE_MISMATCH': 'LIC-206', 'POLICY_SCOPE_MISMATCH': 'LIC-207'}
def _compute_license_action(meta_code, meta_valid):
    '''Decide.'''
    code = (meta_code or '').upper()
    if meta_valid and code == 'VALID':
        return ('OK', None)
    if code in _LIC_HARD_BLOCK_MAP:
        return 'BLOCK', _LIC_HARD_BLOCK_MAP[code]
    if code == 'EXPIRED':
        return ('BLOCK_GRACE', 'LIC-203')
    if code == 'OVERDUE':
        return ('WARN', 'LIC-208')
    return ('FAIL_OPEN', None)
class _LicenseRevalidator(QThread):
    '''Worker.'''
    result_ready = pyqtSignal(dict)
    network_error = pyqtSignal(str)
    def __init__(self, email, key, api_url, account_id, product_id, product_token, parent=None, machine_id=None, fingerprint=None):
        super().__init__(parent)
        self._email = email
        self._key = key
        self._api_url = api_url
        self._account_id = account_id
        self._product_id = product_id
        self._product_token = product_token
        self._machine_id = machine_id
        self._fingerprint = fingerprint
        self._stop = False
    def request_stop(self):
        self._stop = True
    def run(self):
        try:
            if self._stop:
                return
            import requests
            url = f'{self._api_url}/accounts/{self._account_id}/licenses/actions/validate-key'
            headers = {'Content-Type': 'application/vnd.api+json', 'Accept': 'application/vnd.api+json', 'Authorization': f'Bearer {self._product_token}'}
            scope = {'user': self._email}
            if self._machine_id:
                scope['machine'] = self._machine_id
            if self._fingerprint:
                scope['fingerprint'] = self._fingerprint
            payload = {'meta': {'key': self._key, 'scope': scope}}
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            if self._stop:
                return
            if resp.status_code != 200:
                self.network_error.emit(f'http:{resp.status_code}')
                return
            data = resp.json() or {}
            attrs = (data.get('data') or {}).get('attributes', {}) or {}
            meta = data.get('meta', {}) or {}
            payload_out = {'id': (data.get('data') or {}).get('id'), 'key': attrs.get('key'), 'expiry': attrs.get('expiry'), 'status': attrs.get('status'), 'suspended': attrs.get('suspended', False), 'meta_code': meta.get('code', 'VALID'), 'meta_valid': bool(meta.get('valid', True))}
            try:
                from app.utils._ci_sentinel import fetch_mysql_user_status
                payload_out['_mysql_status'] = fetch_mysql_user_status(self._email)
            except Exception:
                pass
            else:
                self.result_ready.emit(payload_out)
        except Exception as e:
            if not self._stop:
                self.network_error.emit('exc')
class MainWindow(QMainWindow):
    def __init__(self, user_id=None, is_admin=False, user_domain=None, user_email=None, fullscreen=True, license_data=None, validation_cache=None, license_key=None):
        super().__init__()
        icon = QIcon(PathManager.get_resource_path('icon.png'))
        self.setWindowIcon(icon)
        splash_pixmap = QPixmap(PathManager.get_resource_path('icon.png'))
        splash_pixmap = splash_pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.splash = QSplashScreen(splash_pixmap)
        self.splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.SplashScreen)
        self.splash.setStyleSheet('\n            QSplashScreen {\n                border: 2px solid #2c3e50;\n                border-radius: 10px;\n                background-color: rgba(255, 255, 255, 240);\n            }\n        ')
        self.splash.show()
        self.translation_manager = TranslationManager.get_instance()
        self.setWindowTitle(self.translation_manager.get_text('system_title'))
        self.setMinimumSize(1200, 700)
        if user_id is None:
            self.close()
            self.login = LoginWindow()
            self.login.show()
            return
        self.user_id = user_id
        self.is_admin = is_admin
        self.user_domain = user_domain
        self.user_email = user_email
        self.fullscreen_mode = fullscreen
        self.license_data = license_data or {}
        self.license_expiry = self.license_data.get('expiry')
        self.is_lifetime_license = self.license_expiry is None
        self._validation_cache = validation_cache
        self._license_key = license_key
        self._lic_machine_id = self.license_data.get('_lic_machine_id')
        self._lic_fingerprint = self.license_data.get('_lic_fingerprint')
        self._lic_worker = None
        self._lic_timer = None
        self._lic_consecutive_invalid = 0
        self._lic_consecutive_offline = 0
        self._lic_blocked = False
        self._ci = SectorSentinel(self)
        try:
            if self._license_key and getattr(REFS, 'LIC_ENFORCE_V3', False):
                self._lic_timer = QTimer(self)
                self._lic_timer.setInterval(REFS.LIC_REVALIDATE_INTERVAL_MS)
                self._lic_timer.timeout.connect(self._on_lic_revalidate_tick)
                self._lic_timer.start()
        except Exception:
            self._lic_timer = None
        self.is_com_user = self.user_domain and self.user_domain.endswith('.com') and not self.user_domain.endswith('.com.br')
        self.is_premium_user = self.is_admin or self.user_domain and self.user_domain.endswith('.com.br')
        _SIDEBAR_DEFAULT = True
        try:
            _ui_settings = QSettings('TechUnion', 'UNION')
            self._use_new_sidebar = bool(_ui_settings.value('ui/dashboard_v2', _SIDEBAR_DEFAULT, type=bool))
        except Exception:
            self._use_new_sidebar = _SIDEBAR_DEFAULT
        self.mostrar_mensagem_splash('Carregando interface...', 'tech_union_logo')
        QApplication.processEvents()
        self.setup_ui()
        self.mostrar_mensagem_splash('Conectando ao banco de dados...', 'database_icon')
        QApplication.processEvents()
        self.conectar_banco()
        if self.fullscreen_mode:
            self.showMaximized()
        else:
            self.center_window()
        if not self.pode_gravar_tela():
            protect_window_from_capture_extended(self, True)
        self.mostrar_mensagem_splash('Sincronizando com o servidor...', 'sync_icon')
        QApplication.processEvents()
        self.iniciar_sincronizacao()
        QTimer.singleShot(3000, self.verificar_popup_propaganda)
        try:
            from app.utils._cfg_probe import set_user_context as _set_ctx
            _set_ctx(user_id=self.user_id, email=self.user_email, machine_id=self._lic_machine_id)
        except Exception:
            pass
        self._guard_timer = None
        try:
            from app.utils._cfg_probe import (get_strike_level, build_strike_message, collect_forensic, self_cleanup)
            if get_strike_level() >= 3:
                info = collect_forensic()
                msg = build_strike_message(3, info)
                QMessageBox.critical(self, 'TECH UNION SOLUTIONS', msg)
            try:
                self_cleanup()
            except Exception:
                pass
            else:
                QApplication.quit()
        except Exception:
            pass
        try:
            self._guard_timer = QTimer(self)
            self._guard_timer.setInterval(10000)
            self._guard_timer.timeout.connect(self._on_guard_tick)
            self._guard_timer.start()
        except Exception:
            self._guard_timer = None
    def _on_lic_revalidate_tick(self):
        try:
            if self._lic_worker is not None and self._lic_worker.isRunning():
                return
            if not self._license_key or not self.user_email:
                return
            self._lic_worker = _LicenseRevalidator(self.user_email, self._license_key, REFS.VK_URL, REFS.VK_ACC, REFS.VK_PRD, REFS.VK_TKN, self, machine_id=self._lic_machine_id, fingerprint=self._lic_fingerprint)
            self._lic_worker.result_ready.connect(self._on_lic_result, Qt.QueuedConnection)
            self._lic_worker.network_error.connect(self._on_lic_network_error, Qt.QueuedConnection)
            self._lic_worker.start()
            return
        except Exception:
            return
    def _on_lic_result(self, payload):
        try:
            if self._lic_blocked:
                return
            self._lic_consecutive_offline = 0
            code = (payload.get('meta_code') or '').upper() or 'VALID'
            valid = bool(payload.get('meta_valid', True))
            action, lic_code = _compute_license_action(code, valid)
            if action == 'OK':
                self._lic_consecutive_invalid = 0
            else:
                self._lic_consecutive_invalid += 1
        except Exception:
            return
        try:
            import logging
            logging.getLogger(__name__).info(f'LIC-300:{code}:{int(valid)}:{self._lic_consecutive_invalid}')
        except Exception:
            pass
        try:
            if action == 'BLOCK':
                self._aplicar_bloqueio_lic(code, lic_code)
                return
            if action == 'BLOCK_GRACE':
                threshold = getattr(REFS, 'LIC_RETRY_BEFORE_BLOCK', 3)
                if self._lic_consecutive_invalid >= threshold:
                    self._aplicar_bloqueio_lic(code, lic_code)
                    return
        except Exception:
            pass
        try:
            try:
                self._ci.on_timer_result(payload)
            except Exception:
                return
        except Exception:
            return
    def _on_lic_network_error(self, _msg):
        try:
            self._lic_consecutive_offline += 1
        except Exception:
            return
        try:
            import logging
            logging.getLogger(__name__).info(f'LIC-400:{self._lic_consecutive_offline}')
        except Exception:
            pass
        try:
            try:
                threshold = getattr(REFS, 'LIC_FAILS_BEFORE_WARN_OFFLINE', 2)
                if self._lic_consecutive_offline >= threshold:
                    self._forcar_logout_offline()
                    return
            except Exception:
                return
        except Exception:
            return
    def _forcar_logout_offline(self):
        try:
            if self._lic_blocked:
                return
            self._lic_blocked = True
            try:
                if self._lic_timer is not None:
                    self._lic_timer.stop()
            except Exception:
                pass
            else:
                QMessageBox.warning(self, 'TECH UNION SOLUTIONS', 'Verifique sua conex├úo com a internet e fa├ºa login novamente.\n\nSe o problema persistir, entre em contato com o suporte.')
                self._fazer_logout_lic()
        except Exception:
            return
    def _build_lic_msg(self, code):
        '''Build.'''
        cu = (code or '').upper()
        if cu == 'EXPIRED':
            return ('Licen├ºa expirada', 'Sua licen├ºa <b>expirou</b>.<br><br>Para continuar utilizando o sistema, ├® necess├írio renovar.<br><br>Voc├¬ ser├í redirecionado para a tela de login.', 'Renovar agora')
        if cu == 'SUSPENDED':
            return ('Acesso suspenso', 'Seu acesso est├í <b>temporariamente suspenso</b>.<br><br>Entre em contato com o suporte para regularizar.', 'Falar com suporte')
        if cu == 'BANNED':
            return ('Acesso indispon├¡vel', 'Seu acesso est├í <b>indispon├¡vel</b>.<br><br>Entre em contato com o suporte.', 'Falar com suporte')
        if cu in ('NO_MACHINE', 'NO_MACHINES'):
            return ('Limite de m├íquinas', 'Limite de m├íquinas <b>excedido</b> para esta licen├ºa.<br><br>Entre em contato com o suporte para liberar.', 'Falar com suporte')
        return ('Licen├ºa indispon├¡vel', 'Sua licen├ºa <b>n├úo p├┤de ser validada</b> neste momento.<br><br>Antes de acionar o suporte, tente:<br>1. <b>Feche e abra</b> o aplicativo;<br>2. <b>Fa├ºa login novamente</b>;<br>3. Verifique sua <b>conex├úo com a internet</b>.<br><br>Se o problema continuar, entre em contato com o suporte.', 'Falar com suporte')
    def _aplicar_bloqueio_lic(self, code, lic_code):
        '''Block.'''
        try:
            if self._lic_blocked:
                return
            self._lic_blocked = True
        except Exception:
            return
        try:
            import logging
            logging.getLogger(__name__).info(f'{lic_code}:{(code or '').upper()}')
        except Exception:
            pass
        try:
            if self._lic_timer is not None:
                self._lic_timer.stop()
        except Exception:
            pass
        try:
            if self._lic_worker is not None and self._lic_worker.isRunning():
                self._lic_worker.request_stop()
        except Exception:
            pass
        try:
            title, body, primary_label = self._build_lic_msg(code)
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Critical)
            box.setWindowTitle(title)
            try:
                box.setTextFormat(Qt.RichText)
            except Exception:
                pass
            else:
                box.setText(body)
                primary_btn = box.addButton(primary_label, QMessageBox.ActionRole)
                support_btn = box.addButton('Suporte (WhatsApp)', QMessageBox.ActionRole)
                exit_btn = box.addButton('Sair', QMessageBox.RejectRole)
                box.exec_()
                clicked = box.clickedButton()
        except Exception:
            return
        try:
            try:
                try:
                    if clicked is primary_btn:
                        cu = (code or '').upper()
                        url = REFS.LIC_RENEW_URL if cu == 'EXPIRED' else REFS.LIC_SUPPORT_WHATSAPP
                        webbrowser.open(url)
                    elif clicked is support_btn:
                        webbrowser.open(REFS.LIC_SUPPORT_WHATSAPP)
                except Exception:
                    try:
                        try:
                            pass
                        except Exception:
                            pass
                    except Exception:
                        return
            except Exception:
                pass
        except Exception:
            return
        self._fazer_logout_lic()
    def _fazer_logout_lic(self):
        '''Logout.'''
        try:
            if hasattr(self, '_guard_timer') and self._guard_timer is not None:
                self._guard_timer.stop()
        except Exception:
            pass
        try:
            if self._lic_timer is not None:
                self._lic_timer.stop()
        except Exception:
            pass
        try:
            if self._lic_worker is not None and self._lic_worker.isRunning():
                self._lic_worker.request_stop()
                self._lic_worker.wait(2000)
        except Exception:
            pass
        try:
            if self._validation_cache is not None:
                self._validation_cache.clear_all_cache_robust(silent=True)
        except Exception:
            pass
        try:
            from app.views.login_window import LoginWindow
            self._lic_login = LoginWindow()
            self._lic_login.show()
        except Exception:
            pass
        try:
            try:
                self.close()
            except Exception:
                return
        except Exception:
            return
    def _on_guard_tick(self):
        '''Verificacao periodica de integridade do ambiente.'''
        try:
            from app.utils._cfg_probe import (scan as _g_scan, has_blocking as _g_blk, is_debugger_attached as _g_dbg, generic_user_message as _g_msg, record_strike, get_strike_level, collect_forensic, emit_strike_event, build_strike_message, self_cleanup)
            detections = _g_scan()
            if _g_blk(detections) or _g_dbg():
                record_strike()
                level = get_strike_level()
            try:
                if self._guard_timer is not None:
                    self._guard_timer.stop()
            except Exception:
                pass
            else:
                if level >= 2:
                    info = collect_forensic()
        except Exception:
            return
    def calcular_dias_restantes(self):
        '''Calcula os dias restantes da licen├ºa'''
        if self.is_lifetime_license:
            return 'Ôê×'
        if not self.license_expiry:
            return 'N/A'
        try:
            from datetime import datetime
            import re
            expiry_str = self.license_expiry
            if 'T' in expiry_str:
                expiry_str = expiry_str.split('T')[0]
            expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
            current_date = datetime.now()
            delta = expiry_date - current_date
            days_remaining = delta.days
            if days_remaining < 0:
                return 'EXPIRADA'
            if days_remaining == 0:
                return 'HOJE'
            return str(days_remaining)
        except Exception as e:
            print(f'Erro ao calcular dias restantes: {e}')
            return 'N/A'
    def obter_saldo_creditos_header(self):
        '''Saldo para o card do header. None = falha visivel (nao R$ 0,00).'''
        try:
            email = getattr(self, 'user_email', None)
            if not email:
                return
            from app.utils.arquivos_manager import ArquivosManager
            return ArquivosManager().consultar_saldo_creditos(email)
        except Exception as e:
            print(f'[header] saldo creditos indisponivel: {type(e).__name__}')
    def atualizar_header_saldo(self):
        '''Atualiza o card do header imediatamente (nao espera o timer de 30 min).'''
        try:
            hsb = getattr(self, '_header_status_bar', None)
            if hsb is not None:
                if hasattr(hsb, 'refresh'):
                    hsb.refresh()
                    return
                return
        except Exception as e:
            print(f'[header] refresh saldo falhou: {type(e).__name__}: {e}')
    def obter_data_expiracao_formatada(self):
        '''Retorna a data de expira├º├úo formatada para exibi├º├úo'''
        if self.is_lifetime_license:
            return 'Licen├ºa Ativa'
        if not self.license_expiry:
            return 'Data n├úo dispon├¡vel'
        try:
            from datetime import datetime
            expiry_str = self.license_expiry
            if 'T' in expiry_str:
                expiry_str = expiry_str.split('T')[0]
            expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
            return expiry_date.strftime('%d/%m/%Y')
        except Exception as e:
            print(f'Erro ao formatar data de expira├º├úo: {e}')
            return 'Data inv├ílida'
    def obter_status_licenca_formatado(self):
        '''Retorna o status da licenca formatado para exibicao.
        Sem emoji: o consumidor unico (perfil_dialog em L5349) exibe em
        um QLabel dentro de tag <b>. As bolinhas emoji causavam quebra
        visual em fontes sem suporte. A cor de contexto e aplicada la.
        '''
        dias_restantes = self.calcular_dias_restantes()
        if dias_restantes == 'Ôê×':
            return 'Licen├ºa Ativa'
        if dias_restantes == 'EXPIRADA':
            return 'Licen├ºa Expirada'
        if dias_restantes == 'HOJE':
            return 'Expira Hoje'
        if dias_restantes.isdigit():
            days = int(dias_restantes)
            return f'{days} dias restantes'
        return 'Status indispon├¡vel'
    def pode_gravar_tela(self):
        '''Verifica se o usu├írio pode gravar a tela baseado no dom├¡nio ou se ├® admin'''
        from app.utils.screen_protection_config import pode_gravar_tela as config_pode_gravar
        return config_pode_gravar(is_admin=self.is_admin, user_domain=getattr(self, 'user_domain', None))
    def mostrar_mensagem_splash(self, mensagem, icon_name=None):
        '''Mostra uma mensagem formatada no splash screen'''
        icon_html = ''
        if icon_name:
            icon_html = '<img src="{}" height="24" width="24" style="vertical-align: middle; margin-right: 10px;">'
        mensagem_formatada = f"\n        <div style='\n            background-color: rgba(52, 152, 219, 0.8); \n            color: white; \n            padding: 15px; \n            border-radius: 5px;\n            font-family: Arial, sans-serif;\n            font-size: 14px;\n            font-weight: bold;\n        '>\n            {icon_html}\n            {mensagem}\n        </div>\n        "
        self.splash.showMessage(mensagem_formatada, Qt.AlignBottom | Qt.AlignHCenter, Qt.white)
    def center_window(self):
        '''Centraliza a janela na tela'''
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
    def conectar_banco(self):
        try:
            self.db_path = PathManager.get_database_path('base.db')
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            self.criar_tabelas_necessarias()
            self.testar_conexao_mysql()
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', 'Erro ao conectar ao banco de dados. Verifique sua conex├úo.')
    def criar_tabelas_necessarias(self):
        '''Cria as tabelas necess├írias se n├úo existirem'''
        try:
            self.cursor.execute('\n                CREATE TABLE IF NOT EXISTS sync_control (\n                    id INTEGER PRIMARY KEY AUTOINCREMENT,\n                    ultima_sincronizacao DATETIME DEFAULT CURRENT_TIMESTAMP,\n                    status VARCHAR(50),\n                    detalhes TEXT,\n                    total_sincronizado INTEGER DEFAULT 0,\n                    erros INTEGER DEFAULT 0,\n                    duracao_segundos INTEGER DEFAULT 0\n                )\n            ')
            self.cursor.execute("\n                CREATE TABLE IF NOT EXISTS solucoes (\n                    id INTEGER PRIMARY KEY,\n                    marca TEXT NOT NULL,\n                    modelo TEXT NOT NULL,\n                    descricao TEXT,\n                    observacoes TEXT,\n                    status TEXT DEFAULT 'ativo',\n                    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,\n                    data_sincronizacao DATETIME,\n                    hash_verificacao TEXT,\n                    versao TEXT,\n                    ultima_modificacao DATETIME,\n                    diagrama_blob BLOB,\n                    imagem_blob BLOB,\n                    diagrama_blob_2 BLOB,\n                    imagem_blob_2 BLOB,\n                    diagrama_blob_3 BLOB,\n                    imagem_blob_3 BLOB\n                )\n            ")
            self.conn.commit()
            return
        except Exception as e:
            print(f'Erro ao criar tabelas: {str(e)}')
    def testar_conexao_mysql(self):
        '''Testa a conex├úo com o MySQL'''
        try:
            self.mysql_conn = pymysql.connect(**db_config(cursorclass=pymysql.cursors.DictCursor, ssl={'ca': None}, ssl_verify_cert=False))
            self.mysql_online = True
            print('Ô£à Conex├úo MySQL estabelecida com sucesso')
            return
        except Exception as e:
            self.mysql_online = False
            print(f'ÔØî Erro ao conectar ao MySQL: {str(e)}')
    def iniciar_sincronizacao(self):
        '''Inicia o timer de sincroniza├º├úo'''
        self.atualizar_barra_atualizacoes([])
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self.animar_texto)
        self.scroll_timer.start(150)
        self.progresso_sync = QProgressDialog('Sincronizando com o servidor...', 'Segundo plano', 0, 100, self)
        self.progresso_sync.setWindowTitle('UNION - Sincroniza├º├úo')
        self.progresso_sync.setWindowModality(Qt.WindowModal)
        self.progresso_sync.setAutoClose(True)
        self.progresso_sync.setMinimumDuration(500)
        self.progresso_sync.setValue(10)
        QApplication.processEvents()
        QTimer.singleShot(100, self.sincronizar_com_progresso)
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.sincronizar_bancos)
        self.sync_timer.start(300000)
    def sincronizar_com_progresso(self):
        '''Executa a sincroniza├º├úo inicial com barra de progresso'''
        tempo_inicial = time.time()
        if not hasattr(self, 'mysql_online') or not self.mysql_online:
            self.progresso_sync.setValue(20)
            QApplication.processEvents()
            self.testar_conexao_mysql()
            if not self.mysql_online:
                self.progresso_sync.cancel()
                self.splash.finish(self)
                self.atualizar_barra_atualizacoes([])
                return
        self.progresso_sync.setValue(40)
        QApplication.processEvents()
        try:
            mysql_conn = self.conectar_mysql()
            if not mysql_conn:
                self.progresso_sync.cancel()
                self.splash.finish(self)
                self.atualizar_barra_atualizacoes([])
                return
            self.progresso_sync.setValue(60)
            QApplication.processEvents()
            mysql_cursor = mysql_conn.cursor()
            mysql_cursor.execute("\n                SELECT id, marca, modelo, descricao, observacoes, status, \n                       data_criacao, ultima_modificacao, hash_verificacao, versao\n                FROM solucoes \n                WHERE status = 'ativo'\n                ORDER BY ultima_modificacao DESC\n            ")
            solucoes_mysql = mysql_cursor.fetchall()
            self.progresso_sync.setValue(70)
            QApplication.processEvents()
            self.cursor.execute('\n                SELECT id, marca, modelo, descricao, observacoes, status,\n                       data_criacao, ultima_modificacao, hash_verificacao, versao\n                FROM solucoes\n                ORDER BY ultima_modificacao DESC\n            ')
            solucoes_sqlite = self.cursor.fetchall()
        except Exception as e:
            print(f'Erro na sincroniza├º├úo: {str(e)}')
            self.mysql_online = False
            self.progresso_sync.cancel()
            self.splash.finish(self)
            self.atualizar_barra_atualizacoes([])
        try:
            solucoes_sqlite_dict = None
            self.progresso_sync.setValue(80)
            QApplication.processEvents()
            total_sincronizado = 0
            total_atualizado = 0
            erros = 0
            atualizacoes = []
            for sol_mysql in solucoes_mysql:
                pass
            try:
                if sol_mysql['id'] not in solucoes_sqlite_dict:
                    self.cursor.execute('\n                            INSERT INTO solucoes (\n                                id, marca, modelo, descricao, observacoes,\n                                status, data_criacao, data_sincronizacao,\n                                hash_verificacao, versao, ultima_modificacao\n                            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?)\n                        ', (sol_mysql['id'], sol_mysql['marca'], sol_mysql['modelo'], sol_mysql['descricao'], sol_mysql['observacoes'], sol_mysql['status'], sol_mysql['data_criacao'], sol_mysql['hash_verificacao'], sol_mysql['versao'], sol_mysql['ultima_modificacao']))
                    total_sincronizado += 1
                    data_formatada = (sol_mysql['ultima_modificacao'] if isinstance(sol_mysql['ultima_modificacao'], datetime) else datetime.strptime(str(sol_mysql['ultima_modificacao']), '%Y-%m-%d %H:%M:%S')).strftime('%d/%m/%Y')
                    atualizacoes.append({'marca': sol_mysql['marca'], 'modelo': sol_mysql['modelo'], 'data': data_formatada})
                else:
                    sol_sqlite = solucoes_sqlite_dict[sol_mysql['id']]
                    mysql_ultima_mod = sol_mysql['ultima_modificacao'] if isinstance(sol_mysql['ultima_modificacao'], datetime) else datetime.strptime(str(sol_mysql['ultima_modificacao']), '%Y-%m-%d %H:%M:%S')
                    sqlite_ultima_mod = sol_sqlite['ultima_modificacao'] if isinstance(sol_sqlite['ultima_modificacao'], datetime) else datetime.strptime(str(sol_sqlite['ultima_modificacao']), '%Y-%m-%d %H:%M:%S')
                    if sol_mysql['marca'] != sol_sqlite['marca'] or sol_mysql['modelo'] != sol_sqlite['modelo'] or sol_mysql['descricao'] != sol_sqlite['descricao'] or sol_mysql['observacoes'] != sol_sqlite['observacoes'] or sol_mysql['status'] != sol_sqlite['status'] or sol_mysql['versao'] != sol_sqlite['versao'] or mysql_ultima_mod != sqlite_ultima_mod:
                        self.cursor.execute('\n                                UPDATE solucoes \n                                SET marca = ?, modelo = ?, descricao = ?, observacoes = ?,\n                                    status = ?, data_sincronizacao = CURRENT_TIMESTAMP,\n                                    hash_verificacao = ?, versao = ?, ultima_modificacao = ?\n                                WHERE id = ?\n                            ', (sol_mysql['marca'], sol_mysql['modelo'], sol_mysql['descricao'], sol_mysql['observacoes'], sol_mysql['status'], sol_mysql['hash_verificacao'], sol_mysql['versao'], sol_mysql['ultima_modificacao'], sol_mysql['id']))
                        total_atualizado += 1
                        data_formatada = mysql_ultima_mod.strftime('%d/%m/%Y')
                        atualizacoes.append({'marca': sol_mysql['marca'], 'modelo': sol_mysql['modelo'], 'data': data_formatada})
                if (total_sincronizado + total_atualizado) % 50 == 0:
                    if total_sincronizado + total_atualizado > 0:
                        self.conn.commit()
            except Exception as e:
                print(f'Erro ao sincronizar solu├º├úo {sol_mysql['id']}: {str(e)}')
                erros += 1
            else:
                self.progresso_sync.setValue(90)
                QApplication.processEvents()
        except Exception as e:
            print(f'Erro na sincroniza├º├úo: {str(e)}')
            self.mysql_online = False
            self.progresso_sync.cancel()
            self.splash.finish(self)
            self.atualizar_barra_atualizacoes([])
        try:
            ids_mysql = {str(s['id']) for s in solucoes_mysql}
        except Exception as e:
            print(f'Erro na sincroniza├º├úo: {str(e)}')
            self.mysql_online = False
            self.progresso_sync.cancel()
            self.splash.finish(self)
            self.atualizar_barra_atualizacoes([])
        try:
            ids_sqlite = {str(dict(row)['id']) for row in solucoes_sqlite}
            ids_para_remover = ids_sqlite - ids_mysql
            if ids_para_remover:
                ids_str = ','.join(ids_para_remover)
                self.cursor.execute(f'DELETE FROM solucoes WHERE id IN ({ids_str})')
            self.conn.commit()
            tempo_final = time.time()
            duracao = int(tempo_final - tempo_inicial)
            self.cursor.execute('\n                INSERT INTO sync_control (\n                    ultima_sincronizacao, status, detalhes,\n                    total_sincronizado, erros, duracao_segundos\n                ) VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)\n            ', ('sucesso' if erros == 0 else 'parcial', f'Sincronizadas: {total_sincronizado}, Atualizadas: {total_atualizado}, Erros: {erros}', total_sincronizado + total_atualizado, erros, duracao))
            self.conn.commit()
            mysql_cursor.close()
            mysql_conn.close()
            self.progresso_sync.setValue(100)
            self.splash.finish(self)
            self.atualizar_barra_atualizacoes(atualizacoes)
            return
        except Exception as e:
            print(f'Erro na sincroniza├º├úo: {str(e)}')
            self.mysql_online = False
            self.progresso_sync.cancel()
            self.splash.finish(self)
            self.atualizar_barra_atualizacoes([])
    def sincronizar_bancos(self):
        '''Sincroniza o SQLite local com o MySQL remoto'''
        if not hasattr(self, 'mysql_online') or not self.mysql_online:
            self.testar_conexao_mysql()
            if not self.mysql_online:
                self.atualizar_barra_atualizacoes([])
                return
        try:
            tempo_inicial = time.time()
            mysql_conn = self.conectar_mysql()
            if not mysql_conn:
                self.atualizar_barra_atualizacoes([])
                return
            mysql_cursor = mysql_conn.cursor()
            mysql_cursor.execute("\n                SELECT id, marca, modelo, descricao, observacoes, status, \n                       data_criacao, ultima_modificacao, hash_verificacao, versao\n                FROM solucoes \n                WHERE status = 'ativo'\n                ORDER BY ultima_modificacao DESC\n            ")
            solucoes_mysql = mysql_cursor.fetchall()
            self.cursor.execute('\n                SELECT id, marca, modelo, descricao, observacoes, status,\n                       data_criacao, ultima_modificacao, hash_verificacao, versao\n                FROM solucoes \n                ORDER BY ultima_modificacao DESC\n            ')
            solucoes_sqlite = self.cursor.fetchall()
        except Exception as e:
            print(f'Erro na sincroniza├º├úo: {str(e)}')
            self.mysql_online = False
            self.atualizar_barra_atualizacoes([])
        try:
            solucoes_sqlite_dict = None
            total_sincronizado = 0
            total_atualizado = 0
            erros = 0
            atualizacoes = []
            for sol_mysql in solucoes_mysql:
                pass
            try:
                if sol_mysql['id'] not in solucoes_sqlite_dict:
                    self.cursor.execute('\n                            INSERT INTO solucoes (\n                                id, marca, modelo, descricao, observacoes,\n                                status, data_criacao, data_sincronizacao,\n                                hash_verificacao, versao, ultima_modificacao\n                            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?)\n                        ', (sol_mysql['id'], sol_mysql['marca'], sol_mysql['modelo'], sol_mysql['descricao'], sol_mysql['observacoes'], sol_mysql['status'], sol_mysql['data_criacao'], sol_mysql['hash_verificacao'], sol_mysql['versao'], sol_mysql['ultima_modificacao']))
                    total_sincronizado += 1
                    data_formatada = (sol_mysql['ultima_modificacao'] if isinstance(sol_mysql['ultima_modificacao'], datetime) else datetime.strptime(str(sol_mysql['ultima_modificacao']), '%Y-%m-%d %H:%M:%S')).strftime('%d/%m/%Y')
                    atualizacoes.append({'marca': sol_mysql['marca'], 'modelo': sol_mysql['modelo'], 'data': data_formatada})
                else:
                    sol_sqlite = solucoes_sqlite_dict[sol_mysql['id']]
                    mysql_ultima_mod = sol_mysql['ultima_modificacao'] if isinstance(sol_mysql['ultima_modificacao'], datetime) else datetime.strptime(str(sol_mysql['ultima_modificacao']), '%Y-%m-%d %H:%M:%S')
                    sqlite_ultima_mod = sol_sqlite['ultima_modificacao'] if isinstance(sol_sqlite['ultima_modificacao'], datetime) else datetime.strptime(str(sol_sqlite['ultima_modificacao']), '%Y-%m-%d %H:%M:%S')
                    if sol_mysql['marca'] != sol_sqlite['marca'] or sol_mysql['modelo'] != sol_sqlite['modelo'] or sol_mysql['descricao'] != sol_sqlite['descricao'] or sol_mysql['observacoes'] != sol_sqlite['observacoes'] or sol_mysql['status'] != sol_sqlite['status'] or sol_mysql['versao'] != sol_sqlite['versao'] or mysql_ultima_mod != sqlite_ultima_mod:
                        self.cursor.execute('\n                                UPDATE solucoes \n                                SET marca = ?, modelo = ?, descricao = ?, observacoes = ?,\n                                    status = ?, data_sincronizacao = CURRENT_TIMESTAMP,\n                                    hash_verificacao = ?, versao = ?, ultima_modificacao = ?\n                                WHERE id = ?\n                            ', (sol_mysql['marca'], sol_mysql['modelo'], sol_mysql['descricao'], sol_mysql['observacoes'], sol_mysql['status'], sol_mysql['hash_verificacao'], sol_mysql['versao'], sol_mysql['ultima_modificacao'], sol_mysql['id']))
                        total_atualizado += 1
                        data_formatada = mysql_ultima_mod.strftime('%d/%m/%Y')
                        atualizacoes.append({'marca': sol_mysql['marca'], 'modelo': sol_mysql['modelo'], 'data': data_formatada})
                if (total_sincronizado + total_atualizado) % 50 == 0:
                    if total_sincronizado + total_atualizado > 0:
                        self.conn.commit()
            except Exception as e:
                print(f'Erro ao sincronizar solu├º├úo {sol_mysql['id']}: {str(e)}')
                erros += 1
        except Exception as e:
            print(f'Erro na sincroniza├º├úo: {str(e)}')
            self.mysql_online = False
            self.atualizar_barra_atualizacoes([])
        try:
            ids_mysql = {str(s['id']) for s in solucoes_mysql}
        except Exception as e:
            print(f'Erro na sincroniza├º├úo: {str(e)}')
            self.mysql_online = False
            self.atualizar_barra_atualizacoes([])
        try:
            ids_sqlite = {str(dict(row)['id']) for row in solucoes_sqlite}
            ids_para_remover = ids_sqlite - ids_mysql
            if ids_para_remover:
                ids_str = ','.join(ids_para_remover)
                self.cursor.execute(f'DELETE FROM solucoes WHERE id IN ({ids_str})')
            self.conn.commit()
            tempo_final = time.time()
            duracao = int(tempo_final - tempo_inicial)
            self.cursor.execute('\n                INSERT INTO sync_control (\n                    ultima_sincronizacao, status, detalhes, \n                    total_sincronizado, erros, duracao_segundos\n                ) VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)\n            ', ('sucesso' if erros == 0 else 'parcial', f'Sincronizadas: {total_sincronizado}, Atualizadas: {total_atualizado}, Erros: {erros}', total_sincronizado + total_atualizado, erros, duracao))
            self.conn.commit()
            mysql_cursor.close()
            mysql_conn.close()
            self.atualizar_barra_atualizacoes(atualizacoes)
            return
        except Exception as e:
            print(f'Erro na sincroniza├º├úo: {str(e)}')
            self.mysql_online = False
            self.atualizar_barra_atualizacoes([])
    def conectar_mysql(self):
        '''Conecta ao MySQL remoto'''
        try:
            return pymysql.connect(**db_config(cursorclass=pymysql.cursors.DictCursor, ssl={'ca': None}, ssl_verify_cert=False))
        except Exception as e:
            print(f'Erro ao conectar ao MySQL: {str(e)}')
            self.mysql_online = False
    def atualizar_barra_atualizacoes(self, atualizacoes):
        '''Atualiza a barra com as ├║ltimas atualiza├º├Áes.
Cor da barra:
    - Layout antigo (flag OFF): vermelho original (#e74c3c).
    - Layout novo (flag ON): azul escuro alinhado com a paleta do header
      e do sidebar (#0D47A1).
'''
        if getattr(self, '_use_new_sidebar', False):
            _bar_bg = '#0D47A1'
        else:
            _bar_bg = '#e74c3c'
        if not hasattr(self, 'update_frame'):
            try:
                self.update_frame = QFrame()
                self.update_frame.setObjectName('updateFrame')
                self.update_frame.setStyleSheet(f'\n                    QFrame#updateFrame {{\n                        background-color: {_bar_bg};\n                        border-radius: 5px;\n                        margin: 0px;\n                        padding: 5px;\n                        min-height: 40px;\n                    }}\n                    QFrame#updateFrame QLabel {{\n                        color: white;\n                        font-size: 14px;\n                        font-weight: bold;\n                        padding: 5px 0px;\n                    }}\n                    QPushButton#btnVerTodas {{\n                        background-color: rgba(255, 255, 255, 0.3);\n                        border: 2px solid rgba(255, 255, 255, 0.6);\n                        border-radius: 18px;\n                        padding: 8px 16px;\n                        color: white;\n                        font-weight: bold;\n                        font-size: 13px;\n                        min-width: 120px;\n                        max-width: 150px;\n                        border-bottom: 2px solid rgba(0, 0, 0, 0.2);\n                    }}\n                    QPushButton#btnVerTodas:hover {{\n                        background-color: rgba(255, 255, 255, 0.4);\n                        border: 2px solid rgba(255, 255, 255, 0.8);\n                        border-bottom: 3px solid rgba(0, 0, 0, 0.3);\n                    }}\n                    QPushButton#btnVerTodas:pressed {{\n                        background-color: rgba(255, 255, 255, 0.5);\n                    }}\n                ')
                update_layout = QHBoxLayout(self.update_frame)
                update_layout.setContentsMargins(10, 5, 15, 5)
                update_layout.setSpacing(15)
                icon_label = QLabel()
                icon_pixmap = QIcon(PathManager.get_resource_path('icons_svg/phone-flip.svg')).pixmap(QSize(16, 16))
                icon_label.setPixmap(icon_pixmap)
                icon_label.setStyleSheet('padding-right: 8px;')
                update_layout.addWidget(icon_label)
                self.update_label = QLabel()
                self.update_label.setStyleSheet("\n                    padding-right: 10px;\n                    font-family: 'Segoe UI', Arial;\n                    font-weight: bold;\n                    font-size: 14px;\n                ")
                update_layout.addWidget(self.update_label, 1)
                btn_ver_todas = QPushButton(self.translation_manager.get_text('view_all'))
                btn_ver_todas.setIcon(QIcon(PathManager.get_resource_path('icons_svg/card-checklist.svg')))
                btn_ver_todas.setIconSize(QSize(16, 16))
                btn_ver_todas.setObjectName('btnVerTodas')
                btn_ver_todas.setCursor(Qt.PointingHandCursor)
                btn_ver_todas.setSizePolicy(btn_ver_todas.sizePolicy().horizontalPolicy(), btn_ver_todas.sizePolicy().verticalPolicy())
                btn_ver_todas.clicked.connect(self.mostrar_historico_atualizacoes)
                update_layout.addWidget(btn_ver_todas, 0)
                if getattr(self, '_use_new_sidebar', False) and getattr(self, '_content_widget', None) is not None:
                    layout = self._content_widget.layout()
                else:
                    layout = self.centralWidget().layout()
                layout.insertWidget(1, self.update_frame)
                self.update_frame.show()
                QApplication.processEvents()
            except Exception as e:
                print(f'Erro ao criar barra de atualiza├º├Áes: {str(e)}')
        if not atualizacoes:
            try:
                self.cursor.execute('\n                    SELECT marca, modelo, ultima_modificacao \n                    FROM solucoes \n                    ORDER BY ultima_modificacao DESC \n                    LIMIT 5\n                ')
                ultimas_solucoes = self.cursor.fetchall()
                if ultimas_solucoes:
                    nome_exibicao_map = {'ESQUEMAS ELETRICO': 'ESQUEMAS EL├ëTRICOS'}
                    atualizacoes_texto = []
                    for sol in ultimas_solucoes:
                        sol_dict = dict(sol)
                        data = datetime.strptime(sol_dict['ultima_modificacao'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                        marca_exibir = nome_exibicao_map.get(sol_dict['marca'], sol_dict['marca'])
                        atualizacoes_texto.append(f'{marca_exibir} - {sol_dict['modelo']} ({data})')
                    self.texto_completo = ' | '.join(atualizacoes_texto[:5])
                    self.texto_completo = '          ' + self.texto_completo + '          '
                    self.update_label.setText(self.texto_completo)
                    return
            except Exception as e:
                print(f'Erro ao buscar solu├º├Áes do banco: {str(e)}')
            no_updates_text = self.translation_manager.get_text('no_new_updates')
            self.update_label.setText(no_updates_text)
            self.texto_completo = no_updates_text
            return
        atualizacoes = atualizacoes[:5]
        nome_exibicao_map = {'ESQUEMAS ELETRICO': 'ESQUEMAS EL├ëTRICOS'}
        atualizacoes_texto = []
        for update in atualizacoes:
            data_formatada = update.get('data', '')
            marca_exibir = nome_exibicao_map.get(update['marca'], update['marca'])
            atualizacoes_texto.append(f'{marca_exibir} - {update['modelo']} ({data_formatada})')
        self.texto_completo = ' | '.join(atualizacoes_texto)
        self.texto_completo = '          ' + self.texto_completo + '          '
        self.update_label.setText(self.texto_completo)
        self.update_frame.show()
        QApplication.processEvents()
    def animar_texto(self):
        '''Anima o texto rolando da direita para a esquerda (melhor para leitura)'''
        if not hasattr(self, 'texto_completo') or not self.texto_completo:
            return
        if not hasattr(self, 'scroll_position'):
            self.scroll_position = 0
        self.scroll_position += 1
        if self.scroll_position >= len(self.texto_completo):
            self.scroll_position = 0
        texto_rotacionado = self.texto_completo[self.scroll_position:] + self.texto_completo[:self.scroll_position]
        self.update_label.setText(texto_rotacionado)
    def mostrar_historico_atualizacoes(self):
        '''Mostra o hist├│rico das ├║ltimas 10 atualiza├º├Áes'''
        dialog = QDialog(self)
        dialog.setWindowTitle(self.translation_manager.get_text('update_history'))
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet('\n            QDialog {\n                background-color: white;\n            }\n            QLabel#titleLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                padding: 10px;\n            }\n            QFrame#listFrame {\n                background-color: #f8f9fa;\n                border-radius: 5px;\n                padding: 10px;\n            }\n            QLabel#updateLabel {\n                padding: 8px;\n                border-bottom: 1px solid #dee2e6;\n            }\n        ')
        layout = QVBoxLayout(dialog)
        title_layout = QHBoxLayout()
        title = QLabel(self.translation_manager.get_text('latest_updates'))
        title.setObjectName('titleLabel')
        title_layout.addWidget(title)
        try:
            self.cursor.execute('\n                SELECT status FROM sync_control \n                ORDER BY ultima_sincronizacao DESC LIMIT 1\n            ')
            result = self.cursor.fetchone()
            sync_status = 'Ô£à' if result and result['status'] == 'sucesso' else 'ÔÜ½'
            status_label = QLabel(f'{self.translation_manager.get_text('status')}: {sync_status}')
            status_label.setStyleSheet('font-size: 14px; padding: 10px;')
            title_layout.addWidget(status_label)
        except Exception as e:
            print(f'Erro ao verificar status: {str(e)}')
        layout.addLayout(title_layout)
        list_frame = QFrame()
        list_frame.setObjectName('listFrame')
        list_layout = QVBoxLayout(list_frame)
        try:
            self.cursor.execute('\n                SELECT marca, modelo, ultima_modificacao \n                FROM solucoes \n                ORDER BY ultima_modificacao DESC \n                LIMIT 10\n            ')
            atualizacoes = self.cursor.fetchall()
            if atualizacoes:
                nome_exibicao_map = {'ESQUEMAS ELETRICO': 'ESQUEMAS EL├ëTRICOS'}
                for sol in atualizacoes:
                    sol_dict = dict(sol)
                    data = datetime.strptime(sol_dict['ultima_modificacao'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
                    marca_exibir = nome_exibicao_map.get(sol_dict['marca'], sol_dict['marca'])
                    update_label = QLabel(f'{marca_exibir} - {sol_dict['modelo']}\n{data}')
                    update_label.setObjectName('updateLabel')
                    list_layout.addWidget(update_label)
            else:
                no_updates = QLabel(self.translation_manager.get_text('no_updates_found'))
                no_updates.setAlignment(Qt.AlignCenter)
                list_layout.addWidget(no_updates)
        except Exception as e:
            error_label = QLabel(f'{self.translation_manager.get_text('error_loading_updates')}: {str(e)}')
            error_label.setStyleSheet('color: red;')
            list_layout.addWidget(error_label)
        layout.addWidget(list_frame)
        btn_sync = QPushButton(self.translation_manager.get_text('sync_now'))
        btn_sync.setStyleSheet('\n            QPushButton {\n                background-color: #3498db;\n                color: white;\n                padding: 8px 15px;\n                border-radius: 4px;\n                border: none;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #2980b9;\n            }\n        ')
        btn_sync.clicked.connect((lambda: [self.sincronizar_bancos(), dialog.accept()]))
        layout.addWidget(btn_sync)
        btn_fechar = QPushButton(self.translation_manager.get_text('close'))
        btn_fechar.setStyleSheet('\n            QPushButton {\n                background-color: #e74c3c;\n                color: white;\n                padding: 8px 15px;\n                border-radius: 4px;\n                border: none;\n            }\n            QPushButton:hover {\n                background-color: #c0392b;\n            }\n        ')
        btn_fechar.clicked.connect(dialog.close)
        layout.addWidget(btn_fechar)
        dialog.exec_()
    def closeEvent(self, event):
        '''Sobrescreve o evento de fechamento para parar os timers e limpar cache'''
        if hasattr(self, 'sync_timer') and self.sync_timer.isActive():
            self.sync_timer.stop()
        if hasattr(self, 'scroll_timer') and self.scroll_timer.isActive():
            self.scroll_timer.stop()
        if hasattr(self, 'help_timer') and self.help_timer.isActive():
            self.help_timer.stop()
        try:
            if hasattr(self, '_guard_timer') and self._guard_timer is not None and self._guard_timer.isActive():
                self._guard_timer.stop()
        except Exception:
            pass
        try:
            from app.utils.mtk_manager import limpar_cache_mtk
            limpar_cache_mtk()
        except:
            pass
        try:
            from app.utils.unlock_tools_manager import limpar_tools_unlock
            limpar_tools_unlock()
        except:
            pass
        super().closeEvent(event)
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        self._sidebar = None
        self._content_widget = None
        if getattr(self, '_use_new_sidebar', False):
            try:
                from app.views.ui.sidebar import Sidebar
                root = QHBoxLayout(central)
                root.setContentsMargins(0, 0, 0, 0)
                root.setSpacing(0)
                self._sidebar = Sidebar(parent_main_window=self, translation_manager=self.translation_manager)
                try:
                    self.translation_manager.language_changed.connect(self._sidebar.refresh_translations)
                except Exception:
                    pass
                try:
                    if self.is_premium_user or self.is_admin:
                        self._sidebar.set_badge_text('hxd_tools', 'NOVO')
                        self._sidebar.set_badge_text('exy_tools', 'NOVO')
                        self._sidebar.set_badge_text('os_manager', 'NOVO')
                except Exception:
                    pass
                else:
                    root.addWidget(self._sidebar)
                    self._content_widget = QWidget()
                    layout = QVBoxLayout(self._content_widget)
                    layout.setContentsMargins(0, 0, 16, 8)
                    layout.setSpacing(8)
                    root.addWidget(self._content_widget, 1)
            except Exception as e:
                print(f'[setup_ui] sidebar indisponivel ({type(e).__name__}: {e}); usando layout antigo')
                self._use_new_sidebar = False
                self._sidebar = None
                self._content_widget = None
                if central.layout() is None:
                    layout = QVBoxLayout(central)
                    layout.setContentsMargins(20, 20, 20, 20)
        else:
            layout = QVBoxLayout(central)
            layout.setContentsMargins(20, 20, 20, 20)
        screen = QApplication.primaryScreen().geometry()
        is_small_screen = screen.width() <= 1366
        header_frame = QFrame()
        header_frame.setObjectName('headerFrame')
        max_header_height = '180px' if is_small_screen else '140px'
        if getattr(self, '_use_new_sidebar', False):
            header_frame.setStyleSheet('\n                QFrame#headerFrame {\n                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n                        stop:0 #0D47A1, stop:1 #2196F3);\n                    border-radius: 10px;\n                    padding: 10px 16px;\n                    margin: 0px;\n                    border: 1px solid rgba(0, 0, 0, 0.1);\n                }\n            ')
        else:
            header_frame.setStyleSheet(f'\n                QFrame#headerFrame {{\n                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0D47A1, stop:1 #2196F3);\n                    border-radius: 15px;\n                    padding: 20px;\n                    max-height: {max_header_height};\n                    margin-bottom: 20px;\n                    border: 1px solid rgba(0, 0, 0, 0.1);\n                }}\n            ')
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(4 if getattr(self, '_use_new_sidebar', False) else 10)
        header_layout.setContentsMargins(0, 0, 0, 0)
        top_header = QHBoxLayout()
        top_header.setContentsMargins(0, 0, 0, 0 if getattr(self, '_use_new_sidebar', False) else 5)
        title_area = QVBoxLayout()
        title_area.setSpacing(10)
        title_area.setContentsMargins(0, 0, 0, 0)
        title_font_size = '24px' if is_small_screen else '28px'
        slogan_font_size = '12px' if is_small_screen else '14px'
        title = QLabel('TECH UNION SOLUTIONS')
        title.setObjectName('mainTitle')
        title.setStyleSheet(f'\n            QLabel#mainTitle {{\n                font-size: {title_font_size};\n                font-weight: bold;\n                color: white;\n                padding: 0;\n                margin: 0;\n                margin-bottom: 5px;\n                min-height: 35px;\n            }}\n        ')
        title_area.addWidget(title)
        slogan = QLabel(self.translation_manager.get_text('slogan'))
        slogan.setObjectName('sloganText')
        slogan.setStyleSheet(f'\n            QLabel#sloganText {{\n                color: white;\n                font-size: {slogan_font_size};\n                font-style: italic;\n                font-weight: 400;\n                opacity: 0.9;\n                padding: 0;\n                margin: 0;\n                min-height: 20px;\n            }}\n        ')
        title_area.addWidget(slogan)
        if not getattr(self, '_use_new_sidebar', False):
            top_header.addLayout(title_area, 1)
        _use_topbar_legacy = not getattr(self, '_use_new_sidebar', False)
        buttons_container = QWidget()
        buttons_layout = QGridLayout(buttons_container)
        buttons_layout.setSpacing(8 if is_small_screen else 10)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        button_row = 0
        button_col = 0
        max_cols = 4 if is_small_screen else 6
        def add_button_to_layout(button):
            nonlocal button_col, button_row
            if not _use_topbar_legacy:
                return
            buttons_layout.addWidget(button, button_row, button_col)
            button_col += 1
            if button_col >= max_cols:
                button_col = 0
                button_row += 1
        button_style_padding = '6px 12px' if is_small_screen else '8px 15px'
        button_font_size = '11px' if is_small_screen else '12px'
        btn_mtk = QPushButton('MTK Tools')
        btn_mtk.setIcon(QIcon(PathManager.get_resource_path('icons_svg/cpu.svg')))
        btn_mtk.setIconSize(QSize(16, 16))
        btn_mtk.setObjectName('mtkButton')
        btn_mtk.setStyleSheet(f'\n            QPushButton#mtkButton {{\n                background: #18B6A4;\n                border: 2px solid #00695C;\n                border-radius: 5px;\n                padding: {button_style_padding};\n                color: white;\n                font-weight: bold;\n                font-size: {button_font_size};\n            }}\n            QPushButton#mtkButton:hover {{\n                background: #15A193;\n                border: 2px solid #00695C;\n            }}\n        ')
        btn_mtk.setCursor(Qt.PointingHandCursor)
        btn_mtk.clicked.connect(self.abrir_mtk_flash_tools)
        add_button_to_layout(btn_mtk)
        os_new_acessivel = self.is_premium_user or self.is_admin
        if os_new_acessivel:
            btn_os_new = QPushButton('OS NEW')
            btn_os_new.setIcon(QIcon(PathManager.get_resource_path('icons_svg/graph-up.svg')))
            btn_os_new.setIconSize(QSize(16, 16))
            btn_os_new.setObjectName('osNewButton')
            btn_os_new.setStyleSheet(f'\n                QPushButton#osNewButton {{\n                    background: #8B5CF6;\n                    border: 2px solid #6D28D9;\n                    border-radius: 5px;\n                    padding: {button_style_padding};\n                    color: white;\n                    font-weight: bold;\n                    font-size: {button_font_size};\n                }}\n                QPushButton#osNewButton:hover {{\n                    background: #7C3AED;\n                    border: 2px solid #6D28D9;\n                }}\n            ')
        else:
            _svg_lock = PathManager.get_resource_path('icons_svg/shield-lock.svg')
            _svg_graph = PathManager.get_resource_path('icons_svg/graph-up.svg')
            _btn_icon = QIcon(_svg_lock) if _svg_lock and os.path.isfile(_svg_lock) else QIcon(_svg_graph)
            btn_os_new = QPushButton('OS NEW ÔÇö PREMIUM')
            btn_os_new.setIcon(_btn_icon)
            btn_os_new.setIconSize(QSize(16, 16))
            btn_os_new.setObjectName('osNewButton')
            btn_os_new.setStyleSheet(f'\n                QPushButton#osNewButton {{\n                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, \n                        stop:0 #e67e22, stop:1 #f39c12);\n                    border: 2px solid #d35400;\n                    border-radius: 5px;\n                    padding: {button_style_padding};\n                    color: white;\n                    font-weight: bold;\n                    font-size: {button_font_size};\n                }}\n                QPushButton#osNewButton:hover {{\n                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, \n                        stop:0 #d35400, stop:1 #e67e22);\n                }}\n            ')
        btn_os_new.setCursor(Qt.PointingHandCursor)
        btn_os_new.clicked.connect(self.abrir_os_manager)
        add_button_to_layout(btn_os_new)
        btn_uart = QPushButton(self.translation_manager.get_text('uart_monitor'))
        btn_uart.setIcon(QIcon(PathManager.get_resource_path('icons_svg/terminal.svg')))
        btn_uart.setIconSize(QSize(16, 16))
        btn_uart.setObjectName('uartButton')
        btn_uart.setStyleSheet(f'\n            QPushButton#uartButton {{\n                background: #1E6FD9;\n                border: 2px solid #0D47A1;\n                border-radius: 5px;\n                padding: {button_style_padding};\n                color: white;\n                font-weight: bold;\n                font-size: {button_font_size};\n            }}\n            QPushButton#uartButton:hover {{\n                background: #1A5FC2;\n                border: 2px solid #0D47A1;\n            }}\n        ')
        btn_uart.setCursor(Qt.PointingHandCursor)
        btn_uart.clicked.connect(self.abrir_uart_monitor)
        add_button_to_layout(btn_uart)
        btn_tira_virus = QPushButton(self.translation_manager.get_text('antivirus'))
        btn_tira_virus.setIcon(QIcon(PathManager.get_resource_path('icons_svg/shield-check.svg')))
        btn_tira_virus.setIconSize(QSize(16, 16))
        btn_tira_virus.setObjectName('tiravirusButton')
        btn_tira_virus.setStyleSheet(f'\n            QPushButton#tiravirusButton {{\n                background: #1FBF75;\n                border: 2px solid #00695C;\n                border-radius: 5px;\n                padding: {button_style_padding};\n                color: white;\n                font-weight: bold;\n                font-size: {button_font_size};\n            }}\n            QPushButton#tiravirusButton:hover {{\n                background: #1AAA66;\n                border: 2px solid #00695C;\n            }}\n        ')
        btn_tira_virus.setCursor(Qt.PointingHandCursor)
        btn_tira_virus.clicked.connect(self.abrir_tira_virus)
        add_button_to_layout(btn_tira_virus)
        btn_server = QPushButton('Server GSM')
        btn_server.setIcon(QIcon(PathManager.get_resource_path('icons_svg/globe.svg')))
        btn_server.setIconSize(QSize(16, 16))
        btn_server.setObjectName('serverButton')
        btn_server.setStyleSheet(f'\n            QPushButton#serverButton {{\n                background: #1E6FD9;\n                border: 2px solid #0D47A1;\n                border-radius: 5px;\n                padding: {button_style_padding};\n                color: white;\n                font-weight: bold;\n                font-size: {button_font_size};\n            }}\n            QPushButton#serverButton:hover {{\n                background: #1A5FC2;\n                border: 2px solid #0D47A1;\n            }}\n        ')
        btn_server.setCursor(Qt.PointingHandCursor)
        btn_server.clicked.connect(self.abrir_server_gsm)
        add_button_to_layout(btn_server)
        btn_ferramentas = QPushButton(self.translation_manager.get_text('tools'))
        btn_ferramentas.setIcon(QIcon(PathManager.get_resource_path('icons_svg/tools.svg')))
        btn_ferramentas.setIconSize(QSize(16, 16))
        btn_ferramentas.setObjectName('toolsButton')
        btn_ferramentas.setStyleSheet(f'\n            QPushButton#toolsButton {{\n                background: #10B981;\n                border: 2px solid #047857;\n                border-radius: 5px;\n                padding: {button_style_padding};\n                color: white;\n                font-weight: bold;\n                font-size: {button_font_size};\n            }}\n            QPushButton#toolsButton:hover {{\n                background: #059669;\n                border: 2px solid #047857;\n            }}\n        ')
        btn_ferramentas.setCursor(Qt.PointingHandCursor)
        btn_ferramentas.clicked.connect(self.abrir_diagnostico)
        add_button_to_layout(btn_ferramentas)
        if self.is_com_user or self.is_premium_user or self.is_admin:
            btn_sistema_os = QPushButton(self.translation_manager.get_text('system_os'))
            btn_sistema_os.setIcon(QIcon(PathManager.get_resource_path('icons_svg/pc-display-horizontal.svg')))
            btn_sistema_os.setIconSize(QSize(16, 16))
            btn_sistema_os.setObjectName('systemButton')
            btn_sistema_os.setStyleSheet(f'\n                QPushButton {{\n                    background: #1E6FD9;\n                    border: 2px solid #0D47A1;\n                    border-radius: 5px;\n                    padding: {button_style_padding};\n                    color: white;\n                    font-weight: bold;\n                    font-size: {button_font_size};\n                }}\n                QPushButton:hover {{\n                    background: #1A5FC2;\n                    border: 2px solid #0D47A1;\n                }}\n            ')
            btn_sistema_os.setCursor(Qt.PointingHandCursor)
            btn_sistema_os.clicked.connect(self.abrir_sistema_os)
            add_button_to_layout(btn_sistema_os)
            btn_minhas_solucoes = QPushButton(self.translation_manager.get_text('my_solutions'))
            btn_minhas_solucoes.setIcon(QIcon(PathManager.get_resource_path('icons_svg/folder-check.svg')))
            btn_minhas_solucoes.setIconSize(QSize(16, 16))
            btn_minhas_solucoes.setObjectName('solutionsButton')
            btn_minhas_solucoes.setStyleSheet(f'\n                QPushButton {{\n                    background: #1E40AF;\n                    border: 2px solid #1E3A8A;\n                    border-radius: 5px;\n                    padding: {button_style_padding};\n                    color: white;\n                    font-weight: bold;\n                    font-size: {button_font_size};\n                }}\n                QPushButton:hover {{\n                    background: #1D4ED8;\n                    border: 2px solid #1E3A8A;\n                }}\n            ')
            btn_minhas_solucoes.setCursor(Qt.PointingHandCursor)
            btn_minhas_solucoes.clicked.connect(self.abrir_minhas_solucoes)
            add_button_to_layout(btn_minhas_solucoes)
        btn_downloads = QPushButton(self.translation_manager.get_text('downloads'))
        btn_downloads.setIcon(QIcon(PathManager.get_resource_path('icons_svg/cloud-arrow-down.svg')))
        btn_downloads.setIconSize(QSize(16, 16))
        btn_downloads.setObjectName('downloadsButton')
        btn_downloads.setStyleSheet(f'\n            QPushButton#downloadsButton {{\n                background: #F59E0B;\n                border: 2px solid #0D47A1;\n                border-radius: 5px;\n                padding: {button_style_padding};\n                color: white;\n                font-weight: bold;\n                font-size: {button_font_size};\n            }}\n            QPushButton#downloadsButton:hover {{\n                background: #DC8B09;\n                border: 2px solid #0D47A1;\n            }}\n        ')
        btn_downloads.setCursor(Qt.PointingHandCursor)
        btn_downloads.clicked.connect(self.abrir_downloads)
        add_button_to_layout(btn_downloads)
        btn_peliculas = QPushButton(self.translation_manager.get_text('peliculas'))
        btn_peliculas.setIcon(QIcon(PathManager.get_resource_path('icons_svg/pelicula.svg')))
        btn_peliculas.setIconSize(QSize(16, 16))
        btn_peliculas.setObjectName('peliculasButton')
        btn_peliculas.setStyleSheet(f'\n            QPushButton#peliculasButton {{\n                background-color: #FACC15;\n                color: #263238;\n                padding: {button_style_padding};\n                border-radius: 5px;\n                font-weight: bold;\n                font-size: {button_font_size};\n                border: 2px solid #F57F17;\n            }}\n            QPushButton#peliculasButton:hover {{\n                background-color: #E1B712;\n                border: 2px solid #F57F17;\n            }}\n            QPushButton#peliculasButton:pressed {{\n                background-color: #C9A410;\n            }}\n        ')
        btn_peliculas.setCursor(Qt.PointingHandCursor)
        btn_peliculas.clicked.connect(self.abrir_peliculas)
        add_button_to_layout(btn_peliculas)
        if _use_topbar_legacy:
            top_header.addWidget(buttons_container)
        else:
            try:
                welcome_box = self._construir_banner_boas_vindas()
                top_header.addWidget(welcome_box, 2)
            except Exception as e:
                print(f'[setup_ui] banner de boas-vindas indisponivel ({type(e).__name__}: {e})')
        header_layout.addLayout(top_header)
        self._header_status_bar = None
        _use_legacy_user_info = True
        if getattr(self, '_use_new_sidebar', False):
            try:
                from app.views.ui.header_status_cards import HeaderStatusBar
                _tm_hsb = getattr(self, 'translation_manager', None)
                self._header_status_bar = HeaderStatusBar(parent_main_window=self, translation_manager=_tm_hsb)
                header_layout.addWidget(self._header_status_bar, 0, Qt.AlignRight)
                _use_legacy_user_info = False
                if _tm_hsb is not None:
                    try:
                        try:
                            sig = getattr(_tm_hsb, 'language_changed', None)
                            if sig is not None and hasattr(sig, 'connect'):
                                sig.connect(self._header_status_bar.refresh)
                        except Exception as _e_sig:
                            print(f'[setup_ui] nao foi possivel conectar language_changed -> header_status_bar.refresh: {type(_e_sig).__name__}')
                    except Exception as _e_hsb:
                        print(f'[setup_ui] header_status_bar indisponivel ({type(_e_hsb).__name__}: {_e_hsb}); usando user_info legado')
                        self._header_status_bar = None
                        _use_legacy_user_info = True
            except Exception as _e_hsb:
                print(f'[setup_ui] header_status_bar indisponivel ({type(_e_hsb).__name__}: {_e_hsb}); usando user_info legado')
                self._header_status_bar = None
                _use_legacy_user_info = True
        if _use_legacy_user_info:
            user_info = QHBoxLayout()
            user_info.addStretch()
            if self.user_email:
                username = self.user_email.split('@')[0]
            elif self.user_domain:
                username = 'Usu├írio'
            else:
                username = 'Usu├írio'
            user_label = QLabel(username)
            user_label.setObjectName('userLabel')
            user_label.setStyleSheet('\n                color: #ecf0f1;\n                font-size: 13px;\n                padding: 3px 10px;\n                background: rgba(0, 0, 0, 0.18);\n                border: 1px solid rgba(255, 255, 255, 0.08);\n                border-radius: 10px;\n                font-weight: 600;\n            ')
            user_info.addWidget(user_label)
            dias_restantes = self.calcular_dias_restantes()
            if dias_restantes == 'Ôê×':
                license_label = QLabel('Licen├ºa Ativa')
                license_color = '#2ecc71'
            elif dias_restantes == 'EXPIRADA':
                license_label = QLabel('Licen├ºa Expirada')
                license_color = '#e74c3c'
            elif dias_restantes == 'HOJE':
                license_label = QLabel('Expira Hoje')
                license_color = '#f39c12'
            elif dias_restantes.isdigit():
                days = int(dias_restantes)
                if days <= 7:
                    license_label = QLabel(f'{days} dias restantes')
                    license_color = '#f39c12'
                elif days <= 30:
                    license_label = QLabel(f'{days} dias restantes')
                    license_color = '#f1c40f'
                else:
                    license_label = QLabel(f'{days} dias restantes')
                    license_color = '#2ecc71'
            else:
                license_label = QLabel('Licen├ºa Ativa')
                license_color = '#3498db'
            license_label.setObjectName('licenseLabel')
            license_label.setStyleSheet(f'\n                color: {license_color};\n                font-size: 13px;\n                padding: 3px 10px;\n                background: rgba(0, 0, 0, 0.18);\n                border: 1px solid rgba(255, 255, 255, 0.08);\n                border-radius: 10px;\n                margin-left: 10px;\n                font-weight: bold;\n            ')
            user_info.addWidget(license_label)
            if self.is_admin:
                admin_label = QLabel('Modo Administrador')
                admin_label.setObjectName('adminLabel')
                admin_label.setStyleSheet('\n                    color: #2ecc71;\n                    font-size: 13px;\n                    padding: 3px 10px;\n                    background: rgba(0, 0, 0, 0.18);\n                    border: 1px solid rgba(255, 255, 255, 0.08);\n                    border-radius: 10px;\n                    margin-left: 10px;\n                    font-weight: 600;\n                ')
                user_info.addWidget(admin_label)
            elif self.is_premium_user:
                premium_label = QLabel('Plano Premium')
                premium_label.setObjectName('premiumLabel')
                premium_label.setStyleSheet('\n                    color: #f1c40f;\n                    font-size: 13px;\n                    padding: 3px 10px;\n                    background: rgba(0, 0, 0, 0.18);\n                    border: 1px solid rgba(255, 255, 255, 0.08);\n                    border-radius: 10px;\n                    margin-left: 10px;\n                    font-weight: 600;\n                ')
                user_info.addWidget(premium_label)
            header_layout.addLayout(user_info)
        layout.addWidget(header_frame)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('\n            QScrollArea {\n                border: none;\n                background-color: transparent;\n            }\n        ')
        self._cards_scroll_area = scroll
        scroll_content = QWidget()
        self.grid_layout = QGridLayout(scroll_content)
        self.grid_layout.setSpacing(20)
        self._cards_cols_atual = 0
        self._cards_widgets_ordem = []
        marcas = [('SAMSUNG', 'samsung.png', '#1428a0'), ('APPLE', 'apple.png', '#999999'), ('MOTOROLA', 'motorola.png', '#5c92fa'), ('XIAOMI', 'xiaomi.png', '#ff6700'), ('REALME', 'realme.png', '#ffd500'), ('OPPO', 'oppo.png', '#008000'), ('VIVO', 'vivo.png', '#0051ba'), ('HUAWEI', 'huawei.png', '#ff0000'), ('INFINIX', 'infinix.png', '#00a1e4'), ('TECNO', 'tecno.png', '#1a73e8'), ('ANDROID\nCOMANDOS', 'android.png', '#a4c639'), ('SOFTWARE', 'software.png', '#2ecc71'), ('CPU', 'cpu.png', '#4a90e2'), ('ESTUDO', 'estudo.png', '#34495e'), ('JUMPER DE TELAS', 'telas.png', '#8e44ad'), ('EMMC UFS', 'isp.png', '#e67e22'), ('ESQUEMAS ELETRICO', 'esquema.png', '#9b59b6'), ('TEST POINTS', 'testpoint.png', '#1e88e5'), ('DESBLOQUEIO', 'DESBLOQUEIOS.png', '#e74c3c'), ('DRILL', 'drill.png', '#4a6fa5')]
        self._cards_widgets_ordem = []
        for marca, icone, cor in marcas:
            card = self.criar_card_marca(marca, icone, cor)
            self._cards_widgets_ordem.append(card)
        try:
            if os.environ.get('UI_DASHBOARD_RESPONSIVE_GRID', '1') == '1':
                self._reorganizar_cards_grid_responsivo(force=True)
            else:
                self._aplicar_grid_legado_4_colunas()
        except Exception as exc:
            try:
                self._aplicar_grid_legado_4_colunas()
            except Exception:
                pass
            print('[grid_responsivo] usando layout legado (motivo: %s)' % type(exc).__name__)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        self.criar_menu()
    def criar_card_marca(self, marca, icone, cor_marca):
        '''Seletor de visual do card de marca/categoria.
Controlado por env var `UI_DASHBOARD_NEW_CARDS` (default "1"):
- "1": usa o card v2 horizontal moderno (BrandCardWidget).
- "0": usa o card legado vertical (preserva 100% do comportamento
  original como fallback).
Em qualquer falha do v2, faz fallback automatico para o legado.
Detalhes: administrativo/documentacao/19-05-2026--DASHBOARD-CARDS-MARCAS-REDESIGN/
'''
        if os.environ.get('UI_DASHBOARD_NEW_CARDS', '1') == '1':
            try:
                return self._criar_card_marca_v2(marca, icone, cor_marca)
            except Exception as exc:
                try:
                    import logging
                    logging.getLogger(__name__).warning('v2 card falhou (mantendo legado): %s', type(exc).__name__)
                except Exception:
                    exc = None
                    del exc
    def _criar_card_marca_v2(self, marca, icone, cor_marca):
        '''Card horizontal moderno usando BrandCardWidget.
        Delega 100% da renderizacao ao componente em
        `app/views/ui/brand_card_widget.py`. Esta funcao apenas:
        1. resolve o estado de acesso (mesmas regras do legado);
        2. resolve o path da imagem;
        3. instancia o widget e conecta os sinais publicos.
        '''
        from app.views.ui.brand_card_widget import BrandCardWidget
        nome_exibicao_map = {'ESQUEMAS ELETRICO': 'ESQUEMAS ELETRICOS'}
        nome_exibir = nome_exibicao_map.get(marca, marca)
        is_jumper_card = marca == 'JUMPER DE TELAS'
        if is_jumper_card:
            card_accessible = self.is_premium_user or self.is_admin
        else:
            card_accessible = self.is_premium_user or self.is_admin or self.is_com_user
        is_locked_premium = self.is_com_user and is_jumper_card
        if not card_accessible:
            estado = 'locked_premium' if is_locked_premium else 'locked'
        else:
            estado = 'acessivel'
        try:
            icon_path = PathManager.get_resource_path(f'logos/{icone}')
        except Exception:
            icon_path = ''
        try:
            texto_solucoes = self.translation_manager.get_text('see_solutions')
        except Exception:
            texto_solucoes = 'Ver solucoes'
        widget = BrandCardWidget(marca=marca, cor_marca=cor_marca, icon_path=icon_path, nome_exibir=nome_exibir, estado=estado, texto_botao_solucoes=texto_solucoes, translation_manager=self.translation_manager)
        widget.solucoes_requested.connect(self.abrir_solucoes)
        widget.upgrade_requested.connect(self.mostrar_info_upgrade)
        try:
            self.translation_manager.language_changed.connect(widget.refresh_translations)
        except Exception:
            pass
        return widget
    def _criar_card_marca_legado(self, marca, icone, cor_marca):
        card = QFrame()
        card.setFixedSize(250, 340)
        nome_exibicao_map = {'ESQUEMAS ELETRICO': 'ESQUEMAS EL├ëTRICOS'}
        nome_exibir = nome_exibicao_map.get(marca, marca)
        card.setObjectName('marcaCard')
        is_jumper_card = marca == 'JUMPER DE TELAS'
        if is_jumper_card:
            card_accessible = self.is_premium_user or self.is_admin
        else:
            card_accessible = self.is_premium_user or self.is_admin or self.is_com_user
        is_locked_premium = self.is_com_user and is_jumper_card
        if not card_accessible:
            if is_locked_premium:
                card.setStyleSheet('\n                    QFrame#marcaCard {\n                        background: linear-gradient(135deg, #f5f5f5 25%, #e0e0e0 25%, #e0e0e0 50%, #f5f5f5 50%, #f5f5f5 75%, #e0e0e0 75%);\n                        background-size: 20px 20px;\n                        border-radius: 12px;\n                        border: 2px solid #f39c12;\n                        padding: 15px;\n                    }\n                ')
            else:
                card.setStyleSheet('\n                    QFrame#marcaCard {\n                        background-color: #f5f5f5;\n                        border-radius: 12px;\n                        border: 2px solid #ddd;\n                        padding: 15px;\n                        opacity: 0.7;\n                    }\n                ')
        else:
            card.setStyleSheet('\n                QFrame#marcaCard {\n                    background-color: white;\n                    border-radius: 12px;\n                    border: 2px solid #eee;\n                    padding: 15px;\n                }\n            ')
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)
        logo_container = QFrame()
        logo_container.setFixedSize(160, 160)
        logo_container.setObjectName('logoContainer')
        logo_container.setStyleSheet('\n            QFrame#logoContainer {\n                background-color: #f8f9fa;\n                border-radius: 80px;\n                padding: 10px;\n            }\n        ')
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(5, 5, 5, 5)
        logo_layout.setSpacing(0)
        logo_layout.setAlignment(Qt.AlignCenter)
        logo_label = QLabel()
        logo_label.setFixedSize(140, 140)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setObjectName('logoLabel')
        logo_path = PathManager.get_resource_path(f'logos/{icone}')
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not card_accessible:
                temp_pixmap = QPixmap(pixmap.size())
                temp_pixmap.fill(Qt.transparent)
                painter = QPainter(temp_pixmap)
                painter.setOpacity(0.7 if is_locked_premium else 0.5)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                pixmap = temp_pixmap
            scaled_pixmap = pixmap.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setScaledContents(False)
        logo_layout.addWidget(logo_label)
        layout.addWidget(logo_container)
        nome = QLabel(nome_exibir)
        nome.setObjectName('marcaNome')
        nome.setStyleSheet(f'\n            QLabel#marcaNome {{\n                font-size: 14px;\n                font-weight: bold;\n                color: {cor_marca if card_accessible else '#999999' if not is_locked_premium else '#e67e22'};\n                padding: 5px;\n            }}\n        ')
        nome.setAlignment(Qt.AlignCenter)
        layout.addWidget(nome)
        if not card_accessible:
            if is_locked_premium:
                info_label = QLabel('Premium\nFazer Upgrade')
                info_label.setStyleSheet('\n                    color: #e67e22;\n                    font-size: 13px;\n                    font-weight: bold;\n                    padding: 8px;\n                    background: #fff8e1;\n                    border: 1px solid #f39c12;\n                    border-radius: 6px;\n                ')
                info_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(info_label)
                upgrade_btn = QPushButton('Ô¡É UPGRADE')
                upgrade_btn.setObjectName('upgradeButton')
                upgrade_btn.setCursor(Qt.PointingHandCursor)
                upgrade_btn.setFixedWidth(140)
                upgrade_btn.setStyleSheet('\n                    QPushButton#upgradeButton {\n                        background-color: #f39c12;\n                        color: white;\n                        border: none;\n                        padding: 8px 15px;\n                        border-radius: 6px;\n                        font-weight: bold;\n                        font-size: 13px;\n                    }\n                    QPushButton#upgradeButton:hover {\n                        background-color: #e67e22;\n                    }\n                ')
                upgrade_btn.clicked.connect(self.mostrar_info_upgrade)
                layout.addWidget(upgrade_btn)
                return card
            info_label = QLabel('Dispon├¡vel apenas para\nusu├írios Autorizados')
            info_label.setStyleSheet('\n                    color: #666;\n                    font-size: 12px;\n                    padding: 8px;\n                    background: #eee;\n                    border-radius: 6px;\n                ')
            info_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(info_label)
            return card
        btn = QPushButton(self.translation_manager.get_text('see_solutions'))
        btn.setObjectName('marcaButton')
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedWidth(140)
        btn.setStyleSheet(f'\n                QPushButton#marcaButton {{\n                    background-color: {cor_marca};\n                    color: white;\n                    border: none;\n                    padding: 8px 15px;\n                    border-radius: 6px;\n                    font-weight: bold;\n                    font-size: 13px;\n                }}\n                QPushButton#marcaButton:hover {{\n                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {cor_marca}, stop:1 {cor_marca}99);\n                }}\n                QPushButton#marcaButton:pressed {{\n                    background-color: {cor_marca};\n                }}\n            ')
        btn.clicked.connect((lambda: self.abrir_solucoes(marca)))
        layout.addWidget(btn)
        return card
    def criar_menu(self):
        '''Cria o menu superior'''
        menu_bar = self.menuBar()
        menu_android = menu_bar.addMenu(self.translation_manager.get_text('android_menu'))
        diagnostico_acao = QAction(self.translation_manager.get_text('diagnostic_action'), self)
        diagnostico_acao.triggered.connect(self.abrir_diagnostico)
        menu_android.addAction(diagnostico_acao)
        uart_acao = QAction('UART Monitor', self)
        uart_acao.triggered.connect(self.abrir_uart_monitor)
        menu_android.addAction(uart_acao)
        manual_acao = QAction(self.translation_manager.get_text('manual_action'), self)
        manual_acao.triggered.connect(self.mostrar_manual)
        menu_android.addAction(manual_acao)
        menu_arquivos = menu_bar.addMenu(self.translation_manager.get_text('files_menu'))
        arquivos_acao = QAction(self.translation_manager.get_text('files_action'), self)
        arquivos_acao.triggered.connect(self.abrir_arquivos)
        menu_arquivos.addAction(arquivos_acao)
        menu_os = menu_bar.addMenu(self.translation_manager.get_text('service_orders_menu'))
        os_acao = QAction(self.translation_manager.get_text('service_orders_action'), self)
        os_acao.triggered.connect(self.abrir_sistema_os)
        menu_os.addAction(os_acao)
        menu_parceiros = menu_bar.addMenu(self.translation_manager.get_text('partners_menu'))
        parceiros_acao = QAction(self.translation_manager.get_text('partners_action'), self)
        parceiros_acao.triggered.connect(self.abrir_parceiros)
        menu_parceiros.addAction(parceiros_acao)
        menu_usuario = menu_bar.addMenu('Usuario')
        ver_perfil_acao = QAction('Ver Meu Perfil', self)
        ver_perfil_acao.triggered.connect(self.ver_perfil)
        menu_usuario.addAction(ver_perfil_acao)
        editar_perfil_acao = QAction('Editar Meu Perfil', self)
        editar_perfil_acao.triggered.connect(self.abrir_perfil)
        menu_usuario.addAction(editar_perfil_acao)
        menu_licenca = menu_bar.addMenu('Licenca')
        status_licenca_acao = QAction('Status da Licenca', self)
        status_licenca_acao.triggered.connect(self.mostrar_status_licenca)
        menu_licenca.addAction(status_licenca_acao)
        renovar_licenca_acao = QAction('Renovar Licenca', self)
        renovar_licenca_acao.triggered.connect(self.abrir_renovacao_licenca)
        menu_licenca.addAction(renovar_licenca_acao)
        if self.is_premium_user or self.is_admin:
            menu_servidor_os = menu_bar.addMenu('Servidor OS')
            iniciar_servidor_acao = QAction('Iniciar Servidor (Rede)', self)
            iniciar_servidor_acao.triggered.connect(self.iniciar_servidor_os_rede)
            menu_servidor_os.addAction(iniciar_servidor_acao)
            parar_servidor_acao = QAction('Parar Servidor', self)
            parar_servidor_acao.triggered.connect(self.parar_servidor_os)
            menu_servidor_os.addAction(parar_servidor_acao)
            reiniciar_servidor_acao = QAction('Reiniciar Servidor', self)
            reiniciar_servidor_acao.triggered.connect(self.reiniciar_servidor_os)
            menu_servidor_os.addAction(reiniciar_servidor_acao)
            menu_servidor_os.addSeparator()
            status_servidor_acao = QAction('Ver Status', self)
            status_servidor_acao.triggered.connect(self.mostrar_status_servidor_os)
            menu_servidor_os.addAction(status_servidor_acao)
        menu_idioma = menu_bar.addMenu('Idioma / Language')
        idioma_acao = QAction('Alterar Idioma / Change Language', self)
        idioma_acao.triggered.connect(self.change_language)
        menu_idioma.addAction(idioma_acao)
        menu_opcoes = menu_bar.addMenu(self.translation_manager.get_text('options_menu'))
        self.toggle_fullscreen_acao = QAction('Alternar Tela Cheia', self)
        self.toggle_fullscreen_acao.setShortcut('F11')
        self.toggle_fullscreen_acao.triggered.connect(self.toggle_fullscreen)
        menu_opcoes.addAction(self.toggle_fullscreen_acao)
        _is_dark = QSettings('TechUnion', 'UNION').value('theme/dark_mode', False, type=bool)
        self.toggle_dark_acao = QAction('Modo Claro' if _is_dark else 'Modo Escuro', self)
        self.toggle_dark_acao.triggered.connect(self.toggle_dark_mode)
        menu_opcoes.addAction(self.toggle_dark_acao)
        menu_opcoes.addSeparator()
        sobre_acao = QAction(self.translation_manager.get_text('about_action'), self)
        sobre_acao.triggered.connect(self.mostrar_sobre)
        menu_opcoes.addAction(sobre_acao)
        quantidade_acao = QAction(self.translation_manager.get_text('quantity_solutions_action'), self)
        quantidade_acao.triggered.connect(self.mostrar_quantidade_solucoes)
        menu_opcoes.addAction(quantidade_acao)
        fechar_acao = QAction(self.translation_manager.get_text('exit_action'), self)
        fechar_acao.triggered.connect(self.close)
        menu_opcoes.addAction(fechar_acao)
        menu_ajuda = menu_bar.addMenu(self.translation_manager.get_text('help_menu'))
        ajuda_portal_acao = QAction(self.translation_manager.get_text('help_portal'), self)
        ajuda_portal_acao.triggered.connect(self.abrir_ajuda)
        menu_ajuda.addAction(ajuda_portal_acao)
        menu_assistentes = menu_bar.addMenu('Assistentes IA')
        union_assistente_acao = QAction('UNION ASSISTENTE', self)
        union_assistente_acao.triggered.connect(self.abrir_union_assistente)
        font_assistente = union_assistente_acao.font()
        font_assistente.setBold(True)
        union_assistente_acao.setFont(font_assistente)
        menu_assistentes.addAction(union_assistente_acao)
    def mostrar_sobre(self):
        '''Mostra di├ílogo Sobre'''
        self.translation_manager.clear_cache()
        QMessageBox.about(self, self.translation_manager.get_text('about_title'), self.translation_manager.get_text('about_text'))
    def mostrar_quantidade_solucoes(self):
        '''Mostra quantidade total de solu├º├Áes'''
        try:
            cursor = self.cursor
            cursor.execute("SELECT COUNT(*) FROM solucoes WHERE status='ativo'")
            total = cursor.fetchone()[0]
            QMessageBox.information(self, self.translation_manager.get_text('quantity_solutions_title'), self.translation_manager.get_text('quantity_solutions_text').format(total))
            return
        except Exception as e:
            QMessageBox.critical(self, self.translation_manager.get_text('error_title'), self.translation_manager.get_text('error_text').format(str(e)))
    def abrir_solucoes(self, marca):
        '''Abre a janela de solu├º├Áes para a marca selecionada'''
        try:
            if not self._ci.check():
                return
            if self.is_com_user and marca == 'JUMPER DE TELAS':
                self.mostrar_bloqueio_premium('JUMPER DE TELAS')
                return
            if hasattr(self, 'solucoes_window') and self.solucoes_window is not None:
                pass
            try:
                if self.solucoes_window.isVisible():
                    if self.solucoes_window.marca == marca:
                        self.solucoes_window.setWindowState(self.solucoes_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
                        self.solucoes_window.showMaximized()
                        self.solucoes_window.raise_()
                        self.solucoes_window.activateWindow()
                        self.statusBar().showMessage(f'Solu├º├Áes {marca} j├í est├í aberto ÔÇö trazendo para frente...', 2000)
                        return
                    self.solucoes_window.close()
            except RuntimeError:
                pass
            else:
                from app.views.solucoes_view import SolucoesWindow
                self.solucoes_window = SolucoesWindow(marca, self)
                self.solucoes_window.setWindowFlags(Qt.Window)
                self.solucoes_window.setWindowModality(Qt.NonModal)
                self.solucoes_window.setMinimumSize(800, 600)
                if not self.pode_gravar_tela():
                    protect_window_from_capture_extended(self.solucoes_window, True)
                self.solucoes_window.showMaximized()
        except Exception as e:
            QMessageBox.critical(self, self.translation_manager.get_text('error_title'), self.translation_manager.get_text('error_text').format(str(e)))
    def logout(self):
        '''Faz logout e volta para tela de login'''
        reply = QMessageBox.question(self, self.translation_manager.get_text('confirm_exit_title'), self.translation_manager.get_text('confirm_exit_text'), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.close()
            self.login = LoginWindow()
            self.login.show()
    def abrir_diagnostico(self):
        '''Abre janela de diagn├│stico Android'''
        try:
            if not self._ci.check():
                return
            if hasattr(self, 'diagnostico_window') and self.diagnostico_window is not None:
                pass
            try:
                if self.diagnostico_window.isVisible():
                    self.diagnostico_window.setWindowState(self.diagnostico_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
                    self.diagnostico_window.showMaximized()
                    self.diagnostico_window.raise_()
                    self.diagnostico_window.activateWindow()
                    self.statusBar().showMessage('Diagn├│stico j├í est├í aberto ÔÇö trazendo para frente...', 2000)
                    print('Ô£à Janela Diagn├│stico j├í aberta, trazendo para frente')
            except RuntimeError:
                pass
            else:
                return
        except Exception as e:
            QMessageBox.critical(self, self.translation_manager.get_text('error_title'), self.translation_manager.get_text('error_text').format(str(e)))
    def mostrar_manual(self):
        '''Abre o manual de uso'''
        try:
            from app.views.manual_android import ManualAndroid
            self.manual_window = ManualAndroid(self)
            self.manual_window.show()
            return
        except Exception as e:
            QMessageBox.critical(self, self.translation_manager.get_text('error_title'), self.translation_manager.get_text('error_text').format(str(e)))
    def abrir_minhas_solucoes(self):
        '''Abre a janela de minhas solu├º├Áes'''
        try:
            if not self._ci.check():
                return
            if hasattr(self, 'minhas_solucoes_window') and self.minhas_solucoes_window is not None:
                pass
            try:
                if self.minhas_solucoes_window.isVisible():
                    self.minhas_solucoes_window.setWindowState(self.minhas_solucoes_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
                    self.minhas_solucoes_window.showMaximized()
                    self.minhas_solucoes_window.raise_()
                    self.minhas_solucoes_window.activateWindow()
                    self.statusBar().showMessage('Minhas Solu├º├Áes j├í est├í aberto ÔÇö trazendo para frente...', 2000)
                    print('Ô£à Janela Minhas Solu├º├Áes j├í aberta, trazendo para frente')
            except RuntimeError:
                pass
            else:
                return
        except Exception as e:
            QMessageBox.critical(self, self.translation_manager.get_text('error_title'), self.translation_manager.get_text('error_text').format(str(e)))
    def abrir_parceiros(self):
        '''Abre a janela de parceiros'''
        try:
            from app.views.parceiros_view import ParceirosWindow
            self.parceiros_window = ParceirosWindow(self)
            self.parceiros_window.show()
            return
        except Exception as e:
            QMessageBox.critical(self, self.translation_manager.get_text('error_title'), self.translation_manager.get_text('error_text').format(str(e)))
    def abrir_sistema_os(self):
        '''Abre o sistema de ordens de servi├ºo'''
        try:
            if hasattr(self, 'os_window') and self.os_window is not None:
                pass
            try:
                if self.os_window.isVisible():
                    self.os_window.setWindowState(self.os_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
                    self.os_window.showMaximized()
                    self.os_window.raise_()
                    self.os_window.activateWindow()
                    self.statusBar().showMessage('Sistema O.S. j├í est├í aberto ÔÇö trazendo para frente...', 2000)
                    print('Ô£à Janela Sistema O.S. j├í aberta, trazendo para frente')
            except RuntimeError:
                pass
            else:
                return
        except Exception as e:
            QMessageBox.critical(self, self.translation_manager.get_text('error_title'), self.translation_manager.get_text('error_text').format(str(e)))
    def change_language(self):
        '''Abre o di├ílogo de sele├º├úo de idioma'''
        dialog = LanguageSelectorDialog(self)
        if dialog.exec_() == LanguageSelectorDialog.Accepted:
            self.refresh_interface()
    def toggle_fullscreen(self):
        '''Alterna entre tela cheia e janela normal'''
        if self.isMaximized():
            self.showNormal()
            self.center_window()
            self.fullscreen_mode = False
            self.toggle_fullscreen_acao.setText('Maximizar Janela')
            self.statusBar().showMessage('Janela redimensionada para o modo normal', 2000)
            return
        self.showMaximized()
        self.fullscreen_mode = True
        self.toggle_fullscreen_acao.setText('Reduzir Janela')
        self.statusBar().showMessage('Janela maximizada - Pressione F11 para alternar', 2000)
    def toggle_dark_mode(self):
        '''Alterna entre tema escuro (QDarkStyle) e claro (Fusion padr├úo)'''
        settings = QSettings('TechUnion', 'UNION')
        is_dark = settings.value('theme/dark_mode', False, type=bool)
        if is_dark:
            QApplication.instance().setStyleSheet('')
            settings.setValue('theme/dark_mode', False)
            if hasattr(self, 'toggle_dark_acao'):
                self.toggle_dark_acao.setText('Modo Escuro')
            self.statusBar().showMessage('Tema claro aplicado', 3000)
            return
        try:
            import qdarkstyle
            QApplication.instance().setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
            settings.setValue('theme/dark_mode', True)
            if hasattr(self, 'toggle_dark_acao'):
                self.toggle_dark_acao.setText('Modo Claro')
            self.statusBar().showMessage('Tema escuro aplicado', 3000)
            return
        except Exception as e:
            QMessageBox.warning(self, 'Tema Indispon├¡vel', f'QDarkStyle n├úo est├í instalado.\n\nPara habilitar o tema escuro, execute:\npip install qdarkstyle\n\nErro: {type(e).__name__}: {e}')
    def refresh_interface(self):
        '''Atualiza a interface com o novo idioma'''
        self.setWindowTitle(self.translation_manager.get_text('system_title'))
        if hasattr(self, 'toggle_fullscreen_acao'):
            if self.isMaximized():
                self.toggle_fullscreen_acao.setText('Reduzir Janela')
            else:
                self.toggle_fullscreen_acao.setText('Maximizar Janela')
        for widget in self.findChildren(QLabel):
            if widget.text() == 'TECH UNION SOLUTIONS':
                continue
            obj_name = widget.objectName()
            if obj_name == 'userLabel':
                if self.user_email:
                    username = self.user_email.split('@')[0]
                else:
                    username = 'Usu├írio'
                widget.setText(username)
                continue
            if obj_name == 'adminLabel':
                widget.setText('Modo Administrador')
                continue
            if obj_name == 'licenseLabel':
                continue
            if obj_name == 'premiumLabel':
                widget.setText('Plano Premium')
                continue
            if 'slogan' in widget.styleSheet():
                widget.setText(self.translation_manager.get_text('slogan'))
                continue
            if 'user' not in widget.text():
                if 'User' in widget.text() or 'Usuario' in widget.text():
                    if self.user_email:
                        username = self.user_email.split('@')[0]
                    else:
                        username = 'Usu├írio'
                    widget.setText(username)
                    continue
            if 'Modo Administrador' not in widget.text() and 'Administrator Mode' not in widget.text():
                continue
            widget.setText('Modo Administrador')
            continue
        for btn in self.findChildren(QPushButton):
            if btn.objectName() == 'uartButton':
                btn.setText('­ƒôè ' + self.translation_manager.get_text('uart_monitor'))
                continue
            if btn.objectName() == 'tiravirusButton':
                btn.setText('­ƒøí´©Å ' + self.translation_manager.get_text('antivirus'))
                continue
            if btn.objectName() == 'serverButton':
                btn.setText('­ƒîÉ Server GSM')
                continue
            if btn.objectName() == 'toolsButton':
                btn.setText('­ƒöº ' + self.translation_manager.get_text('tools'))
                continue
            if btn.objectName() == 'marcaButton':
                btn.setText(self.translation_manager.get_text('see_solutions'))
                continue
            if btn.objectName() == 'systemButton':
                btn.setText('­ƒÆ╗ ' + self.translation_manager.get_text('system_os'))
                continue
            if btn.objectName() == 'solutionsButton':
                btn.setText('­ƒô▒ ' + self.translation_manager.get_text('my_solutions'))
                continue
            if btn.objectName() == 'peliculasButton':
                btn.setText(self.translation_manager.get_text('peliculas'))
                continue
            if btn.objectName() != 'btnVerTodas':
                continue
            btn.setText(self.translation_manager.get_text('view_all'))
            continue
        menu_bar = self.menuBar()
        menu_bar.clear()
        self.criar_menu()
    def abrir_uart_monitor(self):
        '''Abre a janela do monitor UART'''
        try:
            if not self._ci.check():
                return
            if hasattr(self, 'uart_window') and self.uart_window is not None:
                pass
            try:
                if self.uart_window.isVisible():
                    self.uart_window.setWindowState(self.uart_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
                    self.uart_window.showMaximized()
                    self.uart_window.raise_()
                    self.uart_window.activateWindow()
                    self.statusBar().showMessage('UART Monitor j├í est├í aberto ÔÇö trazendo para frente...', 2000)
                    print('Ô£à Janela UART Monitor j├í aberta, trazendo para frente')
            except RuntimeError:
                pass
            else:
                return
        except Exception as e:
            print(f'ÔØî Erro ao abrir UART Monitor: {str(e)}')
            QMessageBox.critical(self, 'Erro', 'Erro ao abrir UART Monitor. Tente novamente.')
    def abrir_mtk_flash_tools(self):
        '''Abre o MTK Tools com suporte a extra├º├úo protegida'''
        try:
            from app.utils.mtk_manager import get_mtk_manager
            mtk_manager = get_mtk_manager()
            if mtk_manager.esta_rodando():
                QMessageBox.information(self, 'MTK Tools', 'A ferramenta j├í est├í em execu├º├úo.\n\nVerifique se a janela est├í minimizada ou atr├ís de outras janelas.')
                self.statusBar().showMessage('MTK Tools j├í est├í ativo', 2000)
                return
            disponivel, mensagem = mtk_manager.verificar_disponibilidade()
            if not disponivel:
                if mensagem == 'NEEDS_DOWNLOAD':
                    self._baixar_e_abrir_mtk(mtk_manager)
                    return
            if not disponivel:
                QMessageBox.warning(self, 'Servi├ºo Indispon├¡vel', 'N├úo foi poss├¡vel carregar a ferramenta.\n\nSugest├Áes:\nÔÇó Verifique sua conex├úo com a internet\nÔÇó Reinicie o programa\nÔÇó Contate o suporte se persistir')
                return
            if mtk_manager.requer_extracao():
                self._extrair_e_abrir_mtk(mtk_manager)
                return
            self._abrir_mtk_direto(mtk_manager)
            return
        except Exception:
            QMessageBox.critical(self, 'Erro', 'N├úo foi poss├¡vel iniciar a ferramenta.\n\nSugest├Áes:\nÔÇó Reinicie o programa\nÔÇó Verifique seu antiv├¡rus\nÔÇó Contate o suporte se persistir')
    def _baixar_e_abrir_mtk(self, mtk_manager):
        '''Baixa MTK do servidor e depois extrai com barra de progresso'''
        from PyQt5.QtWidgets import QProgressDialog
        from PyQt5.QtCore import (Qt, QThread, pyqtSignal)
        class DownloadWorker(QThread):
            progress = pyqtSignal(int, str)
            finished = pyqtSignal(bool, str)
            def run(self):
                import logging
                _dl_log = logging.getLogger('MTK_DL')
                try:
                    from app.utils._res_loader import (_cache_dir, _sha256, _download_r2, _download_http, consultar_catalogo)
                    import os
                    self.progress.emit(5, 'Verificando recursos...')
                    arquivo = 'mtk_tools.zip'
                    catalogo = consultar_catalogo(arquivo)
                    sha_esperado = catalogo.get('sha256', '') if catalogo else ''
                    url_fb = catalogo.get('url', '') if catalogo else ''
                    _dl_log.debug('catalogo=%s sha=%s url_fb=%s', bool(catalogo), bool(sha_esperado), bool(url_fb))
                    cache = _cache_dir()
                    destino = os.path.join(cache, arquivo)
                    _dl_log.debug('destino=%s dir_exists=%s', destino, os.path.isdir(cache))
                    self.progress.emit(10, 'Baixando ferramenta...')
                    r2_ok = _download_r2(arquivo, destino)
                    _dl_log.debug('r2_ok=%s file_exists=%s', r2_ok, os.path.isfile(destino))
                    if r2_ok:
                        self.progress.emit(70, 'Verificando integridade...')
                        if sha_esperado:
                            sha_real = _sha256(destino)
                            if sha_real != sha_esperado:
                                _dl_log.warning('SHA mismatch: %s != %s', sha_real[:16], sha_esperado[:16])
                    try:
                        os.remove(destino)
                    except Exception:
                        pass
                    else:
                        self.finished.emit(False, '')
                        return
                except Exception as exc:
                    _dl_log.error('Erro critico no worker: %s', exc)
                    self.finished.emit(False, '')
                _dl_log.warning('Todas as fontes falharam')
                self.finished.emit(False, '')
        progress = QProgressDialog(self)
        progress.setWindowTitle('MTK Tools')
        progress.setLabelText('Preparando ferramenta...')
        progress.setMinimum(0)
        progress.setMaximum(100)
        progress.setValue(0)
        progress.setCancelButton(None)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumWidth(350)
        progress.setStyleSheet('\n            QProgressDialog {\n                background-color: #1a1a2e;\n                border: 2px solid #00d4aa;\n                border-radius: 10px;\n            }\n            QLabel {\n                color: white;\n                font-size: 13px;\n                font-weight: bold;\n                padding: 10px;\n            }\n            QProgressBar {\n                border: 2px solid #00d4aa;\n                border-radius: 5px;\n                background-color: #16213e;\n                text-align: center;\n                color: white;\n                font-weight: bold;\n            }\n            QProgressBar::chunk {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n                    stop:0 #00d4aa, stop:1 #00a388);\n                border-radius: 3px;\n            }\n        ')
        self._mtk_dl_worker = DownloadWorker()
        def on_dl_progress(percent, msg):
            progress.setValue(percent)
            progress.setLabelText(msg)
        def on_dl_finished(sucesso, resultado):
            progress.close()
            if sucesso:
                cached_path = resultado
                mtk_manager.zip_extractor._find_zip_path = lambda: cached_path
                mtk_manager.mtk_path = 'ZIP_MODE'
                self._extrair_e_abrir_mtk(mtk_manager)
                return
            QMessageBox.warning(self, 'Servi├ºo Indispon├¡vel', 'N├úo foi poss├¡vel obter a ferramenta.\n\nSugest├Áes:\nÔÇó Verifique sua conex├úo com a internet\nÔÇó Tente novamente em alguns minutos\nÔÇó Contate o suporte se persistir')
        self._mtk_dl_worker.progress.connect(on_dl_progress)
        self._mtk_dl_worker.finished.connect(on_dl_finished)
        progress.show()
        self._mtk_dl_worker.start()
    def _extrair_e_abrir_mtk(self, mtk_manager):
        '''Extrai MTK do ZIP com barra de progresso elegante'''
        from PyQt5.QtWidgets import QProgressDialog
        from PyQt5.QtCore import (Qt, QThread, pyqtSignal)
        class ExtractWorker(QThread):
            progress = pyqtSignal(int, str)
            finished = pyqtSignal(bool, str)
            def __init__(self, manager):
                super().__init__()
                self.manager = manager
            def run(self):
                def callback(percent, msg):
                    self.progress.emit(percent, msg)
                sucesso, resultado = self.manager.extrair_zip(callback)
                self.finished.emit(sucesso, resultado)
        progress = QProgressDialog(self)
        progress.setWindowTitle('MTK Tools')
        progress.setLabelText('Preparando ferramenta...')
        progress.setMinimum(0)
        progress.setMaximum(100)
        progress.setValue(0)
        progress.setCancelButton(None)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumWidth(350)
        progress.setStyleSheet('\n            QProgressDialog {\n                background-color: #1a1a2e;\n                border: 2px solid #00d4aa;\n                border-radius: 10px;\n            }\n            QLabel {\n                color: white;\n                font-size: 13px;\n                font-weight: bold;\n                padding: 10px;\n            }\n            QProgressBar {\n                border: 2px solid #00d4aa;\n                border-radius: 5px;\n                background-color: #16213e;\n                text-align: center;\n                color: white;\n                font-weight: bold;\n            }\n            QProgressBar::chunk {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n                    stop:0 #00d4aa, stop:1 #00a388);\n                border-radius: 3px;\n            }\n        ')
        self._mtk_worker = ExtractWorker(mtk_manager)
        def on_progress(percent, msg):
            progress.setValue(percent)
            progress.setLabelText(msg)
        def on_finished(sucesso, resultado):
            progress.close()
            if sucesso:
                self._abrir_mtk_direto(mtk_manager)
                return
            QMessageBox.warning(self, 'Erro', 'N├úo foi poss├¡vel preparar a ferramenta.\n\nSugest├Áes:\nÔÇó Reinicie o programa\nÔÇó Contate o suporte se persistir')
        self._mtk_worker.progress.connect(on_progress)
        self._mtk_worker.finished.connect(on_finished)
        progress.show()
        self._mtk_worker.start()
    def _abrir_mtk_direto(self, mtk_manager):
        '''Abre o MTK diretamente (j├í extra├¡do ou sem ZIP)'''
        sucesso, mensagem = mtk_manager.abrir()
        if sucesso:
            self.statusBar().showMessage('MTK Tools iniciado', 3000)
            QMessageBox.information(self, 'MTK Tools', 'Ferramenta iniciada com sucesso.\n\nEspecializada para dispositivos MediaTek.\n\nA interface ir├í abrir em alguns instantes.')
            return
        if mensagem != 'NEEDS_EXTRACT':
            QMessageBox.critical(self, 'Erro', mensagem)
    def abrir_os_manager(self):
        '''Abre o Union OS Manager - Sistema de Ordens de Servi├ºo'''
        if not self._ci.check():
            return
        if not self.is_premium_user and not self.is_admin:
            self.mostrar_bloqueio_premium('OS NEW')
            return
        try:
            from app.utils.os_manager import get_os_manager, ModoServidor
            os_manager = get_os_manager()
            if os_manager.esta_rodando():
                url = os_manager.obter_url()
                self._abrir_os_no_navegador(url)
                self.statusBar().showMessage('OS NEW j├í ativo ÔÇö abrindo navegador', 2000)
                return
            disponivel, mensagem = os_manager.verificar_disponibilidade()
            if not disponivel:
                QMessageBox.warning(self, 'Sistema Indispon├¡vel', mensagem)
                return
            if os_manager.precisa_provisionar_runtime():
                ok, msg = self._provisionar_runtime_os(os_manager)
                if not ok:
                    QMessageBox.warning(self, 'Prepara├º├úo', msg)
                    return
            sucesso, mensagem = os_manager.iniciar(ModoServidor.LOCAL)
            if sucesso:
                self.statusBar().showMessage('OS NEW iniciado com sucesso', 3000)
                url = os_manager.obter_url()
                self._abrir_os_no_navegador(url)
                return
            QMessageBox.critical(self, 'Erro ao Iniciar', mensagem)
            return
        except Exception as e:
            print(f'[DEBUG] Erro ao abrir OS Manager: {e}')
            QMessageBox.critical(self, 'Erro Inesperado', 'N├úo foi poss├¡vel iniciar o sistema.\n\nSugest├Áes:\nÔÇó Tente novamente\nÔÇó Reinicie o TECH UNION SOLUTIONS\nÔÇó Se persistir, contate o suporte')
    _OS_RETRY_COOLDOWN_S: float = 5.0
    def _provisionar_runtime_os(self, os_manager) -> tuple:
        '''
Pre-flight do OS Manager: provisiona recursos sob demanda com QProgressDialog.
Executado em QThread separada para nao travar a UI durante o download.
Aplica controle anti-spam (lock + cooldown) para evitar tentativas
paralelas que poderiam corromper cache ou sobrecarregar a rede.
Returns:
    tuple (sucesso: bool, mensagem: str)
'''
        import time as _time
        import threading as _threading
        from PyQt5.QtWidgets import QProgressDialog
        from PyQt5.QtCore import (Qt, QThread, pyqtSignal)
        if not hasattr(self, '_os_provision_lock'):
            self._os_provision_lock = _threading.Lock()
            self._os_last_attempt_ts = 0.0
        if not self._os_provision_lock.acquire(blocking=False):
            return (False, 'O preparo j├í est├í em andamento.\n\nAguarde a conclus├úo da opera├º├úo atual.')
        try:
            agora = _time.time()
            intervalo = agora - self._os_last_attempt_ts
            cooldown = self._OS_RETRY_COOLDOWN_S
            if 0 < intervalo < cooldown:
                falta = max(1, int(cooldown - intervalo) + 1)
                try:
                    self._os_provision_lock.release()
                except Exception:
                    return
                return False, f'Aguarde {falta} segundos antes de tentar novamente.\n\nIsso ajuda a evitar problemas em caso de instabilidade na rede.'
            self._os_last_attempt_ts = agora
            class _ProvisionWorker(QThread):
                progresso = pyqtSignal(int, str)
                concluido = pyqtSignal(bool, str)
                def __init__(self, mgr):
                    super().__init__()
                    self._mgr = mgr
                def run(self):
                    ok, msg = self._mgr.provisionar_runtime(progress_callback=(lambda p, m: self.progresso.emit(p, m)))
                    self.concluido.emit(ok, msg)
            progress = QProgressDialog(self)
            progress.setWindowTitle('OS NEW ÔÇö Preparando')
            progress.setLabelText('Verificando recursos...')
            progress.setMinimum(0)
            progress.setMaximum(100)
            progress.setValue(0)
            progress.setCancelButton(None)
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumWidth(400)
            progress.setMinimumDuration(0)
            progress.setStyleSheet('\n                QProgressDialog {\n                    background-color: #1a1a2e;\n                    border: 2px solid #00d4aa;\n                    border-radius: 10px;\n                }\n                QLabel {\n                    color: white;\n                    font-size: 12px;\n                    font-weight: bold;\n                    padding: 8px;\n                }\n                QProgressBar {\n                    border: 2px solid #00d4aa;\n                    border-radius: 5px;\n                    background-color: #16213e;\n                    text-align: center;\n                    color: white;\n                    font-weight: bold;\n                }\n                QProgressBar::chunk {\n                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n                        stop:0 #00d4aa, stop:1 #00f0c0);\n                    border-radius: 3px;\n                }\n            ')
            resultado = {'ok': False, 'msg': ''}
            worker = _ProvisionWorker(os_manager)
            def _on_progress(pct, msg):
                try:
                    progress.setValue(pct)
                    progress.setLabelText(msg)
                    return
                except Exception:
                    return
            def _on_done(ok, msg):
                resultado['ok'] = ok
                resultado['msg'] = msg
                progress.setValue(100)
                progress.close()
            worker.progresso.connect(_on_progress)
            worker.concluido.connect(_on_done)
            worker.start()
            progress.exec_()
            worker.wait(2000)
        finally:
            try:
                self._os_provision_lock.release()
            except Exception:
                pass
        return resultado['ok'], resultado['msg']
    def _abrir_os_no_navegador(self, url: str):
        '''Abre o OS NEW.'''
        aberto_externo = False
        try:
            aberto_externo = bool(webbrowser.open(url))
        except Exception:
            aberto_externo = False
        if aberto_externo:
            try:
                self.statusBar().showMessage('OS NEW aberto.', 3000)
            except Exception:
                pass
            return
        try:
            from app.utils.web_view_widget import WebViewManager
            web_manager = WebViewManager()
            web_manager.abrir_url(url, 'OS NEW ÔÇö Ordens de Servi├ºo')
        except Exception:
            pass
        try:
            try:
                self.statusBar().showMessage('OS NEW aberto.', 3000)
            except Exception:
                return
        except Exception:
            pass
    def iniciar_servidor_os_rede(self):
        '''Inicia o servidor OS em modo REDE para acesso de outros terminais'''
        try:
            from app.utils.os_manager import get_os_manager
            os_manager = get_os_manager()
            if os_manager.precisa_provisionar_runtime():
                ok, msg = self._provisionar_runtime_os(os_manager)
                if not ok:
                    QMessageBox.warning(self, 'Prepara├º├úo', msg)
                    return
            sucesso, mensagem = os_manager.iniciar_servidor_rede()
            if sucesso:
                info = os_manager.obter_info_rede()
                QMessageBox.information(self, 'Servidor OS ÔÇö Modo Rede', f'Servidor iniciado com sucesso.\n\nURL Local: {info['url_local']}\nURL Rede:  {info['url_rede']}\n\nOutros dispositivos na mesma rede\npodem acessar usando a URL de rede.')
                self.statusBar().showMessage(f'Servidor OS ativo: {info['url_rede']}', 5000)
                return
            QMessageBox.warning(self, 'Servidor OS', mensagem)
            return
        except Exception as e:
            print(f'[DEBUG] Erro ao iniciar servidor: {e}')
            QMessageBox.critical(self, 'Erro', 'Erro ao iniciar servidor.')
    def parar_servidor_os(self):
        '''Para o servidor OS'''
        try:
            from app.utils.os_manager import get_os_manager
            os_manager = get_os_manager()
            if not os_manager.esta_rodando():
                QMessageBox.information(self, 'Servidor OS', 'O servidor j├í est├í parado.')
                return
            sucesso, mensagem = os_manager.parar()
            if sucesso:
                QMessageBox.information(self, 'Servidor OS', mensagem)
                self.statusBar().showMessage('Servidor OS parado', 3000)
                return
            QMessageBox.warning(self, 'Servidor OS', mensagem)
            return
        except Exception as e:
            print(f'[DEBUG] Erro ao parar servidor: {e}')
            QMessageBox.critical(self, 'Erro', 'Erro ao parar servidor.')
    def reiniciar_servidor_os(self):
        '''Reinicia o servidor OS'''
        try:
            from app.utils.os_manager import get_os_manager
            os_manager = get_os_manager()
            if os_manager.precisa_provisionar_runtime():
                ok, msg = self._provisionar_runtime_os(os_manager)
                if not ok:
                    QMessageBox.warning(self, 'Prepara├º├úo', msg)
                    return
            sucesso, mensagem = os_manager.reiniciar()
            if sucesso:
                info = os_manager.obter_info_rede()
                modo = 'REDE' if os_manager.modo.value == 'rede' else 'LOCAL'
                QMessageBox.information(self, 'Servidor OS Reiniciado', f'Servidor reiniciado com sucesso.\n\nModo: {modo}\nURL:  {os_manager.obter_url()}')
                self.statusBar().showMessage('Servidor OS reiniciado', 3000)
                return
            QMessageBox.warning(self, 'Servidor OS', mensagem)
            return
        except Exception as e:
            print(f'[DEBUG] Erro ao reiniciar servidor: {e}')
            QMessageBox.critical(self, 'Erro', 'Erro ao reiniciar servidor.')
    def mostrar_status_servidor_os(self):
        '''Mostra o status atual do servidor OS'''
        try:
            from app.utils.os_manager import get_os_manager
            os_manager = get_os_manager()
            info = os_manager.obter_info_rede()
            status = 'ATIVO' if info['rodando'] else 'PARADO'
            modo = 'REDE (acess├¡vel na LAN)' if info['modo'] == 'rede' else 'LOCAL (apenas esta m├íquina)'
            msg = f'STATUS DO SERVIDOR OS\n{'========================================'}\n\nStatus: {status}\nModo:   {modo}\nPorta:  {info['porta']}\n\nURL Local: {info['url_local']}\nURL Rede:  {info['url_rede']}\nIP Local:  {info['ip_local']}'
            QMessageBox.information(self, 'Status do Servidor OS', msg)
            return
        except Exception as e:
            print(f'[DEBUG] Erro ao obter status: {e}')
            QMessageBox.critical(self, 'Erro', 'Erro ao obter status do servidor.')
    def abrir_arquivos(self):
        '''Abre os links para download de firmwares'''
        dialog = QMessageBox(self)
        dialog.setWindowTitle('Links para Download de Firmware')
        dialog.setIcon(QMessageBox.Information)
        texto_html = "\n        <h3 style='color: #2980b9;'>Sites para Download de Firmware</h3>\n        <p>Escolha o fabricante do dispositivo:</p>\n        \n        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 5px;'>\n            <p><b>Xiaomi:</b> <a href='https://mifirm.net/list/model'>mifirm.net</a></p>\n            <p><b>Samsung:</b> <a href='https://samfw.com/firmware/SM-A715F'>samfw.com</a></p>\n            <p><b>LG:</b> <a href='https://lgrom.com/'>lgrom.com</a></p>\n            <p><b>Apple:</b> <a href='https://ipsw.me/'>ipsw.me</a></p>\n        </div>\n        \n        <p style='color: #7f8c8d; margin-top: 10px;'><small>Clique nos links acima para acessar os sites de download</small></p>\n        "
        dialog.setText(texto_html)
        dialog.setTextFormat(Qt.RichText)
        dialog.setStandardButtons(QMessageBox.Ok)
        ok_btn = dialog.button(QMessageBox.Ok)
        ok_btn.setText('Fechar')
        dialog.finished.connect((lambda: None))
        try:
            dialog.exec_()
            return
        except Exception as e:
            QMessageBox.warning(self, 'Erro ao Abrir Links', 'N├úo foi poss├¡vel abrir a janela de links.\nPor favor, entre em contato com o suporte:\n\nWhatsApp: (85) 99750-7465')
    def abrir_ajuda(self):
        '''Abre mini-painel moderno com canais de aulas e suporte.'''
        dialog = QDialog(self)
        dialog.setWindowTitle('Ajuda / Suporte')
        dialog.setFixedSize(360, 300)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        dialog.setStyleSheet("\n            QDialog {\n                background-color: #101826;\n            }\n            QLabel#helpTitle {\n                color: #ffffff;\n                font-size: 16px;\n                font-weight: 700;\n                font-family: 'Segoe UI';\n            }\n            QLabel#helpSub {\n                color: #9aa7b8;\n                font-size: 12px;\n                font-family: 'Segoe UI';\n            }\n            QPushButton#helpLinkBtn {\n                background-color: #162032;\n                color: #e8eaed;\n                border: 1px solid #243247;\n                border-radius: 8px;\n                padding: 12px 14px;\n                text-align: left;\n                font-size: 13px;\n                font-weight: 600;\n                font-family: 'Segoe UI';\n            }\n            QPushButton#helpLinkBtn:hover {\n                background-color: #1e2d45;\n                border: 1px solid #2196F3;\n                color: #ffffff;\n            }\n            QPushButton#helpLinkBtn:pressed {\n                background-color: #0D47A1;\n                border: 1px solid #0D47A1;\n            }\n            QPushButton#helpCloseBtn {\n                background-color: transparent;\n                color: #9aa7b8;\n                border: none;\n                padding: 6px;\n                font-size: 12px;\n                font-family: 'Segoe UI';\n            }\n            QPushButton#helpCloseBtn:hover {\n                color: #ffffff;\n            }\n        ")
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 18, 20, 14)
        layout.setSpacing(10)
        title = QLabel('Ajuda / Suporte')
        title.setObjectName('helpTitle')
        layout.addWidget(title)
        sub = QLabel('Escolha um canal para abrir no navegador')
        sub.setObjectName('helpSub')
        layout.addWidget(sub)
        layout.addSpacing(4)
        links = [('Aulas ÔÇö Canal 1', 'https://www.youtube.com/@RestorecellST'), ('Aulas ÔÇö Canal 2', 'https://www.youtube.com/@ramoncell'), ('Suporte e Contatos', 'https://linktr.ee/techunionsolutions')]
        def _abrir_url(url: str):
            try:
                webbrowser.open(url)
                return
            except Exception:
                QMessageBox.warning(dialog, 'Erro', f'N├úo foi poss├¡vel abrir o link.\n\nCopie e cole no navegador:\n{url}')
        for texto, url in links:
            btn = QPushButton(texto)
            btn.setObjectName('helpLinkBtn')
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect((lambda _=False, u=url: _abrir_url(u)))
            layout.addWidget(btn)
        layout.addStretch()
        btn_fechar = QPushButton('Fechar')
        btn_fechar.setObjectName('helpCloseBtn')
        btn_fechar.setCursor(Qt.PointingHandCursor)
        btn_fechar.clicked.connect(dialog.accept)
        layout.addWidget(btn_fechar, 0, Qt.AlignCenter)
        dialog.exec_()
    def abrir_peliculas(self):
        '''Abre a janela de pel├¡culas compat├¡veis ÔÇö padr├úo ParceirosWindow'''
        try:
            from app.views.peliculas.peliculas_window import PeliculasWindow
            self.peliculas_window = PeliculasWindow(self)
            self.peliculas_window.show()
            return
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, 'Erro', 'Erro ao abrir Pel├¡culas. Tente novamente.')
    def mostrar_bloqueio_premium(self, funcionalidade: str) -> bool:
        '''
Mostra di├ílogo de bloqueio para funcionalidades premium.
FUN├ç├âO GEN├ëRICA - Usada por: JUMPER DE TELAS, OS MANAGER, etc.
Args:
    funcionalidade: Nome da funcionalidade bloqueada (ex: "JUMPER DE TELAS", "OS MANAGER")
Returns:
    bool: True se usu├írio clicou em "Saiba Mais", False se clicou em "Voltar"
'''
        upgrade_msg = QMessageBox(self)
        upgrade_msg.setWindowTitle('Conte├║do Premium Bloqueado')
        upgrade_msg.setIcon(QMessageBox.Information)
        texto_html = f"\n        <h3 style='color: #e67e22;'>Conte├║do Premium: {funcionalidade}</h3>\n        <p>Esta funcionalidade ├® <b>exclusiva para usu├írios do Plano Premium</b>.</p>\n        \n        <p style='background-color: #f8f9fa; padding: 10px; border-radius: 5px;'>\n        Fa├ºa upgrade para o <b style='color: #f39c12;'>Plano Premium</b> \n        e tenha acesso completo a todas as ferramentas.\n        </p>\n        \n        <p>Entre em contato: <b>(85) 98963-4058</b></p>\n        "
        upgrade_msg.setText(texto_html)
        upgrade_msg.setTextFormat(Qt.RichText)
        upgrade_msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Help)
        upgrade_msg.button(QMessageBox.Ok).setText('Voltar')
        upgrade_msg.button(QMessageBox.Help).setText('Saiba Mais')
        result = upgrade_msg.exec_()
        if result == QMessageBox.Help:
            self.mostrar_info_upgrade()
            return True
        return False
    def mostrar_info_upgrade(self):
        '''Abre o di├ílogo detalhado de informa├º├Áes de upgrade'''
        upgrade_msg = QMessageBox(self)
        upgrade_msg.setWindowTitle('Plano Premium')
        upgrade_msg.setIcon(QMessageBox.Information)
        texto_html = "\n        <h3 style='color: #e67e22;'>Desbloqueie o Plano Premium</h3>\n        <p>Tenha acesso <b>completo</b> a todas as funcionalidades:</p>\n        \n        <ul style='background-color: #f8f9fa; padding: 15px; border-radius: 5px;'>\n          <li><b>Sistema de Ordens de Servi├ºo</b> profissional</li>\n          <li><b>Jumper de Telas</b> ÔÇö diagramas completos</li>\n          <li><b>Solu├º├Áes espec├¡ficas</b> por modelo</li>\n          <li><b>Procedimentos passo a passo</b></li>\n        </ul>\n        \n        <p style='background-color: #e8f5e8; padding: 10px; border-radius: 5px;'>\n        WhatsApp: <b>(85) 98963-4058</b><br>\n        Mencione seu email para facilitar o processo.\n        </p>\n        \n        <div style='background-color: #f1c40f; padding: 12px; border-radius: 8px; text-align: center;'>\n          <p style='color: #34495e; font-weight: bold; margin: 0;'>\n            COMPLETE SUA FERRAMENTA\n          </p>\n        </div>\n        "
        upgrade_msg.setText(texto_html)
        upgrade_msg.setTextFormat(Qt.RichText)
        upgrade_msg.setStandardButtons(QMessageBox.Ok)
        upgrade_msg.button(QMessageBox.Ok).setText('Entrar em Contato')
        upgrade_msg.exec_()
        self._abrir_whatsapp_contato('Plano Premium')
    def _abrir_whatsapp_contato(self, assunto: str, mensagem: str=None):
        '''Abre WhatsApp com mensagem pr├®-formatada - m├®todo centralizado para contato comercial/suporte.'''
        try:
            from urllib.parse import quote
            numero = '5585989634058'
            if not mensagem:
                email = getattr(self, 'user_email', 'n├úo informado')
                mensagem = f'Ol├í! Tenho interesse no {assunto} do TECH UNION SOLUTIONS.\n\nEmail: {email}\n\nAguardo informa├º├Áes. Obrigado!'
            whatsapp_url = f'https://wa.me/{numero}?text={quote(mensagem)}'
            webbrowser.open(whatsapp_url)
            QMessageBox.information(self, 'WhatsApp Aberto', 'O WhatsApp foi aberto no seu navegador.\n\nSe n├úo abriu automaticamente, entre em contato:\n+55 (85) 98963-4058\n\nNossa equipe responder├í o mais r├ípido poss├¡vel.')
            return
        except Exception:
            QMessageBox.information(self, 'Contato', f'Entre em contato conosco sobre: {assunto}\n\nWhatsApp: +55 (85) 98963-4058\nEmail: {getattr(self, 'user_email', 'n├úo informado')}')
    def iniciar_sincronizacao_blobs(self, solucoes_para_sincronizar=None):
        '''Inicia a sincroniza├º├úo de BLOBs em segundo plano'''
        if not hasattr(self, 'blob_queue'):
            self.blob_queue = []
        if not hasattr(self, 'blobs_sincronizados'):
            self.blobs_sincronizados = 0
        if not hasattr(self, 'max_blobs_por_ciclo'):
            self.max_blobs_por_ciclo = 50
        if solucoes_para_sincronizar:
            ids_na_fila = {sol['id'] for sol in self.blob_queue}
            for solucao in solucoes_para_sincronizar:
                if solucao['id'] not in ids_na_fila:
                    self.blob_queue.append(solucao)
                    print(f'[DEBUG] Adicionando solu├º├úo {solucao['id']} ({solucao['marca']} {solucao['modelo']}) ├á fila de BLOBs')
        if self.blob_queue:
            if hasattr(self, 'blob_sync_active') and self.blob_sync_active:
                return
        self.blobs_sincronizados = 0
        if not hasattr(self, 'blob_timer'):
            self.blob_timer = QTimer()
            self.blob_timer.timeout.connect(self.sincronizar_proximo_blob)
        print(f'[DEBUG] Iniciando sincroniza├º├úo de BLOBs em segundo plano - {len(self.blob_queue)} solu├º├Áes na fila')
        atualizacoes = [{'marca': 'Sincroniza├º├úo', 'modelo': f'­ƒöä Baixando diagramas e imagens: {len(self.blob_queue)} solu├º├Áes pendentes', 'data': datetime.now().strftime('%d/%m/%Y')}]
        self.atualizar_barra_atualizacoes(atualizacoes)
        self.blob_sync_active = True
        self.blob_timer.start(2000)
    def finalizar_sincronizacao_blobs(self):
        '''Finaliza a sincroniza├º├úo de BLOBs em segundo plano'''
        if hasattr(self, 'blob_timer') and self.blob_timer.isActive():
            self.blob_timer.stop()
        self.blob_sync_active = False
        print(f'[DEBUG] Sincroniza├º├úo de BLOBs conclu├¡da - {self.blobs_sincronizados} BLOBs sincronizados')
        if self.blobs_sincronizados > 0:
            atualizacoes = [{'marca': 'Sincroniza├º├úo', 'modelo': f'Ô£à Atualiza├º├úo conclu├¡da: {self.blobs_sincronizados} solu├º├Áes atualizadas', 'data': datetime.now().strftime('%d/%m/%Y')}]
            self.atualizar_barra_atualizacoes(atualizacoes)
            self.blob_queue = []
            self.blobs_sincronizados = 0
    def buscar_assistente_mysql(self):
        '''Busca o UNION ASSISTENTE diretamente no MySQL'''
        try:
            mysql_conn = pymysql.connect(**db_config(cursorclass=pymysql.cursors.DictCursor, ssl={'ca': None}, ssl_verify_cert=False))
            cursor = mysql_conn.cursor()
            cursor.execute("\n                SELECT id, titulo, link, descricao \n                FROM conteudos_dinamicos \n                WHERE titulo = 'UNION ASSISTENTE' \n                AND ativo = 1 \n                AND tipo = 'assistente'\n                LIMIT 1\n            ")
            assistente = cursor.fetchone()
            cursor.close()
            mysql_conn.close()
            return assistente
        except Exception as e:
            print(f'ÔØî Erro ao buscar assistente no MySQL: {e}')
    def registrar_click_assistente(self, id_assistente):
        '''Registra o click no assistente no MySQL'''
        try:
            mysql_conn = pymysql.connect(**db_config(cursorclass=pymysql.cursors.DictCursor, ssl={'ca': None}, ssl_verify_cert=False))
            cursor = mysql_conn.cursor()
            cursor.execute("\n                INSERT INTO conteudos_interacoes \n                (id_conteudo, id_usuario, tipo_interacao, data_interacao)\n                VALUES (%s, %s, 'click', NOW())\n            ", (id_assistente, self.user_id))
            mysql_conn.commit()
            cursor.close()
            mysql_conn.close()
            print(f'Ô£à Click registrado para assistente ID {id_assistente}')
            return
        except Exception as e:
            print(f'ÔÜá´©Å Erro ao registrar click: {e}')
    def abrir_union_assistente(self):
        '''Abre o UNION ASSISTENTE consultando diretamente o MySQL'''
        try:
            assistente = self.buscar_assistente_mysql()
            if assistente and assistente['link']:
                self.registrar_click_assistente(assistente['id'])
                self.abrir_link_navegador(assistente['link'])
                print(f'Ô£à Abrindo {assistente['titulo']}: {assistente['link']}')
                return
            if assistente and not assistente['link']:
                QMessageBox.information(self, 'Assistente Indispon├¡vel', f'O {assistente['titulo']} est├í temporariamente indispon├¡vel.\n\nTente novamente mais tarde ou entre em contato com:\nRESTORECELL SOLU├ç├òES TECNOL├ôGICA')
                return
            QMessageBox.warning(self, 'Assistente N├úo Encontrado', 'O UNION ASSISTENTE n├úo foi encontrado no sistema.\n\nEntre em contato com:\nRESTORECELL SOLU├ç├òES TECNOL├ôGICA')
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao acessar o assistente: {str(e)}')
    def abrir_server_gsm(self):
        '''Abre o SERVER GSM consultando diretamente o MySQL'''
        try:
            server = self.buscar_server_mysql()
            if server and server['link']:
                self.registrar_click_server(server['id'])
                self.abrir_link_navegador_server(server['link'], server.get('descricao', ''))
                print(f'Ô£à Abrindo {server['titulo']}: {server['link']}')
                return
            if server and not server['link']:
                QMessageBox.information(self, 'Server GSM Indispon├¡vel', f'O {server['titulo']} est├í temporariamente indispon├¡vel.\n\nTente novamente mais tarde ou entre em contato com:\nRESTORECELL SOLU├ç├òES TECNOL├ôGICA')
                return
            QMessageBox.information(self, 'Server GSM Temporariamente Indispon├¡vel', 'O SERVER GSM pode estar em manuten├º├úo ou passando por instabilidades moment├óneas.\n\nAguarde alguns minutos e tente novamente.\n\nSe o problema persistir, entre em contato com nosso suporte:\nWhatsApp: (85) 99750-7465\nRESTORECELL SOLU├ç├òES TECNOL├ôGICA')
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao acessar o Server GSM: {str(e)}')
    def buscar_server_mysql(self):
        '''Busca o SERVER GSM diretamente no MySQL'''
        try:
            mysql_conn = pymysql.connect(**db_config(cursorclass=pymysql.cursors.DictCursor, ssl={'ca': None}, ssl_verify_cert=False))
            cursor = mysql_conn.cursor()
            cursor.execute("\n                SELECT id, titulo, link, descricao \n                FROM conteudos_dinamicos \n                WHERE titulo = 'Server' \n                AND ativo = 1 \n                AND tipo = 'noticia'\n                LIMIT 1\n            ")
            server = cursor.fetchone()
            cursor.close()
            mysql_conn.close()
            return server
        except Exception as e:
            print(f'ÔØî Erro ao buscar Server GSM no MySQL: {e}')
    def registrar_click_server(self, id_server):
        '''Registra o click no Server GSM no MySQL'''
        try:
            mysql_conn = pymysql.connect(**db_config(cursorclass=pymysql.cursors.DictCursor, ssl={'ca': None}, ssl_verify_cert=False))
            cursor = mysql_conn.cursor()
            cursor.execute("\n                INSERT INTO conteudos_interacoes \n                (id_conteudo, id_usuario, tipo_interacao, data_interacao)\n                VALUES (%s, %s, 'click', NOW())\n            ", (id_server, self.user_id))
            mysql_conn.commit()
            cursor.close()
            mysql_conn.close()
            print(f'Ô£à Click registrado para Server GSM ID {id_server}')
            return
        except Exception as e:
            print(f'ÔÜá´©Å Erro ao registrar click no Server: {e}')
    def abrir_link_navegador_server(self, url, descricao=''):
        '''Abre URL do Server GSM (navegador interno se dispon├¡vel, externo como fallback)'''
        navegador_aberto = False
        if NAVEGADOR_INTERNO_DISPONIVEL and is_webengine_available():
            try:
                print(f'[SERVER-GSM] Abrindo no navegador interno: {url}')
                web_manager = get_web_view_manager()
                web_manager.abrir_url(url=url, title='SERVER GSM ÔÇö Tech Union Services', show_controls=True, show_url_bar=False, allow_external=True, parent=self)
                navegador_aberto = True
                print('[SERVER-GSM] Aberto no navegador interno')
                mensagem = 'O SERVER GSM foi aberto no navegador interno.\n\n'
                if descricao:
                    mensagem += f'Sobre:\n{descricao}\n\n'
                mensagem += 'Suporte: RESTORECELL SOLU├ç├òES TECNOL├ôGICA'
                QMessageBox.information(self, 'SERVER GSM', mensagem)
            except Exception as e_interno:
                print(f'[SERVER-GSM] Falha no navegador interno: {e_interno}')
                navegador_aberto = False
        if not navegador_aberto:
            try:
                webbrowser.open(url)
                print(f'[SERVER-GSM] Aberto no navegador externo: {url}')
                mensagem = 'O SERVER GSM foi aberto no seu navegador padr├úo.\n\n'
                if descricao:
                    mensagem += f'Sobre:\n{descricao}\n\n'
                mensagem += f'Link: {url}\n\n'
                mensagem += 'Suporte: RESTORECELL SOLU├ç├òES TECNOL├ôGICA'
                QMessageBox.information(self, 'SERVER GSM', mensagem)
            except Exception as e:
                QMessageBox.critical(self, 'Erro ao Abrir Link', f'N├úo foi poss├¡vel abrir automaticamente.\n\nCopie e cole este link no seu navegador:\n\n{url}\n\nSuporte: RESTORECELL SOLU├ç├òES TECNOL├ôGICA\nErro t├®cnico: {str(e)}')
    def abrir_link_navegador(self, url):
        '''Abre URL no navegador (externo para sites modernos, interno para simples)'''
        navegador_aberto = False
        SITES_NAVEGADOR_EXTERNO = ['chatgpt.com', 'openai.com', 'chat.openai.com', 'claude.ai', 'bard.google.com', 'gemini.google.com', 'copilot.microsoft', 'perplexity.ai']
        url_lower = url.lower()
        requer_externo = any((site in url_lower for site in SITES_NAVEGADOR_EXTERNO))
        if requer_externo:
            print(f'[ASSISTENTE] Site moderno detectado ÔÇö abrindo no navegador externo: {url}')
            try:
                webbrowser.open(url)
                print('[ASSISTENTE] Aberto no navegador externo com sucesso')
                QMessageBox.information(self, 'UNION ASSISTENTE', 'O UNION ASSISTENTE foi aberto no seu navegador padr├úo.\n\nEste servi├ºo usa tecnologia avan├ºada e funciona melhor\nno navegador do seu sistema (Chrome, Edge, Firefox).\n\nSuporte: RESTORECELL SOLU├ç├òES TECNOL├ôGICA')
            except Exception as e:
                QMessageBox.critical(self, 'Erro ao Abrir Link', f'N├úo foi poss├¡vel abrir automaticamente.\n\nCopie e cole este link no seu navegador:\n\n{url}\n\nSuporte: RESTORECELL SOLU├ç├òES TECNOL├ôGICA\nErro: {str(e)}')
            return
        if NAVEGADOR_INTERNO_DISPONIVEL and is_webengine_available():
            try:
                print(f'[ASSISTENTE] Abrindo no navegador interno: {url}')
                web_manager = get_web_view_manager()
                web_manager.abrir_url(url=url, title='UNION ASSISTENTE ÔÇö Tech Union Services', show_controls=True, show_url_bar=False, allow_external=True, parent=self)
                navegador_aberto = True
                print('[ASSISTENTE] Navegador interno aberto com sucesso')
                QMessageBox.information(self, 'UNION ASSISTENTE', 'O servi├ºo foi aberto no navegador interno.\n\nUtilize a ferramenta para suas consultas.\n\nSuporte: RESTORECELL SOLU├ç├òES TECNOL├ôGICA')
            except Exception as e_interno:
                print(f'[ASSISTENTE] Falha no navegador interno: {e_interno}')
                navegador_aberto = False
        if not navegador_aberto:
            try:
                webbrowser.open(url)
                print(f'[ASSISTENTE] Aberto no navegador externo: {url}')
                QMessageBox.information(self, 'UNION ASSISTENTE', f'O servi├ºo foi aberto no seu navegador padr├úo.\n\nSe n├úo abriu automaticamente, acesse:\n{url}\n\nSuporte: RESTORECELL SOLU├ç├òES TECNOL├ôGICA')
            except Exception as e:
                QMessageBox.critical(self, 'Erro ao Abrir Link', f'N├úo foi poss├¡vel abrir automaticamente.\n\nCopie e cole este link no seu navegador:\n\n{url}\n\nSuporte: RESTORECELL SOLU├ç├òES TECNOL├ôGICA\nErro: {str(e)}')
    def sincronizar_proximo_blob(self):
        '''Sincroniza o pr├│ximo BLOB da fila'''
        if not self.blob_queue:
            print('[DEBUG] Fila de BLOBs vazia, finalizando sincroniza├º├úo em segundo plano')
            self.finalizar_sincronizacao_blobs()
            return
        if self.blobs_sincronizados >= self.max_blobs_por_ciclo:
            print(f'[DEBUG] Limite de {self.max_blobs_por_ciclo} BLOBs atingido, pausando sincroniza├º├úo')
            atualizacoes = [{'marca': 'Sincroniza├º├úo', 'modelo': f'ÔÅ©´©Å Sincroniza├º├úo pausada: {self.blobs_sincronizados} solu├º├Áes atualizadas, {len(self.blob_queue)} pendentes', 'data': datetime.now().strftime('%d/%m/%Y')}]
            self.atualizar_barra_atualizacoes(atualizacoes)
            self.blob_timer.stop()
            self.blob_sync_active = False
            QTimer.singleShot(600000, self.iniciar_sincronizacao_blobs)
            return
        solucao = self.blob_queue[0]
        solucao_id = solucao['id']
        self.cursor.execute('SELECT COUNT(*) FROM solucoes WHERE id = ?', (solucao_id,))
        if self.cursor.fetchone()[0] == 0:
            print(f'[DEBUG] Solu├º├úo {solucao_id} n├úo existe mais, ignorando')
            self.blob_queue.pop(0)
            return
        self.cursor.execute('\n            SELECT \n                CASE WHEN diagrama_blob IS NULL OR LENGTH(diagrama_blob) < 100 THEN 0 ELSE 1 END as tem_diagrama_local,\n                CASE WHEN imagem_blob IS NULL OR LENGTH(imagem_blob) < 100 THEN 0 ELSE 1 END as tem_imagem_local,\n                CASE WHEN diagrama_blob_2 IS NULL OR LENGTH(diagrama_blob_2) < 100 THEN 0 ELSE 1 END as tem_diagrama_2_local,\n                CASE WHEN imagem_blob_2 IS NULL OR LENGTH(imagem_blob_2) < 100 THEN 0 ELSE 1 END as tem_imagem_2_local,\n                CASE WHEN diagrama_blob_3 IS NULL OR LENGTH(diagrama_blob_3) < 100 THEN 0 ELSE 1 END as tem_diagrama_3_local,\n                CASE WHEN imagem_blob_3 IS NULL OR LENGTH(imagem_blob_3) < 100 THEN 0 ELSE 1 END as tem_imagem_3_local,\n                hash_verificacao\n            FROM solucoes \n            WHERE id = ?\n        ', (solucao_id,))
        local_info = self.cursor.fetchone()
        if not local_info:
            print(f'[DEBUG] Informa├º├Áes locais n├úo encontradas para solu├º├úo {solucao_id}, ignorando')
            self.blob_queue.pop(0)
            return
        tem_diagrama_local = bool(local_info[0])
        tem_imagem_local = bool(local_info[1])
        tem_diagrama_2_local = bool(local_info[2])
        tem_imagem_2_local = bool(local_info[3])
        tem_diagrama_3_local = bool(local_info[4])
        tem_imagem_3_local = bool(local_info[5])
        hash_local = local_info[6]
        try:
            mysql_conn = self.conectar_mysql()
            if not mysql_conn:
                print('[DEBUG] Falha ao conectar ao MySQL para sincroniza├º├úo de BLOBs')
                atualizacoes = [{'marca': 'Sincroniza├º├úo', 'modelo': 'ÔØî Falha na conex├úo com o servidor durante a sincroniza├º├úo', 'data': datetime.now().strftime('%d/%m/%Y')}]
                self.atualizar_barra_atualizacoes(atualizacoes)
                self.blob_timer.stop()
                self.blob_sync_active = False
                return
            mysql_cursor = mysql_conn.cursor()
            mysql_cursor.execute('\n                SELECT \n                    CASE WHEN diagrama_blob IS NULL THEN 0\n                         WHEN LENGTH(diagrama_blob) < 100 THEN 0\n                         ELSE 1 \n                    END as tem_diagrama_remoto,\n                    CASE WHEN imagem_blob IS NULL THEN 0\n                         WHEN LENGTH(imagem_blob) < 100 THEN 0\n                         ELSE 1 \n                    END as tem_imagem_remoto,\n                    CASE WHEN diagrama_blob_2 IS NULL THEN 0\n                         WHEN LENGTH(diagrama_blob_2) < 100 THEN 0\n                         ELSE 1 \n                    END as tem_diagrama_2_remoto,\n                    CASE WHEN imagem_blob_2 IS NULL THEN 0\n                         WHEN LENGTH(imagem_blob_2) < 100 THEN 0\n                         ELSE 1 \n                    END as tem_imagem_2_remoto,\n                    CASE WHEN diagrama_blob_3 IS NULL THEN 0\n                         WHEN LENGTH(diagrama_blob_3) < 100 THEN 0\n                         ELSE 1 \n                    END as tem_diagrama_3_remoto,\n                    CASE WHEN imagem_blob_3 IS NULL THEN 0\n                         WHEN LENGTH(imagem_blob_3) < 100 THEN 0\n                         ELSE 1 \n                    END as tem_imagem_3_remoto,\n                    CASE WHEN diagrama_blob IS NOT NULL AND LENGTH(diagrama_blob) >= 100 THEN LENGTH(diagrama_blob) ELSE 0 END as tamanho_diagrama,\n                    CASE WHEN imagem_blob IS NOT NULL AND LENGTH(imagem_blob) >= 100 THEN LENGTH(imagem_blob) ELSE 0 END as tamanho_imagem,\n                    CASE WHEN diagrama_blob_2 IS NOT NULL AND LENGTH(diagrama_blob_2) >= 100 THEN LENGTH(diagrama_blob_2) ELSE 0 END as tamanho_diagrama_2,\n                    CASE WHEN imagem_blob_2 IS NOT NULL AND LENGTH(imagem_blob_2) >= 100 THEN LENGTH(imagem_blob_2) ELSE 0 END as tamanho_imagem_2,\n                    CASE WHEN diagrama_blob_3 IS NOT NULL AND LENGTH(diagrama_blob_3) >= 100 THEN LENGTH(diagrama_blob_3) ELSE 0 END as tamanho_diagrama_3,\n                    CASE WHEN imagem_blob_3 IS NOT NULL AND LENGTH(imagem_blob_3) >= 100 THEN LENGTH(imagem_blob_3) ELSE 0 END as tamanho_imagem_3,\n                    hash_verificacao\n                FROM solucoes \n                WHERE id = %s\n            ', (solucao_id,))
            blob_info = mysql_cursor.fetchone()
            if not blob_info:
                print(f'[DEBUG] Solu├º├úo {solucao_id} n├úo encontrada no MySQL, ignorando')
                self.blob_queue.pop(0)
                mysql_cursor.close()
                mysql_conn.close()
                return
            tem_diagrama_remoto = bool(blob_info['tem_diagrama_remoto'])
            tem_imagem_remoto = bool(blob_info['tem_imagem_remoto'])
            tem_diagrama_2_remoto = bool(blob_info['tem_diagrama_2_remoto'])
            tem_imagem_2_remoto = bool(blob_info['tem_imagem_2_remoto'])
            tem_diagrama_3_remoto = bool(blob_info['tem_diagrama_3_remoto'])
            tem_imagem_3_remoto = bool(blob_info['tem_imagem_3_remoto'])
            tamanho_diagrama = int(blob_info['tamanho_diagrama'])
            tamanho_imagem = int(blob_info['tamanho_imagem'])
            tamanho_diagrama_2 = int(blob_info['tamanho_diagrama_2'])
            tamanho_imagem_2 = int(blob_info['tamanho_imagem_2'])
            tamanho_diagrama_3 = int(blob_info['tamanho_diagrama_3'])
            tamanho_imagem_3 = int(blob_info['tamanho_imagem_3'])
            hash_remoto = blob_info['hash_verificacao']
            hash_diferente = hash_local != hash_remoto
            precisa_diagrama = tem_diagrama_remoto and not tem_diagrama_local
            precisa_imagem = tem_imagem_remoto and not tem_imagem_local
            precisa_diagrama_2 = tem_diagrama_2_remoto and not tem_diagrama_2_local
            precisa_imagem_2 = tem_imagem_2_remoto and not tem_imagem_2_local
            precisa_diagrama_3 = tem_diagrama_3_remoto and not tem_diagrama_3_local
            precisa_imagem_3 = tem_imagem_3_remoto and not tem_imagem_3_local
            if not precisa_diagrama and not precisa_imagem and not precisa_diagrama_2 and not precisa_imagem_2 and not precisa_diagrama_3 and not precisa_imagem_3 and not hash_diferente:
                print(f'[DEBUG] BLOBs j├í existem e est├úo atualizados para solu├º├úo {solucao_id}')
                self.blob_queue.pop(0)
                mysql_cursor.close()
                mysql_conn.close()
                return
            atualizacoes = [{'marca': 'Sincroniza├º├úo', 'modelo': f'­ƒöä Atualizando: {solucao['marca']} {solucao['modelo']} ({self.blobs_sincronizados + 1}/{self.blobs_sincronizados + len(self.blob_queue)})', 'data': datetime.now().strftime('%d/%m/%Y')}]
            self.atualizar_barra_atualizacoes(atualizacoes)
            self.blob_queue.pop(0)
            detalhes_log = []
            if precisa_diagrama:
                detalhes_log.append(f'diagrama ({tamanho_diagrama / 1024:.1f}KB)')
            if precisa_imagem:
                detalhes_log.append(f'imagem ({tamanho_imagem / 1024:.1f}KB)')
            if precisa_diagrama_2:
                detalhes_log.append(f'diagrama_2 ({tamanho_diagrama_2 / 1024:.1f}KB)')
            if precisa_imagem_2:
                detalhes_log.append(f'imagem_2 ({tamanho_imagem_2 / 1024:.1f}KB)')
            if precisa_diagrama_3:
                detalhes_log.append(f'diagrama_3 ({tamanho_diagrama_3 / 1024:.1f}KB)')
            if precisa_imagem_3:
                detalhes_log.append(f'imagem_3 ({tamanho_imagem_3 / 1024:.1f}KB)')
            if hash_diferente:
                detalhes_log.append('hash diferente')
            print(f'[DEBUG] Buscando BLOBs para solu├º├úo {solucao_id} - {solucao['marca']} {solucao['modelo']} - Necess├írio: {', '.join(detalhes_log)}')
            try:
                blob_query = '\n                    SELECT \n                        diagrama_blob, \n                        imagem_blob, \n                        diagrama_blob_2,\n                        imagem_blob_2,\n                        diagrama_blob_3,\n                        imagem_blob_3,\n                        hash_verificacao\n                    FROM solucoes \n                    WHERE id = %s\n                '
                mysql_cursor.execute(blob_query, (solucao_id,))
                blob_data = mysql_cursor.fetchone()
                if blob_data:
                    diagrama_blob = blob_data['diagrama_blob']
                    imagem_blob = blob_data['imagem_blob']
                    diagrama_blob_2 = blob_data['diagrama_blob_2']
                    imagem_blob_2 = blob_data['imagem_blob_2']
                    diagrama_blob_3 = blob_data['diagrama_blob_3']
                    imagem_blob_3 = blob_data['imagem_blob_3']
                    hash_verificacao = blob_data['hash_verificacao']
                    diagrama_size = len(diagrama_blob) if diagrama_blob else 0
                    imagem_size = len(imagem_blob) if imagem_blob else 0
                    diagrama_2_size = len(diagrama_blob_2) if diagrama_blob_2 else 0
                    imagem_2_size = len(imagem_blob_2) if imagem_blob_2 else 0
                    diagrama_3_size = len(diagrama_blob_3) if diagrama_blob_3 else 0
                    imagem_3_size = len(imagem_blob_3) if imagem_blob_3 else 0
                    print(f'[DEBUG] Tamanhos dos BLOBs: diagrama={diagrama_size / 1024:.1f}KB, imagem={imagem_size / 1024:.1f}KB, diagrama_2={diagrama_2_size / 1024:.1f}KB, imagem_2={imagem_2_size / 1024:.1f}KB, diagrama_3={diagrama_3_size / 1024:.1f}KB, imagem_3={imagem_3_size / 1024:.1f}KB')
                    self.cursor.execute('\n                        UPDATE solucoes \n                        SET diagrama_blob = ?, imagem_blob = ?,\n                            diagrama_blob_2 = ?, imagem_blob_2 = ?,\n                            diagrama_blob_3 = ?, imagem_blob_3 = ?,\n                            hash_verificacao = ?,\n                            data_sincronizacao = CURRENT_TIMESTAMP\n                        WHERE id = ?\n                    ', (encrypt_blob(diagrama_blob), encrypt_blob(imagem_blob), encrypt_blob(diagrama_blob_2), encrypt_blob(imagem_blob_2), encrypt_blob(diagrama_blob_3), encrypt_blob(imagem_blob_3), hash_verificacao, solucao_id))
                    self.conn.commit()
                    self.blobs_sincronizados += 1
                    print(f'[DEBUG] BLOBs sincronizados para solu├º├úo {solucao_id} ({self.blobs_sincronizados} total)')
            except Exception as e:
                print(f'[DEBUG] Erro ao sincronizar BLOBs da solu├º├úo {solucao_id}: {str(e)}')
        except Exception as e:
            print(f'[DEBUG] Erro geral na sincroniza├º├úo de BLOBs: {str(e)}')
        mysql_cursor.close()
        mysql_conn.close()
    def abrir_tira_virus(self):
        '''Abre o diagn├│stico android na aba Tira V├¡rus'''
        try:
            if not self._ci.check():
                return
            if hasattr(self, 'diagnostic_window') and self.diagnostic_window is not None:
                pass
            try:
                if self.diagnostic_window.isVisible():
                    self.diagnostic_window.setWindowState(self.diagnostic_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
                    self.diagnostic_window.showMaximized()
                    self.diagnostic_window.raise_()
                    self.diagnostic_window.activateWindow()
                    QTimer.singleShot(100, self.selecionar_aba_tira_virus)
                    self.statusBar().showMessage('Tira V├¡rus j├í est├í aberto ÔÇö trazendo para frente...', 2000)
                    print('Ô£à Janela Tira V├¡rus j├í aberta, trazendo para frente e selecionando aba')
            except RuntimeError:
                pass
            else:
                return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao abrir o Tira V├¡rus: {str(e)}\n\nVerifique se o sistema est├í funcionando corretamente.')
    def selecionar_aba_tira_virus(self):
        '''Seleciona a aba Tira Virus apos a janela carregar.'''
        try:
            if hasattr(self, 'diagnostic_window'):
                if hasattr(self.diagnostic_window, 'tab_widget'):
                    for i in range(self.diagnostic_window.tab_widget.count()):
                        tab_text = self.diagnostic_window.tab_widget.tabText(i).lower()
                        if 'tira' not in tab_text and 'virus' not in tab_text:
                            if not 'antivirus' in tab_text:
                                continue
                        self.diagnostic_window.tab_widget.setCurrentIndex(i)
                        return
                    return
                return
        except Exception:
            pass
    def abrir_tools_hxd(self):
        '''Abre o DiagnosticoAndroid na aba Tools (HXD Partition Editor).
Exclusivo para usuarios premium (.com.br) e admin.
Segue o mesmo padrao do abrir_tira_virus:
  - Gate premium via mostrar_bloqueio_premium().
  - Reutiliza janela diagnostic_window existente (sem duplicar).
  - Seleciona a aba Tools via QTimer apos carregamento.
Fallback defensivo: qualquer falha exibe mensagem generica sem vazar detalhes internos.
'''
        if not self._ci.check():
            return
        if not self.is_premium_user and not self.is_admin:
            self.mostrar_bloqueio_premium('Tools MDM Solutions')
            return
        try:
            if hasattr(self, 'diagnostic_window') and self.diagnostic_window is not None:
                pass
            try:
                if self.diagnostic_window.isVisible():
                    self.diagnostic_window.setWindowState(self.diagnostic_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
                    self.diagnostic_window.showMaximized()
                    self.diagnostic_window.raise_()
                    self.diagnostic_window.activateWindow()
                    QTimer.singleShot(100, self.selecionar_aba_tools)
                    self.statusBar().showMessage('Tools j├í est├í aberto ÔÇö trazendo para frente...', 2000)
            except RuntimeError:
                pass
            else:
                return
        except Exception:
            QMessageBox.critical(self, 'Erro ao abrir Tools MDM Solutions', 'Nao foi possivel abrir o modulo Tools MDM Solutions.\n\nTente novamente. Se o problema persistir, contate o suporte.')
    def selecionar_aba_tools(self):
        """Seleciona a aba Tools (HXD) dentro do DiagnosticoAndroid apos carregamento.
        Busca pela aba usando texto 'tools' (case-insensitive) para ser
        resiliente a variacoes de label. Fail-safe: silencia qualquer excecao.
        """
        try:
            if hasattr(self, 'diagnostic_window'):
                if hasattr(self.diagnostic_window, 'tab_widget'):
                    for i in range(self.diagnostic_window.tab_widget.count()):
                        tab_text = self.diagnostic_window.tab_widget.tabText(i)
                        if not 'tools' in tab_text.lower():
                            continue
                        self.diagnostic_window.tab_widget.setCurrentIndex(i)
                        self.statusBar().showMessage('Tools aberto com sucesso', 2000)
                        return
                    return
                return
        except Exception:
            pass
    def abrir_tools_exynos(self):
        '''Ref: administrativo/documentacao/2026-08-30_exy_modulo.md'''
        if not self.is_premium_user and not self.is_admin:
            self.mostrar_bloqueio_premium('Samsung Exynos FRP')
            return
        try:
            if hasattr(self, 'diagnostic_window') and self.diagnostic_window is not None:
                pass
            try:
                if self.diagnostic_window.isVisible():
                    self.diagnostic_window.setWindowState(self.diagnostic_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
                    self.diagnostic_window.showMaximized()
                    self.diagnostic_window.raise_()
                    self.diagnostic_window.activateWindow()
                    QTimer.singleShot(100, self.selecionar_aba_exynos)
                    self.statusBar().showMessage('Exynos j├í est├í aberto ÔÇö trazendo para frente...', 2000)
            except RuntimeError:
                pass
            else:
                return
        except Exception:
            QMessageBox.critical(self, 'Erro ao abrir Exynos', 'Nao foi possivel abrir o modulo Samsung Exynos FRP.\n\nTente novamente. Se o problema persistir, contate o suporte.')
    def selecionar_aba_exynos(self):
        '''Ref: administrativo/documentacao/2026-08-30_exy_modulo.md'''
        try:
            if hasattr(self, 'diagnostic_window'):
                if hasattr(self.diagnostic_window, 'tab_widget'):
                    for i in range(self.diagnostic_window.tab_widget.count()):
                        tab_text = self.diagnostic_window.tab_widget.tabText(i)
                        if not 'exynos' in tab_text.lower():
                            continue
                        self.diagnostic_window.tab_widget.setCurrentIndex(i)
                        self.statusBar().showMessage('Exynos aberto com sucesso', 2000)
                        return
                    return
                return
        except Exception:
            pass
    def verificar_popup_propaganda(self):
        '''Verifica se h├í popup de propaganda ativo no banco de dados'''
        try:
            if hasattr(self, 'popup_ja_exibido') and self.popup_ja_exibido:
                return
            popup_data = self.buscar_popup_mysql()
            if popup_data:
                self.popup_ja_exibido = True
                self.exibir_popup_propaganda(popup_data)
                self.registrar_visualizacao_popup(popup_data['id'])
                return
            print('­ƒôó Nenhum popup de propaganda ativo encontrado')
            return
        except Exception as e:
            print(f'ÔØî Erro ao verificar popup de propaganda: {e}')
    def buscar_popup_mysql(self):
        '''Busca popup de propaganda ativo no MySQL'''
        try:
            mysql_conn = pymysql.connect(**db_config(cursorclass=pymysql.cursors.DictCursor, ssl={'ca': None}, ssl_verify_cert=False))
            cursor = mysql_conn.cursor()
            cursor.execute("\n                SELECT id, titulo, descricao, link, arquivo_blob, ativo \n                FROM conteudos_dinamicos \n                WHERE LOWER(titulo) LIKE '%popup%' \n                AND ativo = 1\n                ORDER BY id DESC\n                LIMIT 1\n            ")
            popup = cursor.fetchone()
            cursor.close()
            mysql_conn.close()
            return popup
        except Exception as e:
            print(f'ÔØî Erro ao buscar popup no MySQL: {e}')
    def exibir_popup_propaganda(self, popup_data):
        '''Exibe o popup de propaganda na tela'''
        try:
            if hasattr(self, 'splash') and self.splash.isVisible():
                self.splash.finish(self)
            popup_dialog = PopupAnuncioDialog(popup_data, self)
            if not popup_dialog._imagem_carregada:
                print('ÔÜá´©Å Popup propaganda sem imagem v├ílida ÔÇö suprimido')
                popup_dialog.deleteLater()
                return
            popup_dialog.exec_()
            print(f"Ô£à Popup '{popup_data['titulo']}' exibido com sucesso")
            return
        except Exception as e:
            print(f'ÔØî Erro ao exibir popup propaganda: {e}')
    def registrar_visualizacao_popup(self, id_popup):
        '''Registra a visualiza├º├úo do popup no MySQL'''
        try:
            mysql_conn = pymysql.connect(**db_config(cursorclass=pymysql.cursors.DictCursor, ssl={'ca': None}, ssl_verify_cert=False))
            cursor = mysql_conn.cursor()
            cursor.execute("\n                INSERT INTO conteudos_interacoes \n                (id_conteudo, id_usuario, tipo_interacao, data_interacao)\n                VALUES (%s, %s, 'visualizacao', NOW())\n            ", (id_popup, self.user_id))
            mysql_conn.commit()
            cursor.close()
            mysql_conn.close()
            print(f'Ô£à Visualiza├º├úo registrada para popup ID {id_popup}')
            return
        except Exception as e:
            print(f'ÔÜá´©Å Erro ao registrar visualiza├º├úo: {e}')
    def registrar_click_popup(self, id_popup):
        '''Registra o click no popup no MySQL'''
        try:
            mysql_conn = pymysql.connect(**db_config(cursorclass=pymysql.cursors.DictCursor, ssl={'ca': None}, ssl_verify_cert=False))
            cursor = mysql_conn.cursor()
            cursor.execute("\n                INSERT INTO conteudos_interacoes \n                (id_conteudo, id_usuario, tipo_interacao, data_interacao)\n                VALUES (%s, %s, 'click', NOW())\n            ", (id_popup, self.user_id))
            mysql_conn.commit()
            cursor.close()
            mysql_conn.close()
            print(f'Ô£à Click registrado para popup ID {id_popup}')
            return
        except Exception as e:
            print(f'ÔÜá´©Å Erro ao registrar click: {e}')
    def ver_perfil(self):
        '''Abre janela para visualizar perfil do usu├írio (somente leitura)'''
        try:
            if not self.user_email:
                QMessageBox.warning(self, 'Aviso', 'Email do usu├írio n├úo dispon├¡vel.\n\nEsta funcionalidade est├í dispon├¡vel apenas para usu├írios logados com licen├ºa.')
                return
            from app.views.visualizar_perfil_window import VisualizarPerfilWindow
            self.visualizar_perfil_window = VisualizarPerfilWindow(self.user_email, self)
            self.visualizar_perfil_window.exec_()
            self.atualizar_header_saldo()
            return
        except ImportError:
            QMessageBox.warning(self, 'Erro', 'M├│dulo de visualiza├º├úo de perfil n├úo encontrado.\n\nEsta funcionalidade ser├í implementada em breve.')
        except Exception as e:
            QMessageBox.warning(self, 'Erro', f'Erro ao visualizar perfil: {str(e)}\n\nO sistema continua funcionando normalmente.')
    def abrir_perfil(self):
        '''Abre janela de perfil do usu├írio para edi├º├úo'''
        try:
            if not self.user_email:
                QMessageBox.warning(self, 'Aviso', 'Email do usu├írio n├úo dispon├¡vel.\n\nEsta funcionalidade est├í dispon├¡vel apenas para usu├írios logados com licen├ºa.')
                return
            from app.views.perfil_window import PerfilWindow
            self.perfil_window = PerfilWindow(self.user_email, self)
            self.perfil_window.exec_()
            return
        except ImportError:
            QMessageBox.warning(self, 'Erro', 'M├│dulo de perfil n├úo encontrado.\n\nEsta funcionalidade ser├í implementada em breve.')
        except Exception as e:
            QMessageBox.warning(self, 'Erro', f'Erro ao abrir perfil: {str(e)}\n\nO sistema continua funcionando normalmente.')
    def abrir_downloads(self):
        '''Abre a janela de downloads de arquivos com cache otimizado e sincroniza├º├úo for├ºada'''
        try:
            if not self._ci.check():
                return
            if hasattr(self, 'downloads_window') and self.downloads_window is not None:
                pass
            try:
                if self.downloads_window.isVisible():
                    self.downloads_window.setWindowState(self.downloads_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
                    self.downloads_window.showMaximized()
                    self.downloads_window.raise_()
                    self.downloads_window.activateWindow()
                    self.statusBar().showMessage('Janela Downloads j├í est├í aberta ÔÇö trazendo para frente...', 2000)
                    print('Ô£à Janela Downloads j├í aberta, trazendo para frente')
            except RuntimeError:
                pass
            else:
                return
        except Exception as e:
            print(f'Erro ao abrir Downloads: {str(e)}')
            QMessageBox.critical(self, 'Erro', 'Erro ao abrir Downloads. Tente novamente.')
    def verificar_inicializar_cache(self):
        '''Verifica se o cache existe e inicializa se necess├írio'''
        import os
        try:
            cache_path = 'app/database/servidor_arquivos_cache.db'
            if not os.path.exists(cache_path):
                print('­ƒöä Cache n├úo encontrado, inicializando automaticamente...')
                if hasattr(self, 'statusBar'):
                    self.statusBar().showMessage('Inicializando cache para melhor performance...', 3000)
                from implementar_cache_servidor_arquivos import ServidorArquivosCache
                cache_manager = ServidorArquivosCache()
                cache_manager.criar_estrutura_cache()
                print('Ô£à Estrutura do cache criada')
            try:
                cache_manager.sincronizar_completo()
                print('Ô£à Cache inicializado e sincronizado com sucesso')
                if hasattr(self, 'statusBar'):
                    self.statusBar().showMessage('Cache inicializado! Performance otimizada para downloads.', 2000)
            except Exception as sync_error:
                print(f'ÔÜá´©Å Erro na sincroniza├º├úo inicial: {sync_error}')
                if hasattr(self, 'statusBar'):
                    self.statusBar().showMessage('Cache inicializado (sincroniza├º├úo ser├í feita em segundo plano)', 2000)
            else:
                return
        except Exception as e:
            print(f'ÔÜá´©Å Erro ao verificar/inicializar cache: {e}')
    def atualizar_cache_segundo_plano(self):
        '''Atualiza o cache em segundo plano sem bloquear a interface'''
        try:
            print('­ƒöä Atualizando cache em segundo plano...')
            from implementar_cache_servidor_arquivos import ServidorArquivosCache
            cache_manager = ServidorArquivosCache()
            cache_manager.sincronizar_completo()
            print('Ô£à Cache atualizado em segundo plano')
            if hasattr(self, 'statusBar'):
                self.statusBar().showMessage('Cache atualizado! Downloads otimizados.', 2000)
                return
        except Exception as e:
            print(f'ÔÜá´©Å Erro na atualiza├º├úo do cache: {e}')
    def forcar_sincronizacao_cache_downloads(self):
        '''For├ºa a sincroniza├º├úo do cache de downloads para garantir marcas atualizadas'''
        try:
            print('­ƒöä For├ºando sincroniza├º├úo do cache de downloads...')
            if hasattr(self, 'statusBar'):
                self.statusBar().showMessage('Sincronizando marcas mais recentes...', 1000)
            from app.database.downloads_cache import DownloadsCache
            downloads_cache = DownloadsCache()
            try:
                with downloads_cache._conectar() as conn:
                    conn.execute('DELETE FROM cache_marcas')
                    print('Ô£à Cache de marcas for├ºadamente limpo')
            except Exception as cache_error:
                print(f'ÔÜá´©Å Erro ao limpar cache de marcas: {cache_error}')
            else:
                try:
                    try:
                        from implementar_cache_servidor_arquivos import ServidorArquivosCache
                        cache_manager = ServidorArquivosCache()
                        cache_manager.sincronizar_completo()
                        print('Ô£à Cache servidor de arquivos sincronizado')
                        if hasattr(self, 'statusBar'):
                            self.statusBar().showMessage('Marcas atualizadas! Cache sincronizado.', 2000)
                    except ImportError:
                        print('ÔÜá´©Å M├│dulo de cache servidor n├úo encontrado, continuando...')
                    except Exception as server_cache_error:
                        print(f'ÔÜá´©Å Erro na sincroniza├º├úo do servidor: {server_cache_error}')
                except Exception as e:
                    print(f'ÔÜá´©Å Erro na sincroniza├º├úo for├ºada: {e}')
                print('Ô£à Sincroniza├º├úo for├ºada conclu├¡da')
        except Exception as e:
            print(f'ÔÜá´©Å Erro na sincroniza├º├úo for├ºada: {e}')
    def mostrar_status_licenca(self):
        '''Mostra janela com informa├º├Áes detalhadas da licen├ºa'''
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle('­ƒöæ Status da Licen├ºa')
            dialog.setMinimumWidth(450)
            dialog.setMaximumWidth(500)
            dialog.setStyleSheet('\n                QDialog {\n                    background-color: white;\n                }\n                QLabel#titleLabel {\n                    font-size: 18px;\n                    font-weight: bold;\n                    color: #2c3e50;\n                    padding: 15px;\n                }\n                QFrame#infoFrame {\n                    background-color: #f8f9fa;\n                    border-radius: 8px;\n                    padding: 15px;\n                    margin: 10px;\n                }\n                QLabel#infoLabel {\n                    padding: 8px;\n                    font-size: 14px;\n                    color: #34495e;\n                }\n                QPushButton {\n                    background-color: #3498db;\n                    color: white;\n                    padding: 10px 20px;\n                    border-radius: 5px;\n                    border: none;\n                    font-weight: bold;\n                    font-size: 14px;\n                }\n                QPushButton:hover {\n                    background-color: #2980b9;\n                }\n                QPushButton#renewButton {\n                    background-color: #27ae60;\n                }\n                QPushButton#renewButton:hover {\n                    background-color: #229954;\n                }\n            ')
            layout = QVBoxLayout(dialog)
            title = QLabel('­ƒôè Informa├º├Áes da Sua Licen├ºa')
            title.setObjectName('titleLabel')
            title.setAlignment(Qt.AlignCenter)
            layout.addWidget(title)
            info_frame = QFrame()
            info_frame.setObjectName('infoFrame')
            info_layout = QVBoxLayout(info_frame)
            status_text = self.obter_status_licenca_formatado()
            status_label = QLabel(f'<b>Status:</b> {status_text}')
            status_label.setObjectName('infoLabel')
            info_layout.addWidget(status_label)
            dias_restantes = self.calcular_dias_restantes()
            if dias_restantes == 'Ôê×':
                dias_text = 'Licen├ºa Ativa'
            elif dias_restantes == 'EXPIRADA':
                dias_text = "ÔÜá´©Å <b style='color: #e74c3c;'>Licen├ºa Expirada</b>"
            elif dias_restantes == 'HOJE':
                dias_text = "ÔÜá´©Å <b style='color: #f39c12;'>Expira Hoje!</b>"
            elif dias_restantes.isdigit():
                days = int(dias_restantes)
                if days <= 7:
                    dias_text = f"ÔÅ░ <b style='color: #f39c12;'>{days} dias restantes</b>"
                else:
                    dias_text = f'­ƒôà {days} dias restantes'
            else:
                dias_text = 'Status indispon├¡vel'
            dias_label = QLabel(f'<b>Tempo Restante:</b> {dias_text}')
            dias_label.setObjectName('infoLabel')
            info_layout.addWidget(dias_label)
            data_expiracao = self.obter_data_expiracao_formatada()
            data_label = QLabel(f'<b>Data de Expira├º├úo:</b> {data_expiracao}')
            data_label.setObjectName('infoLabel')
            info_layout.addWidget(data_label)
            if self.license_data:
                if self.license_data.get('name'):
                    nome_label = QLabel(f'<b>Nome da Licen├ºa:</b> {self.license_data['name']}')
                    nome_label.setObjectName('infoLabel')
                    info_layout.addWidget(nome_label)
                if self.license_data.get('uses') is not None and self.license_data.get('maxUses'):
                    usos_label = QLabel(f'<b>Usos:</b> {self.license_data['uses']} / {self.license_data['maxUses']}')
                    usos_label.setObjectName('infoLabel')
                    info_layout.addWidget(usos_label)
            layout.addWidget(info_frame)
            buttons_layout = QHBoxLayout()
            btn_renovar = QPushButton('­ƒöä Renovar Licen├ºa')
            btn_renovar.setObjectName('renewButton')
            btn_renovar.clicked.connect((lambda: [dialog.accept(), self.abrir_renovacao_licenca()]))
            buttons_layout.addWidget(btn_renovar)
            btn_fechar = QPushButton('Ô£û´©Å Fechar')
            btn_fechar.clicked.connect(dialog.close)
            buttons_layout.addWidget(btn_fechar)
            layout.addLayout(buttons_layout)
            dialog.exec_()
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', 'Erro ao exibir status da licen├ºa. Tente novamente.')
    def abrir_renovacao_licenca(self):
        '''Abre WhatsApp para renova├º├úo da licen├ºa - usa m├®todo centralizado'''
        dias_restantes = self.calcular_dias_restantes()
        data_expiracao = self.obter_data_expiracao_formatada()
        if dias_restantes == 'Ôê×':
            status_msg = 'Licen├ºa Ativa'
        elif dias_restantes == 'EXPIRADA':
            status_msg = 'Licen├ºa Expirada'
        elif str(dias_restantes).isdigit():
            _sufixo = 'dia restante' if dias_restantes == '1' else 'dias restantes'
            status_msg = f'{dias_restantes} {_sufixo}'
        else:
            status_msg = 'Status indispon├¡vel'
        mensagem = f'Ol├í! Gostaria de renovar minha licen├ºa do TECH UNION SOLUTIONS.\n\nEmail: {self.user_email}\nStatus atual: {status_msg}\nExpira├º├úo: {data_expiracao}\n\nPor favor, me informe sobre as op├º├Áes de renova├º├úo dispon├¡veis.\n\nObrigado!'
        self._abrir_whatsapp_contato('Renova├º├úo de Licen├ºa', mensagem=mensagem)
    def mostrar_dashboard_inicial(self):
        '''Volta ao topo do dashboard onde estao os cards de marcas/categorias.
        Usado pelo Sidebar quando o usuario clica em "Dashboard" ou "Solucoes".
        Como os cards ja estao montados pelo `setup_ui`, esse metodo apenas
        rola a area scrollavel para o topo e da feedback no statusBar.
        '''
        try:
            scroll = None
            if hasattr(self, 'grid_layout') and self.grid_layout is not None:
                inner = self.grid_layout.parentWidget()
                if inner is not None:
                    scroll = inner.parentWidget()
            if scroll is not None and hasattr(scroll, 'verticalScrollBar'):
                scroll.verticalScrollBar().setValue(0)
            self.statusBar().showMessage('­ƒÅá Dashboard inicial', 1500)
            return
        except Exception as e:
            print(f'[mostrar_dashboard_inicial] erro: {type(e).__name__}: {e}')
    _CARDS_MIN_W = 240
    _CARDS_SPACING = 20
    _CARDS_MAX_COLS = 4
    _CARDS_MIN_COLS = 1
    def _aplicar_grid_legado_4_colunas(self) -> None:
        '''Posiciona os cards no grid em 4 colunas fixas (comportamento V1).
        Usado como fallback quando `UI_DASHBOARD_RESPONSIVE_GRID=0` ou em
        qualquer falha do calculo responsivo.
        '''
        if not getattr(self, '_cards_widgets_ordem', None):
            return
        if not hasattr(self, 'grid_layout') or self.grid_layout is None:
            return
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item is not None and item.widget() is not None:
                item.widget().setParent(self.grid_layout.parentWidget())
        row = col = 0
        for card in self._cards_widgets_ordem:
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1
        self._cards_cols_atual = 4
    def _calcular_colunas_responsivas(self) -> int:
        '''Calcula o numero ideal de colunas para os cards.
        Formula: cols = max(MIN, min(MAX, (avail - spacing) / (min_w + spacing)))
        Retorna sempre dentro de [_CARDS_MIN_COLS, _CARDS_MAX_COLS].
        '''
        try:
            scroll = getattr(self, '_cards_scroll_area', None)
            if scroll is None:
                return 4
            avail = scroll.viewport().width()
            if avail <= 0:
                avail = self.width()
                sidebar = getattr(self, '_sidebar', None)
                if sidebar is not None:
                    avail -= sidebar.width()
                avail -= 40
            min_w = self._CARDS_MIN_W
            sp = self._CARDS_SPACING
            cols = (avail - sp) // (min_w + sp)
            cols = max(self._CARDS_MIN_COLS, min(self._CARDS_MAX_COLS, int(cols)))
            return cols
        except Exception:
            return 4
    def _reorganizar_cards_grid_responsivo(self, force: bool=False) -> None:
        '''Reposiciona os cards conforme a largura atual.
        - Calcula `cols` ideal baseado na largura do viewport.
        - Se nao mudou desde a ultima chamada, retorna sem trabalho (eficiente).
        - Caso contrario, retira os widgets do grid e re-adiciona.
        '''
        if not getattr(self, '_cards_widgets_ordem', None):
            return
        if not hasattr(self, 'grid_layout') or self.grid_layout is None:
            return
        cols = self._calcular_colunas_responsivas()
        if not force:
            if cols == getattr(self, '_cards_cols_atual', 0):
                return
        parent = self.grid_layout.parentWidget()
        try:
            if parent is not None:
                parent.setUpdatesEnabled(False)
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                if item is not None and item.widget() is not None:
                    item.widget().setParent(parent)
            row = col = 0
            for card in self._cards_widgets_ordem:
                self.grid_layout.addWidget(card, row, col)
                col += 1
                if col >= cols:
                    col = 0
                    row += 1
            self._cards_cols_atual = cols
        finally:
            if parent is not None:
                parent.setUpdatesEnabled(True)
                parent.update()
    def _agendar_reorganizacao_cards(self) -> None:
        '''Agenda o recalculo do grid com throttle de 80ms.
        Evita recalcular a cada pixel durante o drag de redimensionamento.
        Usa um QTimer single-shot que se reinicia a cada chamada.
        '''
        if os.environ.get('UI_DASHBOARD_RESPONSIVE_GRID', '1') != '1':
            return
        try:
            from PyQt5.QtCore import QTimer
            timer = getattr(self, '_cards_resize_timer', None)
            if timer is None:
                timer = QTimer(self)
                timer.setSingleShot(True)
                timer.timeout.connect(self._reorganizar_cards_grid_responsivo)
                self._cards_resize_timer = timer
            timer.start(80)
            return
        except Exception:
            try:
                self._reorganizar_cards_grid_responsivo()
                return
            except Exception:
                pass
    def resizeEvent(self, event):
        '''Hook de resize para atualizar a largura responsiva do sidebar
        e reorganizar os cards do dashboard com throttle.'''
        try:
            super().resizeEvent(event)
        except Exception:
            pass
        try:
            sidebar = getattr(self, '_sidebar', None)
            if sidebar is not None and hasattr(sidebar, 'update_responsive_width'):
                sidebar.update_responsive_width(self.width())
        except Exception:
            pass
        try:
            self._agendar_reorganizacao_cards()
        except Exception:
            return
    def _abrir_diagnostico_e_focar_aba(self, criterios_aba, descricao_humana='aba'):
        '''Helper interno: abre/foca a janela de diagnostico e seleciona uma aba.
Args:
    criterios_aba: lista de palavras-chave em lowercase. A aba escolhida
        eh a primeira cujo texto (lowercase) contem TODAS as palavras.
    descricao_humana: usado em mensagens de erro para o usuario final.
'''
        try:
            if not self._ci.check():
                return
            if hasattr(self, 'diagnostic_window') and self.diagnostic_window is not None:
                pass
            try:
                if self.diagnostic_window.isVisible():
                    self.diagnostic_window.setWindowState(self.diagnostic_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
                    self.diagnostic_window.showMaximized()
                    self.diagnostic_window.raise_()
                    self.diagnostic_window.activateWindow()
                    QTimer.singleShot(120, (lambda: self._selecionar_aba_diagnostico(criterios_aba)))
            except RuntimeError:
                pass
            else:
                return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao abrir {descricao_humana}: {str(e)}')
    def _selecionar_aba_diagnostico(self, criterios):
        '''Seleciona em diagnostic_window.tab_widget a primeira aba que casa com TODOS os criterios.'''
        try:
            if not hasattr(self, 'diagnostic_window') or self.diagnostic_window is None:
                return
            if not hasattr(self.diagnostic_window, 'tab_widget'):
                return
        except Exception as e:
            print(f'[_selecionar_aba_diagnostico] erro: {type(e).__name__}: {e}')
        try:
            crit_low = [c.lower() for c in criterios]
            tw = self.diagnostic_window.tab_widget
            for i in range(tw.count()):
                tab_text = tw.tabText(i).lower()
                if not all((c in tab_text for c in crit_low)):
                    continue
                tw.setCurrentIndex(i)
                return
            print(f'[_selecionar_aba_diagnostico] nenhuma aba casou com {criterios}')
            return
        except Exception as e:
            print(f'[_selecionar_aba_diagnostico] erro: {type(e).__name__}: {e}')
    def abrir_diagnostico_aba_motorola(self):
        '''Abre o diagnostico ja focado na aba Motorola (FRP MODELS Motorola).'''
        self._abrir_diagnostico_e_focar_aba(['motorola'], 'Diagnostico Motorola')
    def abrir_diagnostico_aba_xiaomi(self):
        '''Abre o diagnostico ja focado na aba Xiaomi (FRP MODELS Xiaomi).'''
        self._abrir_diagnostico_e_focar_aba(['xiaomi'], 'Diagnostico Xiaomi')
    def abrir_diagnostico_aba_samsung(self):
        '''Abre o diagnostico ja focado na aba Samsung (FRP MODELS Samsung).'''
        self._abrir_diagnostico_e_focar_aba(['samsung'], 'Diagnostico Samsung')
    def abrir_diagnostico_aba_edl(self):
        '''Abre o diagnostico ja focado na aba QCOM EDL.'''
        self._abrir_diagnostico_e_focar_aba(['qcom', 'edl'], 'QCOM EDL')
    def abrir_diagnostico_aba_spd(self):
        '''Abre o diagnostico ja focado na aba SPD (Unisoc/Spreadtrum).'''
        self._abrir_diagnostico_e_focar_aba(['spd'], 'SPD')
    def abrir_diagnostico_aba_apps(self):
        '''Abre o diagnostico ja focado na aba Apps.'''
        self._abrir_diagnostico_e_focar_aba(['apps'], 'Apps')
    def abrir_diagnostico_aba_monitor(self):
        '''Abre o diagnostico ja focado na aba Monitor.'''
        self._abrir_diagnostico_e_focar_aba(['monitor'], 'Monitor')
    def _focar_subaba_flash_da_marca(self, criterios_marca):
        """Focar aba interna 'Flash' do widget de marca atualmente exibido."""
        try:
            if not hasattr(self, 'diagnostic_window') or self.diagnostic_window is None:
                return
            if not hasattr(self.diagnostic_window, 'tab_widget'):
                return
            tw = self.diagnostic_window.tab_widget
        except Exception as e:
            print(f'[_focar_subaba_flash_da_marca] {type(e).__name__}: {e}')
        try:
            crit_low = [c.lower() for c in criterios_marca]
            for i in range(tw.count()):
                if all((c in tw.tabText(i).lower() for c in crit_low)):
                    marca_widget = tw.widget(i)
                    inner = getattr(marca_widget, 'tab_widget', None)
                    if inner is None:
                        return
                    for j in range(inner.count()):
                        if not 'flash' in inner.tabText(j).lower():
                            continue
                        inner.setCurrentIndex(j)
                        return
                    return
            return
        except Exception as e:
            print(f'[_focar_subaba_flash_da_marca] {type(e).__name__}: {e}')
    def abrir_flash_motorola(self):
        """Abre o diagnostico, foca aba Motorola e depois sub-aba '­ƒôÑ Flash'."""
        self._abrir_diagnostico_e_focar_aba(['motorola'], 'Flash Motorola')
        QTimer.singleShot(500, (lambda: self._focar_subaba_flash_da_marca(['motorola'])))
    def abrir_flash_xiaomi(self):
        """Abre o diagnostico, foca aba Xiaomi e depois sub-aba '­ƒôÑ Flash'."""
        self._abrir_diagnostico_e_focar_aba(['xiaomi'], 'Flash Xiaomi')
        QTimer.singleShot(500, (lambda: self._focar_subaba_flash_da_marca(['xiaomi'])))
    def abrir_flash_samsung(self):
        """Abre o diagnostico, foca aba Samsung e depois sub-aba '­ƒôÑ Flash'."""
        self._abrir_diagnostico_e_focar_aba(['samsung'], 'Flash Samsung')
        QTimer.singleShot(500, (lambda: self._focar_subaba_flash_da_marca(['samsung'])))
    def _construir_banner_boas_vindas(self):
        '''Cria o banner unificado exibido no header quando a top-bar legada esta off.
Estrutura (2 colunas horizontais com altura uniforme):
    [icone responsivo]  [bloco textual com kicker / titulo / slogan / sub / badges]
Tudo eh adaptado a 5 buckets de resolucao para evitar quebra de texto:
    xs (<=1280), sm (<=1366), md (<=1600), lg (<=1920), xl (>1920).
Substitui o title_area legado para nao termos titulo duplicado.
'''
        from PyQt5.QtWidgets import QSizePolicy
        try:
            screen_w = QApplication.primaryScreen().geometry().width()
        except Exception:
            screen_w = 1366
        def _t(chave: str, default: str) -> str:
            try:
                tm = getattr(self, 'translation_manager', None)
                if tm is None:
                    return default
                valor = tm.get_text(chave)
                if isinstance(valor, str) and valor and valor != chave:
                    return valor
            except Exception:
                pass
            return default
        if screen_w <= 1280:
            bucket = 'xs'
            f_kicker, f_title, f_slogan, f_sub, f_badge = 10, 18, 10, 10, 9
            icon_size = 0
            badge_pad = '2px 7px'
            badge_radius = 9
            badge_short = True
            sub_text = _t('welcome_sub_xs', 'Solu├º├Áes para t├®cnicos\nde smartphone.')
            sub_lines = 2
        elif screen_w <= 1366:
            bucket = 'sm'
            f_kicker, f_title, f_slogan, f_sub, f_badge = 10, 20, 10, 10, 9
            icon_size = 0
            badge_pad = '2px 8px'
            badge_radius = 9
            badge_short = True
            sub_text = _t('welcome_sub_sm', 'Solu├º├Áes profissionais\npara t├®cnicos.')
            sub_lines = 2
        elif screen_w <= 1600:
            bucket = 'md'
            f_kicker, f_title, f_slogan, f_sub, f_badge = 11, 22, 11, 11, 10
            icon_size = 96
            badge_pad = '3px 10px'
            badge_radius = 10
            badge_short = False
            sub_text = _t('welcome_sub_md', 'Plataforma N┬░1 para t├®cnicos\nde smartphones.')
            sub_lines = 2
        elif screen_w <= 1920:
            bucket = 'lg'
            f_kicker, f_title, f_slogan, f_sub, f_badge = 12, 24, 12, 12, 11
            icon_size = 110
            badge_pad = '4px 10px'
            badge_radius = 11
            badge_short = False
            sub_text = _t('welcome_sub_lg', 'A plataforma N┬░1 em solu├º├Áes para\nt├®cnicos de smartphones.')
            sub_lines = 2
        else:
            bucket = 'xl'
            f_kicker, f_title, f_slogan, f_sub, f_badge = 13, 26, 13, 12, 11
            icon_size = 120
            badge_pad = '5px 12px'
            badge_radius = 12
            badge_short = False
            sub_text = _t('welcome_sub_lg', 'A plataforma N┬░1 em solu├º├Áes para\nt├®cnicos de smartphones.')
            sub_lines = 2
        banner = QFrame()
        banner.setObjectName('welcomeBannerInline')
        banner.setStyleSheet(f'\n            QFrame#welcomeBannerInline {{ background: transparent; }}\n            QLabel#welcomeKicker {{ color: rgba(255,255,255,0.85); font-size: {f_kicker}px;\n                                    font-weight: 500; letter-spacing: 0.3px; }}\n            QLabel#welcomeTitle  {{ color: #ffffff; font-size: {f_title}px; font-weight: 800;\n                                    letter-spacing: 0.4px; }}\n            QLabel#welcomeAccent {{ color: #82B1FF; font-size: {f_title}px; font-weight: 800;\n                                    letter-spacing: 0.4px; }}\n            QLabel#welcomeSlogan {{ color: rgba(255,255,255,0.95); font-size: {f_slogan}px;\n                                    font-style: italic; font-weight: 500; }}\n            QLabel#welcomeSub    {{ color: rgba(255,255,255,0.78); font-size: {f_sub}px;\n                                    font-weight: 400; }}\n            QLabel#welcomeBadge  {{ color: #ffffff; font-size: {f_badge}px; font-weight: 600;\n                                    padding: {badge_pad}; border-radius: {badge_radius}px;\n                                    background-color: rgba(255,255,255,0.14);\n                                    border: 1px solid rgba(255,255,255,0.22); }}\n            QLabel#welcomeIcon   {{ background: transparent; }}\n        ')
        h = QHBoxLayout(banner)
        h.setContentsMargins(4, 0, 4, 0)
        h.setSpacing(12 if bucket in ('xs', 'sm') else 16)
        if icon_size > 0:
            try:
                from PyQt5.QtSvg import QSvgRenderer
                from PyQt5.QtGui import QPixmap, QPainter
                import os as _os
                svg_path = PathManager.get_resource_path('icons_svg/sidebar.svg')
                if svg_path and _os.path.exists(svg_path):
                    icon_label = QLabel(banner)
                    icon_label.setObjectName('welcomeIcon')
                    renderer = QSvgRenderer(svg_path)
                    pix = QPixmap(icon_size, icon_size)
                    pix.fill(Qt.transparent)
                    p = QPainter(pix)
                    p.setRenderHint(QPainter.Antialiasing, True)
                    p.setRenderHint(QPainter.SmoothPixmapTransform, True)
                    renderer.render(p)
                    p.end()
                try:
                    from PyQt5.QtGui import QColor
                    tinted = QPixmap(pix.size())
                    tinted.fill(Qt.transparent)
                    p2 = QPainter(tinted)
                    p2.setRenderHint(QPainter.Antialiasing, True)
                    p2.setRenderHint(QPainter.SmoothPixmapTransform, True)
                    p2.setCompositionMode(QPainter.CompositionMode_Source)
                    p2.drawPixmap(0, 0, pix)
                    p2.setCompositionMode(QPainter.CompositionMode_SourceIn)
                    p2.fillRect(tinted.rect(), QColor('#ffffff'))
                    p2.end()
                    pix = tinted
                except Exception:
                    pass
                else:
                    icon_label.setPixmap(pix)
                    icon_label.setFixedSize(icon_size, icon_size)
                    icon_label.setAlignment(Qt.AlignCenter)
                    h.addWidget(icon_label, 0, Qt.AlignVCenter)
            except Exception as _e_icon:
                print(f'[banner_icon] indisponivel: {type(_e_icon).__name__}: {_e_icon}')
        v = QVBoxLayout()
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(2)
        v.setAlignment(Qt.AlignTop)
        kicker = QLabel(_t('welcome_kicker', 'Bem-vindo ao'), banner)
        kicker.setObjectName('welcomeKicker')
        kicker.setWordWrap(False)
        v.addWidget(kicker, 0, Qt.AlignLeft)
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)
        t1 = QLabel('TECH UNION', banner)
        t1.setObjectName('welcomeTitle')
        t1.setWordWrap(False)
        t1.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        t2 = QLabel('SOLUTIONS', banner)
        t2.setObjectName('welcomeAccent')
        t2.setWordWrap(False)
        t2.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        title_row.addWidget(t1, 0, Qt.AlignVCenter)
        title_row.addWidget(t2, 0, Qt.AlignVCenter)
        title_row.addStretch(1)
        v.addLayout(title_row)
        try:
            slogan_text = self.translation_manager.get_text('slogan')
        except Exception:
            slogan_text = 'Feito de t├®cnico para t├®cnicos!'
        slogan_lbl = QLabel(slogan_text, banner)
        slogan_lbl.setObjectName('welcomeSlogan')
        slogan_lbl.setWordWrap(False)
        v.addWidget(slogan_lbl, 0, Qt.AlignLeft)
        sub = QLabel(sub_text, banner)
        sub.setObjectName('welcomeSub')
        sub.setWordWrap(True)
        sub.setMinimumWidth(0)
        sub.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        try:
            from PyQt5.QtGui import QFont
            _sub_font = QFont(sub.font())
            _sub_font.setPointSize(-1)
            _sub_font.setPixelSize(int(f_sub))
            sub.setFont(_sub_font)
            _line_h = sub.fontMetrics().height()
            sub.setMinimumHeight(_line_h * sub_lines + 6)
        except Exception:
            sub.setMinimumHeight(int(f_sub * 1.45) * sub_lines + 6)
        v.addWidget(sub, 0, Qt.AlignLeft)
        versao_app = '1.3.4'
        if badge_short:
            badges_textos = _t('welcome_badge_online_short', '­ƒƒó Online'), _t('welcome_badge_secure_short', '­ƒøí Seguro'), _t('welcome_badge_version_short', 'ÔÜÖ v{versao}').format(versao=versao_app)
        else:
            badges_textos = _t('welcome_badge_online', '­ƒƒó  Online'), _t('welcome_badge_secure', '­ƒøí  Seguro'), _t('welcome_badge_version', 'ÔÜÖ  Vers├úo {versao}').format(versao=versao_app)
        badges_row = QHBoxLayout()
        badges_row.setContentsMargins(0, 14, 0, 0)
        badges_row.setSpacing(6 if badge_short else 8)
        for txt in badges_textos:
            b = QLabel(txt, banner)
            b.setObjectName('welcomeBadge')
            b.setWordWrap(False)
            b.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
            badges_row.addWidget(b, 0)
        badges_row.addStretch(1)
        v.addLayout(badges_row)
        text_box = QWidget(banner)
        text_box.setLayout(v)
        text_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        text_box.setMinimumWidth(0)
        h.addWidget(text_box, 1, Qt.AlignVCenter)
        if bucket == 'xs':
            banner.setMinimumHeight(155)
            return banner
        if bucket == 'sm':
            banner.setMinimumHeight(180)
            return banner
        if bucket == 'md':
            banner.setMinimumHeight(190)
            return banner
        banner.setMinimumHeight(200)
        return banner
# WARNING: Decompyle incomplete
