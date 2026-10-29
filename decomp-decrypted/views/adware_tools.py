import os
import re
import json
import logging
import traceback
from PyQt5.QtCore import (Qt, QTimer, pyqtSignal, QElapsedTimer, QDateTime, QThread)
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame, QMessageBox, QScrollArea, QDialog, QListWidget, QListWidgetItem, QCheckBox, QApplication, QTextEdit, QSpinBox, QSizePolicy, QTabWidget, QInputDialog, QLineEdit)
from PyQt5.QtGui import (QIcon, QFont, QColor)
from app.utils.adb_manager import ADBManager
from app.utils.path_manager import PathManager
from app.utils._pkg_defs import obter_pacotes_protegidos, is_pacote_protegido
from app.utils.adware_advanced_detector import AdvancedAdwareDetector
from app.utils.adware_csi import AdwareCSI
try:
    from app.views.ui.usb_device_widget import UsbDeviceWidget
except Exception:
    UsbDeviceWidget = None
try:
    from app.utils.usb_requirements_manager import abrir_gerenciador_dispositivos
except Exception:
    abrir_gerenciador_dispositivos = None
logger = logging.getLogger(__name__)
def load_json_blacklist():
    try:
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(app_dir, 'database', 'blacklist_union_apps_v2.json')
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                json_list = json_data.get('blacklist_packages', [])
                logger.info(f'Lista adicional de apps maliciosos carregada do JSON. Total: {len(json_list)} apps')
                return json_list
        logger.warning('Arquivo JSON de blacklist n├úo encontrado.')
    except Exception as e:
        logger.error(f'Erro ao carregar lista do JSON: {str(e)}')
        logger.error(traceback.format_exc())
    return []
class CommandThread(QTimer):
    command_finished = pyqtSignal(str)
    command_started = pyqtSignal()
    command_error = pyqtSignal(str)
    progress_update = pyqtSignal(str)
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.running = True
        self.setSingleShot(True)
        self.timeout.connect(self._execute)
        self.start(0)
    def _execute(self):
        self.command_started.emit()
        try:
            result = self.function(*self.args, **self.kwargs)
            if self.running:
                self.command_finished.emit(result if isinstance(result, str) else str(result))
                return
        except Exception as e:
            if self.running:
                logger.error(f'Erro na execu├º├úo do comando: {str(e)}')
                logger.error(traceback.format_exc())
                self.command_error.emit(str(e))
    def stop(self):
        self.running = False
class _AsyncAdbAction(QThread):
    finished_with_result = pyqtSignal(bool, str)
    def __init__(self, target_callable, parent=None):
        super().__init__(parent)
        self._target = target_callable
    def run(self):
        ok = False
        msg = ''
        try:
            r = self._target()
            if isinstance(r, tuple) and len(r) == 2:
                ok = bool(r[0])
                msg = '' if r[1] is None else str(r[1])
            elif r is None:
                ok = True
            else:
                msg = str(r)
                ok = 'Ô£à' in msg
        except Exception:
            ok = False
            msg = ''
        try:
            self.finished_with_result.emit(ok, msg)
        except Exception:
            return
class _MonitorWorker(QThread):
    log_message = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    finished_with_results = pyqtSignal(object)
    def __init__(self, target_callable, parent=None):
        super().__init__(parent)
        self._target = target_callable
        self._stopped = False
    def request_stop(self):
        self._stopped = True
    def _on_callback(self, message):
        if self._stopped:
            return
        try:
            self.log_message.emit(str(message) if message is not None else '')
            return
        except Exception:
            return
    def run(self):
        results = None
        try:
            results = self._target(self._on_callback)
        except Exception as e:
            if not self._stopped:
                try:
                    self.error_occurred.emit(str(e))
                except Exception:
                    pass
                try:
                    self.finished_with_results.emit(None)
                except Exception:
                    pass
        if not self._stopped:
            try:
                self.finished_with_results.emit(results)
            except Exception:
                return
class AdwareTools(QWidget):
    _USE_MONITOR_WORKER = True
    _monitor_log_request = pyqtSignal(str, object)
    _monitor_status_request = pyqtSignal(str, object)
    _monitor_finished_request = pyqtSignal(object, object)
    _monitor_error_request = pyqtSignal(str, object)
    def __init__(self, parent=None, adb_manager=None):
        super().__init__(parent)
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self.adb = adb_manager or ADBManager()
        self.app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assets_dir = os.path.join(self.app_dir, 'assets')
        self.icon_path = os.path.join(self.assets_dir, 'icons')
        self.json_blacklist = load_json_blacklist()
        self.command_thread = None
        self.active_command = ''
        self._busy_action = False
        self._reset_worker = None
        self._regen_worker = None
        self._monitor_workers = {}
        self._monitor_next_ctx = 0
        try:
            self._monitor_log_request.connect(self._on_monitor_log_request)
            self._monitor_status_request.connect(self._on_monitor_status_request)
            self._monitor_finished_request.connect(self._on_monitor_finished_request)
            self._monitor_error_request.connect(self._on_monitor_error_request)
        except Exception:
            pass
        self.setup_styles()
        self.setup_ui()
    def _on_monitor_log_request(self, message, log_target):
        if log_target is None:
            return
        try:
            log_target.append(str(message))
            return
        except RuntimeError:
            return
        except Exception:
            return
    def _on_monitor_status_request(self, message, status_label):
        if status_label is None:
            return
        try:
            status_label.setText(str(message))
            return
        except RuntimeError:
            return
        except Exception:
            return
    def _on_monitor_finished_request(self, results, ctx_id):
        ctx = self._monitor_workers.pop(ctx_id, None)
        if ctx is None:
            return
        try:
            on_results = ctx.get('on_results')
            cleanup = ctx.get('cleanup')
            if on_results is not None:
                try:
                    on_results(results)
                except Exception as e:
                    logger.error('Monitor on_results falhou: %s', e)
                    logger.error(traceback.format_exc())
            if cleanup is not None:
                try:
                    cleanup()
                except Exception:
                    pass
        finally:
            worker = ctx.get('worker')
            if worker is not None:
                try:
                    if worker.isRunning():
                        worker.wait(1000)
                    worker.deleteLater()
                except Exception:
                    pass
        worker = ctx.get('worker')
        if worker is not None:
            try:
                if worker.isRunning():
                    worker.wait(1000)
                worker.deleteLater()
            except Exception:
                return
    def _on_monitor_error_request(self, error_msg, ctx_id):
        ctx = self._monitor_workers.get(ctx_id)
        if ctx is None:
            return
        try:
            on_error = ctx.get('on_error')
            if on_error is not None:
                try:
                    on_error(str(error_msg))
                except Exception as e:
                    logger.error('Monitor on_error falhou: %s', e)
                    logger.error(traceback.format_exc())
                return
        except Exception:
            return
    def _iniciar_monitor_worker(self, target_callable, on_results, on_error=None, log_target=None, status_label=None, cleanup=None):
        ctx_id = self._monitor_next_ctx
        self._monitor_next_ctx += 1
        worker = _MonitorWorker(target_callable, parent=self)
        def _on_log(msg, _log=log_target, _status=status_label, _self=self):
            try:
                _self._monitor_log_request.emit(msg, _log)
                if _status is not None:
                    _self._monitor_status_request.emit(msg, _status)
                    return
            except Exception:
                pass
        def _on_finished(results, _self=self, _ctx=ctx_id):
            try:
                _self._monitor_finished_request.emit(results, _ctx)
                return
            except Exception:
                return
        def _on_error(error_msg, _self=self, _ctx=ctx_id):
            try:
                _self._monitor_error_request.emit(error_msg, _ctx)
                return
            except Exception:
                return
        worker.log_message.connect(_on_log)
        worker.finished_with_results.connect(_on_finished)
        worker.error_occurred.connect(_on_error)
        self._monitor_workers[ctx_id] = {'worker': worker, 'on_results': on_results, 'on_error': on_error, 'cleanup': cleanup}
        worker.start()
        return ctx_id
    @staticmethod
    def _resolve_adware_layout_profile(dpi_scale):
        try:
            scale = float(dpi_scale) if dpi_scale else 1.0
        except (TypeError, ValueError):
            scale = 1.0
        scale = max(1.0, scale)
        if scale >= 1.53:
            return {'tier': 'ultra_compact', 'primary_h': 29, 'step_h': 28, 'sec_h': 28, 'primary_font': 11, 'step_font': 11, 'sec_font': 11, 'left_min': 340}
        if scale >= 1.38:
            return {'tier': 'compact', 'primary_h': 31, 'step_h': 30, 'sec_h': 30, 'primary_font': 12, 'step_font': 11, 'sec_font': 11, 'left_min': 380}
        if scale >= 1.15:
            return {'tier': 'intermediate', 'primary_h': 33, 'step_h': 32, 'sec_h': 32, 'primary_font': 12, 'step_font': 12, 'sec_font': 12, 'left_min': 420}
        return {'tier': 'normal', 'primary_h': 35, 'step_h': 34, 'sec_h': 34, 'primary_font': 13, 'step_font': 13, 'sec_font': 12, 'left_min': 460}
    def _apply_adware_layout_responsive_fix(self):
        if os.environ.get('UI_ADWARE_LAYOUT_FIX', '1') != '1':
            return
        try:
            from PyQt5.QtWidgets import QApplication, QSizePolicy
            dpi_scale = 1.0
            try:
                qapp = QApplication.instance()
                if qapp is not None:
                    screen = qapp.primaryScreen()
                    if screen is not None:
                        logical_dpi = screen.logicalDotsPerInch()
                        if logical_dpi and logical_dpi > 0:
                            dpi_scale = max(1.0, float(logical_dpi) / 96.0)
            except Exception:
                dpi_scale = 1.0
            else:
                profile = self._resolve_adware_layout_profile(dpi_scale)
        except Exception as e:
            try:
                logger.warning('Adware layout fix nao aplicado (mantendo legado): %s', type(e).__name__)
            except Exception:
                e = None
                del e
                return
        try:
            logger.info('Adware layout: dpi=%.2f tier=%s primary=%d step=%d sec=%d', dpi_scale, profile['tier'], profile['primary_h'], profile['step_h'], profile['sec_h'])
        except Exception:
            pass
        def _apply_group(buttons, height, font_pt):
            for btn in buttons or []:
                if btn is not None:
                    try:
                        btn.setFixedHeight(int(height))
                        btn.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
                        f = btn.font()
                        f.setPointSize(int(font_pt))
                        btn.setFont(f)
                    except Exception:
                        continue
        _apply_group(getattr(self, '_btns_primary', []), profile['primary_h'], profile['primary_font'])
        _apply_group(getattr(self, '_btns_step', []), profile['step_h'], profile['step_font'])
        _apply_group(getattr(self, '_btns_secondary', []), profile['sec_h'], profile['sec_font'])
        try:
            lsa = getattr(self, '_left_scroll_area', None)
            if lsa is not None:
                lsa.setMinimumWidth(int(profile['left_min']))
                return
        except Exception as e:
            try:
                try:
                    logger.warning('Adware layout fix nao aplicado (mantendo legado): %s', type(e).__name__)
                except Exception:
                    return
            except Exception:
                e = None
                del e
                return
    def setup_styles(self):
        self.button_style = '\n            QPushButton {\n                padding: 6px 12px;\n                font-size: 9pt;\n                background-color: #2196F3;\n                color: white;\n                border-radius: 4px;\n                font-weight: 600;\n                border: none;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n            QPushButton:pressed {\n                background-color: #0D47A1;\n            }\n            QPushButton:disabled {\n                background-color: #94a3b8;\n                color: #f1f5f9;\n            }\n        '
        self._palette_premium = {'csi': ('#2196F3', '#1976D2', '#0D47A1'), 'advanced': ('#2196F3', '#1976D2', '#0D47A1'), 'enhanced': ('#2196F3', '#1976D2', '#0D47A1'), 'monitor': ('#2196F3', '#1976D2', '#0D47A1')}
        self.warning_button_style = '\n            QPushButton {\n                padding: 6px 12px;\n                font-size: 9pt;\n                background-color: #c0392b;\n                color: white;\n                border-radius: 4px;\n                font-weight: bold;\n                border: none;\n            }\n            QPushButton:hover {\n                background-color: #e74c3c;\n            }\n            QPushButton:pressed {\n                background-color: #a93226;\n            }\n            QPushButton:disabled {\n                background-color: #e6b0aa;\n                color: #ecf0f1;\n            }\n        '
    def _coloriza_button_style(self, key):
        try:
            base, hover, pressed = self._palette_premium[key]
        except (KeyError, AttributeError, TypeError):
            return self.button_style
        return self.button_style.replace('background-color: #2196F3', f'background-color: {base}').replace('background-color: #1976D2', f'background-color: {hover}').replace('background-color: #0D47A1', f'background-color: {pressed}')
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(6, 6, 6, 6)
        header = QLabel('Detector de Adware e Aplicativos Maliciosos')
        header.setStyleSheet('\n            font-size: 11pt;\n            font-weight: bold;\n            color: #1e40af;\n            background-color: #eff6ff;\n            padding: 8px 12px;\n            border-left: 4px solid #3b82f6;\n            border-radius: 4px;\n        ')
        main_layout.addWidget(header)
        description = QLabel('Esta ferramenta detecta e remove aplicativos potencialmente maliciosos, adware e outros softwares indesejados do seu dispositivo Android.')
        description.setWordWrap(True)
        description.setStyleSheet('color: #475569; font-size: 9pt; margin-bottom: 4px;')
        main_layout.addWidget(description)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(6)
        left_scroll_area = QScrollArea()
        left_scroll_area.setWidgetResizable(True)
        left_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll_area.setStyleSheet('\n            QScrollArea { border: none; background-color: transparent; }\n            QScrollBar:vertical {\n                background-color: #ecf0f1; width: 8px;\n                border-radius: 4px; margin: 0px;\n            }\n            QScrollBar::handle:vertical {\n                background-color: #95a5a6; border-radius: 4px; min-height: 20px;\n            }\n            QScrollBar::handle:vertical:hover { background-color: #7f8c8d; }\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                border: none; background: none;\n            }\n        ')
        left_panel = QFrame()
        left_panel.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border-radius: 6px;\n                border: 1px solid #e0e0e0;\n            }\n        ')
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(8, 8, 8, 8)
        status_frame = QFrame()
        status_frame.setStyleSheet('\n            QFrame {\n                background-color: #2c3e50;\n                border-radius: 6px;\n                padding: 6px;\n            }\n            QLabel {\n                color: white;\n            }\n        ')
        status_layout = QVBoxLayout(status_frame)
        status_layout.setSpacing(4)
        status_layout.setContentsMargins(6, 6, 6, 6)
        self.connection_status = QLabel('Status: Verificando conexao...')
        self.connection_status.setStyleSheet('font-weight: bold; font-size: 9pt;')
        self.connection_status.setVisible(False)
        status_layout.addWidget(self.connection_status)
        self.device_info = QLabel('Nenhum dispositivo conectado')
        self.device_info.setWordWrap(True)
        self.device_info.setVisible(False)
        status_layout.addWidget(self.device_info)
        self.usb_device_widget = None
        if UsbDeviceWidget is not None:
            try:
                self.usb_device_widget = UsbDeviceWidget(adb_manager=self.adb, parent=status_frame, dark_mode=True)
                self.usb_device_widget.request_reset_adb.connect(self._on_usb_widget_reset_adb)
                self.usb_device_widget.request_reauthorize.connect(self._on_usb_widget_reauthorize)
                self.usb_device_widget.request_regenerate_keys.connect(self._on_usb_widget_regenerate_keys)
                self.usb_device_widget.request_open_devices.connect(self._on_usb_widget_open_devices)
                self.usb_device_widget.devices_updated.connect(self._on_usb_widget_devices_updated)
                status_layout.addWidget(self.usb_device_widget)
            except Exception as exc:
                self.logger.debug(f'painel ao vivo indisponivel: {exc}')
                self.usb_device_widget = None
            else:
                try:
                    try:
                        if hasattr(self.usb_device_widget, 'apply_dpi_profile'):
                            self.usb_device_widget.apply_dpi_profile()
                    except Exception:
                        pass
                except Exception as exc:
                    self.logger.debug(f'painel ao vivo indisponivel: {exc}')
                    self.usb_device_widget = None
        self._btn_tutorial = QPushButton('Passo a Passo')
        self._btn_tutorial.setCursor(Qt.PointingHandCursor)
        self._btn_tutorial.setStyleSheet('\n            QPushButton {\n                background-color: #422006; color: #fbbf24;\n                border: 1px solid #d97706; border-radius: 3px;\n                padding: 4px 10px; font-size: 8pt; font-weight: 600;\n            }\n            QPushButton:hover { background-color: #713f12; color: #fde68a; }\n            QPushButton:pressed { background-color: #92400e; }\n            QPushButton:disabled { background-color: #0f172a; color: #64748b; border: 1px solid #334155; }\n        ')
        self._btn_tutorial.setToolTip('Abre o passo a passo completo para usar o Tira V├¡rus')
        self._btn_tutorial.clicked.connect(self._abrir_tutorial)
        if self.usb_device_widget and hasattr(self.usb_device_widget, '_toolbar_layout'):
            tl = self.usb_device_widget._toolbar_layout
            tl.insertWidget(tl.count() - 1, self._btn_tutorial)
        else:
            status_layout.addWidget(self._btn_tutorial, alignment=Qt.AlignRight)
        self.check_connection_btn = QPushButton('1. Verificar Conexao')
        self.check_connection_btn.setStyleSheet('\n            QPushButton {\n                background-color: #10b981; color: white; border: none;\n                border-radius: 4px; padding: 6px 12px;\n                font-size: 9pt; font-weight: 600;\n            }\n            QPushButton:hover { background-color: #059669; }\n            QPushButton:pressed { background-color: #047857; }\n            QPushButton:disabled { background-color: #607080; color: #cfd8dc; }\n        ')
        self.check_connection_btn.clicked.connect(self.check_connection_with_message)
        self.check_connection_btn.setToolTip('PASSO 1: Verifica e conecta o aparelho.\nMostra mensagens guia. Use sempre que iniciar o atendimento.')
        left_layout.addWidget(status_frame)
        self.screen_monitor_button = QPushButton('2. Monitor Tela')
        self.screen_monitor_button.setStyleSheet(self.button_style)
        self.screen_monitor_button.clicked.connect(self.run_screen_monitoring)
        self.screen_monitor_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.screen_monitor_button.setToolTip('PASSO 2: Espelha e observa a tela do aparelho.\nAjuda a identificar visualmente anuncios e comportamento suspeito.')
        self.detect_ads_button = QPushButton('3. Monitorar Ads')
        self.detect_ads_button.setStyleSheet(self.button_style)
        self.detect_ads_button.clicked.connect(self.detect_real_time_ads)
        self.detect_ads_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.scan_button = QPushButton('4. Apps Maliciosos')
        self.scan_button.setStyleSheet(self.button_style)
        self.scan_button.clicked.connect(self.detect_adware)
        self.scan_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.block_unknown_btn = QPushButton('5. Blindagem')
        self.block_unknown_btn.setStyleSheet(self.button_style)
        self.block_unknown_btn.clicked.connect(self.blindar_dispositivo)
        self.block_unknown_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.certificado_btn = QPushButton('Certificado')
        self.certificado_btn.setStyleSheet(self.button_style)
        self.certificado_btn.setToolTip('Gera o certificado de protecao (PDF) para entregar ao cliente')
        self.certificado_btn.clicked.connect(self.abrir_certificado_protecao)
        self.certificado_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.csi_scan_button = QPushButton('CSI Triagem')
        self.csi_scan_button.setStyleSheet(self._coloriza_button_style('csi'))
        self.csi_scan_button.clicked.connect(self.run_csi_investigation)
        self.csi_scan_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.csi_scan_button.setToolTip('Investigacao forense baseada em:\n- Apps instalados recentemente (10 dias)\n- Abuso de bateria e atividade em segundo plano\n- Padroes de SDKs de Ads no logcat\n- Combinacoes perigosas de permissoes')
        self.advanced_scan_button = QPushButton('Analise Avancada')
        self.advanced_scan_button.setStyleSheet(self._coloriza_button_style('advanced'))
        self.advanced_scan_button.clicked.connect(self.run_advanced_analysis)
        self.advanced_scan_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.disable_miui_ads_button = QPushButton('Ads MIUI/Hyper')
        self.disable_miui_ads_button.setStyleSheet(self.button_style)
        self.disable_miui_ads_button.clicked.connect(self.disable_miui_ads)
        self.disable_miui_ads_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.disable_miui_ads_button.setToolTip('Remove anuncios nativos de dispositivos Xiaomi/Redmi/POCO.\nATENCAO: Em Android 16+ (HyperOS recentes) pode haver\nrisco de instabilidade. Use com cautela.')
        self.enhanced_scan_button = QPushButton('Analise V2.0')
        self.enhanced_scan_button.setStyleSheet(self._coloriza_button_style('enhanced'))
        self.enhanced_scan_button.clicked.connect(self.run_enhanced_analysis)
        self.enhanced_scan_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        _btn_grid = QGridLayout()
        _btn_grid.setSpacing(4)
        _btn_grid.setColumnStretch(0, 1)
        _btn_grid.setColumnStretch(1, 1)
        _btn_grid.setColumnStretch(2, 1)
        _btn_grid.addWidget(self.check_connection_btn, 0, 0, 1, 3)
        _grid_buttons = [self.screen_monitor_button, self.detect_ads_button, self.scan_button, self.block_unknown_btn, self.certificado_btn, self.csi_scan_button, self.advanced_scan_button, self.disable_miui_ads_button, self.enhanced_scan_button]
        for idx, btn in enumerate(_grid_buttons):
            _btn_grid.addWidget(btn, 1 + idx // 3, idx % 3)
        left_layout.addLayout(_btn_grid)
        left_layout.addStretch(1)
        self._btns_primary = [self.check_connection_btn]
        self._btns_step = [self.screen_monitor_button, self.detect_ads_button, self.scan_button, self.block_unknown_btn]
        self._btns_secondary = [self.certificado_btn, self.csi_scan_button, self.advanced_scan_button, self.disable_miui_ads_button, self.enhanced_scan_button]
        self._left_scroll_area = left_scroll_area
        self._left_panel = left_panel
        self._svg_dir = PathManager.get_resource_path('icons_svg')
        if self._svg_dir and os.path.isdir(self._svg_dir):
            _icon_map = {self._btn_tutorial: 'clipboard2-pulse.svg', self.check_connection_btn: 'usb-plug.svg', self.screen_monitor_button: 'pc-display.svg', self.detect_ads_button: 'broadcast-pin.svg', self.scan_button: 'virus.svg', self.block_unknown_btn: 'shield-fill-check.svg', self.certificado_btn: 'card-checklist.svg', self.csi_scan_button: 'clipboard2-pulse-fill.svg', self.advanced_scan_button: 'virus2.svg', self.disable_miui_ads_button: 'shield-check.svg', self.enhanced_scan_button: 'graph-up.svg'}
            for btn, svg_name in _icon_map.items():
                svg_path = os.path.join(self._svg_dir, svg_name)
                if os.path.isfile(svg_path):
                    btn.setIcon(QIcon(svg_path))
        left_layout.addStretch()
        left_scroll_area.setWidget(left_panel)
        right_panel = QFrame()
        right_panel.setStyleSheet('\n            QFrame {\n                background-color: #1e1e1e;\n                border-radius: 8px;\n                padding: 8px;\n            }\n        ')
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(4)
        right_layout.setContentsMargins(6, 6, 6, 6)
        log_header = QLabel('Log de Atividades')
        log_header.setStyleSheet('\n            color: white;\n            font-weight: bold;\n            font-size: 9pt;\n            padding: 4px;\n            background-color: #2d2d2d;\n            border-radius: 3px;\n        ')
        right_layout.addWidget(log_header)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("\n            QTextEdit {\n                background-color: #1e1e1e;\n                color: #e0e0e0;\n                border: 1px solid #333;\n                border-radius: 4px;\n                font-family: 'Consolas', 'Courier New', monospace;\n                font-size: 9pt;\n                padding: 6px;\n            }\n        ")
        right_layout.addWidget(self.log_area)
        self.clear_log_btn = QPushButton('Limpar Log')
        self.clear_log_btn.setStyleSheet('\n            QPushButton {\n                background-color: #424242; color: white; border: none;\n                border-radius: 3px; padding: 4px 10px;\n                font-weight: bold; font-size: 8pt;\n            }\n            QPushButton:hover { background-color: #616161; }\n        ')
        self.clear_log_btn.clicked.connect(self.clear_log)
        self.clear_log_btn.setMaximumWidth(110)
        if hasattr(self, '_svg_dir') and self._svg_dir:
            _clear_svg = os.path.join(self._svg_dir, 'arrow-clockwise.svg')
            if os.path.isfile(_clear_svg):
                self.clear_log_btn.setIcon(QIcon(_clear_svg))
        right_layout.addWidget(self.clear_log_btn, alignment=Qt.AlignRight)
        content_layout.addWidget(left_scroll_area, 6)
        content_layout.addWidget(right_panel, 4)
        main_layout.addLayout(content_layout)
        self._show_initial_message()
    def _show_initial_message(self):
        self.log_area.append('==================================================')
        self.log_area.append('  TIRA VIRUS - TECH UNION SOLUTIONS')
        self.log_area.append('==================================================')
        self.log_area.append('')
        self.log_area.append('  Funciona em MODO ADB (Depuracao USB).')
        self.log_area.append('')
        self.log_area.append('  Requisitos:')
        self.log_area.append('   - Cabo USB conectado')
        self.log_area.append('   - Depuracao USB ativada')
        self.log_area.append('   - Autorizado neste PC')
        self.log_area.append('')
        self.log_area.append('  Funcionalidades:')
        self.log_area.append('   - Scan de adware e malware')
        self.log_area.append('   - Monitoramento de anuncios')
        self.log_area.append('   - Remocao de apps maliciosos')
        self.log_area.append('   - Bloqueio de fontes desconhecidas')
        self.log_area.append('   - Limpeza MIUI/HyperOS')
        self.log_area.append('')
        self.log_area.append('--------------------------------------------------')
        self.log_area.append("  Clique em '1. Verificar Conexao' para iniciar.")
        self.log_area.append('--------------------------------------------------')
        self.connection_status.setText('Status: Aguardando verificacao...')
        self.device_info.setText('Aguardando verificacao de conexao')
        try:
            self._apply_adware_layout_responsive_fix()
            return
        except Exception:
            return
    def _on_usb_widget_devices_updated(self, devices):
        try:
            if not devices:
                return
        except Exception:
            return
        try:
            autorizados = [d for d in devices if (d.get('state') or '').lower() == 'device']
        except Exception:
            return
        try:
            unauthorized = [d for d in devices if (d.get('state') or '').lower() == 'unauthorized']
        except Exception:
            return
        try:
            offline = [d for d in devices if (d.get('state') or '').lower() == 'offline']
            if autorizados:
                modelo = autorizados[0].get('model') or autorizados[0].get('product') or autorizados[0].get('serial') or 'Aparelho'
                self.connection_status.setText('Dispositivo conectado e autorizado')
                self.device_info.setText(f'{modelo}')
                return
            if unauthorized:
                self.connection_status.setText('Aguardando autorizacao no aparelho')
                self.device_info.setText("Toque em 'Permitir' na tela do aparelho.")
                return
            if offline:
                self.connection_status.setText('Conexao instavel detectada')
                self.device_info.setText('Tente reiniciar a conex├úo pelo bot├úo acima.')
                return
            return
        except Exception:
            return
    def _on_usb_widget_open_devices(self):
        try:
            ok = False
            if abrir_gerenciador_dispositivos is not None:
                ok = bool(abrir_gerenciador_dispositivos())
            if not ok:
                QMessageBox.information(self, 'Gerenciador de Dispositivos', "N├úo foi poss├¡vel abrir o Gerenciador automaticamente.\nPressione Windows + X e selecione 'Gerenciador de Dispositivos'.")
                return
        except Exception:
            QMessageBox.information(self, 'Gerenciador de Dispositivos', "N├úo foi poss├¡vel abrir o Gerenciador automaticamente.\nPressione Windows + X e selecione 'Gerenciador de Dispositivos'.")
    def _on_usb_widget_reauthorize(self, serial):
        if not hasattr(self.adb, 'force_reconnect_offline'):
            QMessageBox.information(self, 'Reenviar autoriza├º├úo', 'Fun├º├úo indispon├¡vel neste ambiente.')
            return
        try:
            ok, msg = self.adb.force_reconnect_offline()
            self._refresh_usb_widget_async()
            if ok:
                QMessageBox.information(self, 'Reenviar autoriza├º├úo', msg)
                return
            QMessageBox.warning(self, 'Reenviar autoriza├º├úo', msg)
            return
        except Exception:
            QMessageBox.warning(self, 'Reenviar autoriza├º├úo', 'N├úo foi poss├¡vel reenviar o pedido agora. Tente reiniciar a conex├úo.')
    def _on_usb_widget_reset_adb(self):
        if getattr(self, '_busy_action', False):
            return
        confirm = QMessageBox.question(self, 'Reiniciar conex├úo', "Isso vai reiniciar a comunica├º├úo com o aparelho.\nVoc├¬ poder├í precisar tocar em 'Permitir' no aparelho novamente.\n\nDeseja continuar?", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if confirm != QMessageBox.Yes:
            return
        if not hasattr(self.adb, 'reset_adb_complete'):
            QMessageBox.warning(self, 'Reiniciar conex├úo', 'Fun├º├úo indispon├¡vel neste ambiente.')
            return
        self._begin_async_action('Reiniciando conexao... aguarde alguns segundos.')
        try:
            self.log_area.append('­ƒöä Reiniciando conex├úo com o aparelho...')
        except Exception:
            pass
        worker = _AsyncAdbAction(self.adb.reset_adb_complete, parent=self)
        worker.finished_with_result.connect(self._on_reset_adb_finished)
        worker.finished.connect(worker.deleteLater)
        self._reset_worker = worker
        worker.start()
        QTimer.singleShot(90000, self._force_end_async_if_stuck)
    def _on_reset_adb_finished(self, ok, _msg):
        self._end_async_action()
        try:
            self.log_area.append('Ô£à Conex├úo reiniciada.' if ok else 'ÔÜá´©Å Rein├¡cio terminou com aviso.')
        except Exception:
            pass
        self._refresh_usb_widget_async()
        if ok:
            QMessageBox.information(self, 'Conex├úo reiniciada', "Conex├úo reiniciada com sucesso.\nSe o aparelho mostrar um pedido de permiss├úo, toque em 'Permitir'.")
            return
        QMessageBox.warning(self, 'Conex├úo reiniciada', 'A conex├úo foi reiniciada, por├®m pode ser necess├írio reconectar o cabo USB ou reiniciar o aparelho.')
    def _on_usb_widget_regenerate_keys(self):
        if getattr(self, '_busy_action', False):
            return
        confirm = QMessageBox.question(self, 'Renovar autoriza├º├úo', "Esta a├º├úo vai limpar a autoriza├º├úo atual deste computador e fazer o aparelho mostrar um novo pedido de permiss├úo.\n\nUse quando o aparelho n├úo mostra mais o pedido de 'Permitir USB'.\n\nDeseja continuar?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        if not hasattr(self.adb, 'regenerate_adb_keys'):
            QMessageBox.warning(self, 'Renovar autoriza├º├úo', 'Fun├º├úo indispon├¡vel neste ambiente.')
            return
        self._begin_async_action('Renovando autorizacao... aguarde alguns segundos.')
        try:
            self.log_area.append('­ƒöæ Renovando autoriza├º├úo do aparelho...')
        except Exception:
            pass
        worker = _AsyncAdbAction(self.adb.regenerate_adb_keys, parent=self)
        worker.finished_with_result.connect(self._on_regenerate_keys_finished)
        worker.finished.connect(worker.deleteLater)
        self._regen_worker = worker
        worker.start()
        QTimer.singleShot(90000, self._force_end_async_if_stuck)
    def _on_regenerate_keys_finished(self, ok, msg):
        self._end_async_action()
        try:
            self.log_area.append('Ô£à Pronto. Olhe o aparelho.' if ok else 'ÔÜá´©Å N├úo foi poss├¡vel renovar agora.')
        except Exception:
            pass
        self._refresh_usb_widget_async()
        if ok:
            QMessageBox.information(self, 'Renovar autoriza├º├úo', msg or 'Pronto.')
            return
        QMessageBox.warning(self, 'Renovar autoriza├º├úo', msg or 'N├úo foi poss├¡vel renovar a autoriza├º├úo. Reinicie o aplicativo e tente de novo.')
    def _begin_async_action(self, status_text):
        self._busy_action = True
        try:
            self.connection_status.setText(status_text)
            self.device_info.setText('N├úo desconecte o cabo at├® esta etapa terminar.')
        except Exception:
            pass
        try:
            _w = getattr(self, 'usb_device_widget', None)
            if _w is not None:
                _btn = getattr(_w, '_btn_refresh', None)
                if _btn is not None:
                    _btn.setEnabled(False)
                    return
                return
        except Exception:
            pass
    def _end_async_action(self):
        self._busy_action = False
        try:
            _w = getattr(self, 'usb_device_widget', None)
            if _w is not None:
                _btn = getattr(_w, '_btn_refresh', None)
                if _btn is not None:
                    _btn.setEnabled(True)
                    return
                return
        except Exception:
            pass
    def _force_end_async_if_stuck(self):
        if getattr(self, '_busy_action', False):
            logger.warning('Timeout de 90s ÔÇö liberando UI (worker pode estar travado).')
            self._end_async_action()
    def _refresh_usb_widget_async(self):
        try:
            if self.usb_device_widget is not None:
                QTimer.singleShot(300, self.usb_device_widget.force_refresh)
                return
        except Exception:
            pass
    def closeEvent(self, event):
        try:
            if getattr(self, 'usb_device_widget', None) is not None:
                self.usb_device_widget.stop()
        except Exception:
            pass
        try:
            super().closeEvent(event)
        except Exception:
            return
    def hideEvent(self, event):
        try:
            if getattr(self, 'usb_device_widget', None) is not None:
                self.usb_device_widget.stop()
        except Exception:
            pass
        try:
            super().hideEvent(event)
        except Exception:
            return
    _TUTORIAL_ID = 6
    _TUTORIAL_CACHE = 'tv_guide.bin'
    _TUTORIAL_CD = 5
    def _abrir_tutorial(self):
        import time as _t
        if _t.monotonic() - getattr(self, '_tut_ts', 0) < self._TUTORIAL_CD:
            return
        self._tut_ts = _t.monotonic()
        if hasattr(self, '_tut_dlg') and self._tut_dlg and self._tut_dlg.isVisible():
            self._tut_dlg.raise_()
            self._tut_dlg.activateWindow()
            return
        self._btn_tutorial.setEnabled(False)
        try:
            data = self._tut_get_img()
            if not data:
                self.log_area.append('ÔÜá´©Å Tutorial indispon├¡vel no momento.')
                self._btn_tutorial.setEnabled(True)
                return
            self._tut_show(data)
        except Exception:
            self.log_area.append('ÔÜá´©Å N├úo foi poss├¡vel carregar o tutorial.')
        finally:
            self._btn_tutorial.setEnabled(True)
    def _tut_cache_path(self):
        try:
            from app.utils._res_loader import _cache_dir
            return os.path.join(_cache_dir(), self._TUTORIAL_CACHE)
        except Exception:
            return
    def _tut_get_img(self):
        cache = self._tut_cache_path()
        if cache and os.path.isfile(cache):
            try:
                with open(cache, 'rb') as f:
                    d = f.read()
                if len(d) > 1024:
                    return d
            except Exception:
                pass
        blob = self._tut_fetch()
        if not blob:
            return
        if cache:
            try:
                with open(cache, 'wb') as f:
                    f.write(blob)
            except Exception:
                pass
            return blob
        return blob
    def _tut_fetch(self):
        import pymysql
        try:
            from app.utils._app_cfg import db_config
            conn = pymysql.connect(**db_config(), **{'ssl': {'ca': None}, 'ssl_verify_cert': False})
            cur = conn.cursor()
            cur.execute('SELECT arquivo_blob FROM conteudos_dinamicos WHERE id=%s AND ativo=1 LIMIT 1', (self._TUTORIAL_ID,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row and row[0]:
                return bytes(row[0])
        except Exception:
            pass
    def _tut_show(self, img_data: bytes):
        from PyQt5.QtGui import QPixmap
        px = QPixmap()
        if not px.loadFromData(img_data):
            self.log_area.append('ÔÜá´©Å Formato de imagem n├úo suportado.')
            return
        dlg = QDialog(self)
        dlg.setWindowTitle('Passo a Passo - Tira Virus')
        dlg.setAttribute(Qt.WA_DeleteOnClose)
        dlg.showMaximized()
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel()
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet('background-color: #1e293b;')
        screen = QApplication.primaryScreen()
        if screen:
            sw = screen.availableGeometry().width() - 40
        else:
            sw = 1400
        scaled = px.scaledToWidth(min(px.width(), sw), Qt.SmoothTransformation)
        lbl.setPixmap(scaled)
        scroll = QScrollArea()
        scroll.setWidget(lbl)
        scroll.setWidgetResizable(False)
        scroll.setAlignment(Qt.AlignCenter)
        scroll.setStyleSheet('QScrollArea { background-color: #1e293b; border: none; }')
        layout.addWidget(scroll)
        self._tut_dlg = dlg
        dlg.finished.connect((lambda: setattr(self, '_tut_dlg', None)))
    def clear_log(self):
        self.log_area.clear()
        self.log_area.append('­ƒöä Log limpo.')
    def check_connection(self):
        try:
            if self.adb.is_device_connected():
                device_info = self.adb.get_device_info()
                if isinstance(device_info, str):
                    self.connection_status.setText('Erro ao obter informacoes do dispositivo')
                    self.device_info.setText(f'{device_info}')
                    self.log_area.append(f'ÔÜá´©Å Erro ao obter informa├º├Áes do dispositivo: {device_info}')
                    self.scan_button.setEnabled(True)
                    self.block_unknown_btn.setEnabled(True)
                    return
                model = device_info.get('model', 'Desconhecido')
                brand = device_info.get('brand', 'Desconhecido')
                android = device_info.get('android', 'Desconhecido')
                self.connection_status.setText('Dispositivo conectado')
                self.device_info.setText(f'{brand} {model} - Android {android}')
                self.log_area.append(f'Ô£à Dispositivo detectado: {brand} {model} (Android {android})')
                self.scan_button.setEnabled(True)
                self.block_unknown_btn.setEnabled(True)
                self.detect_ads_button.setEnabled(True)
                self.advanced_scan_button.setEnabled(True)
                self.enhanced_scan_button.setEnabled(True)
                self.screen_monitor_button.setEnabled(True)
                self.csi_scan_button.setEnabled(True)
                is_xiaomi = 'xiaomi' in brand.lower() or 'redmi' in brand.lower() or 'poco' in brand.lower()
                self.disable_miui_ads_button.setEnabled(is_xiaomi)
                return
            self.connection_status.setText('Nenhum dispositivo conectado')
            self.device_info.setText('Conecte um dispositivo via USB e ative a Depuracao USB')
            self.log_area.append('ÔØî Nenhum dispositivo detectado. Por favor, conecte um dispositivo Android.')
            self.scan_button.setEnabled(False)
            self.block_unknown_btn.setEnabled(False)
            self.detect_ads_button.setEnabled(False)
            self.disable_miui_ads_button.setEnabled(False)
            self.advanced_scan_button.setEnabled(False)
            self.enhanced_scan_button.setEnabled(False)
            self.screen_monitor_button.setEnabled(False)
            self.csi_scan_button.setEnabled(False)
            return
        except Exception as e:
            logger.error(f'Erro ao verificar conex├úo: {e}')
            self.connection_status.setText('Erro ao verificar conexao')
            self.device_info.setText('Nao foi possivel comunicar com o dispositivo')
            self.log_area.append('ÔÜá´©Å Erro ao verificar conex├úo. Verifique o cabo USB e a depura├º├úo USB.')
            self.scan_button.setEnabled(False)
            self.block_unknown_btn.setEnabled(False)
            self.detect_ads_button.setEnabled(False)
            self.disable_miui_ads_button.setEnabled(False)
            self.advanced_scan_button.setEnabled(False)
            self.enhanced_scan_button.setEnabled(False)
            self.screen_monitor_button.setEnabled(False)
            self.csi_scan_button.setEnabled(False)
    def _on_auth_loop_finished(self, ok, _msg):
        self._end_async_action()
        if ok:
            self.log_area.append('Ô£à Dispositivo autorizado com sucesso!')
            self.check_connection()
            self._refresh_usb_widget_async()
            QMessageBox.information(self, 'Dispositivo autorizado', 'Dispositivo autorizado!\n\nAgora voce pode usar todas as ferramentas.')
            return
        self.log_area.append('ÔÜá´©Å Nao foi possivel obter autorizacao automaticamente.')
        self.log_area.append('')
        self.log_area.append('­ƒÆí DICA ÔÇö Se o aparelho tem virus cobrindo a tela:')
        self.log_area.append('   1. Desligue o aparelho')
        self.log_area.append('   2. Ligue segurando Volume (-) para MODO SEGURO')
        self.log_area.append("   3. Em Modo Seguro, toque 'Permitir' no popup USB")
        self.log_area.append('   4. Reinicie normal e repita a verificacao')
        self._refresh_usb_widget_async()
        QMessageBox.warning(self, 'Autorizacao necessaria', "Nao foi possivel autorizar automaticamente.\n\nSe a tela do aparelho esta bloqueada por virus:\n\n1. Desligue o aparelho\n2. Ligue em MODO SEGURO (Volume - ao ligar)\n3. Toque 'Permitir' quando o popup aparecer\n4. Reinicie normal e volte aqui\n\nEm Modo Seguro nenhum virus roda.")
    def check_connection_with_message(self):
        try:
            self.check_connection()
            self._refresh_usb_widget_async()
            if not self.adb.is_device_connected():
                _tem_unauthorized = False
            try:
                _estados = self.adb.get_device_states_detailed()
                _tem_unauthorized = any((''.lower() == 'unauthorized' for d in _estados if d.get('state')))
            except Exception:
                pass
            else:
                if _tem_unauthorized and hasattr(self.adb, 'aguardar_autorizacao'):
                    self._begin_async_action('Forcando autorizacao no aparelho...')
                    self.log_area.append('­ƒöÉ Aparelho detectado ÔÇö forcando popup de autorizacao...')
                    self.log_area.append('­ƒô▒ Olhe a tela do aparelho e toque em PERMITIR')
                    worker = _AsyncAdbAction((lambda: (self.adb.aguardar_autorizacao(max_tentativas=8), '')), parent=self)
                    worker.finished_with_result.connect(self._on_auth_loop_finished)
                    worker.finished.connect(worker.deleteLater)
                    self._auth_worker = worker
                    worker.start()
                    QTimer.singleShot(90000, self._force_end_async_if_stuck)
                    return
                QMessageBox.information(self, 'Dispositivo nao conectado', "Nenhum dispositivo Android conectado!\n\nPara conectar o dispositivo:\n\n1. Conecte o dispositivo via cabo USB\n2. Ative o 'Modo Desenvolvedor':\n   - Va em Configuracoes > Sobre o telefone\n   - Toque 7 vezes em 'Numero da versao'\n\n3. Habilite a 'Depuracao USB':\n   - Va em Configuracoes > Opcoes do desenvolvedor\n   - Ative 'Depuracao USB'\n\n4. Autorize o computador no dispositivo\n\nApos seguir esses passos, clique novamente em 'Verificar Conexao'.")
                self.log_area.append('ÔØî Nenhum dispositivo conectado. Consulte as instru├º├Áes de conex├úo.')
                return
        except Exception as e:
            logger.error(f'Erro na verifica├º├úo manual: {e}')
            QMessageBox.critical(self, 'Erro ao verificar conexao', 'Erro ao verificar conexao com o dispositivo.\n\nVerifique se:\n- O cabo USB esta conectado corretamente\n- A depuracao USB esta ativada\n- Nao ha outras aplicacoes usando o ADB')
            self.log_area.append('ÔØî Erro na verifica├º├úo manual. Verifique a conex├úo USB e tente novamente.')
    def execute_command(self, function, *args, **kwargs):
        if self.command_thread and hasattr(self.command_thread, 'isRunning') and self.command_thread.isRunning():
            self.command_thread.stop()
            self.command_thread = None
        _FRIENDLY_NAMES = {'detect_malicious_apps': 'Verificacao de aplicativos', 'detect_real_time_ads_impl': 'Deteccao em tempo real', 'block_unknown_sources': 'Bloqueio de fontes desconhecidas', 'run_screen_monitoring': 'Monitoramento de tela', 'execute_enhanced_scan_impl': 'Varredura aprimorada', 'disable_miui_ads': 'Desativacao de anuncios'}
        _raw_name = getattr(function, '__name__', 'operacao')
        self.active_command = _FRIENDLY_NAMES.get(_raw_name, 'Operacao em andamento')
        self.command_thread = CommandThread(function, *args, **kwargs)
        self.command_thread.command_started.connect(self.on_command_started)
        self.command_thread.command_finished.connect(self.on_command_finished)
        self.command_thread.command_error.connect(self.on_command_error)
    def on_command_started(self):
        self.log_area.append(f'\n=== Iniciando {self.active_command} ===\n')
        self.scan_button.setEnabled(False)
        self.block_unknown_btn.setEnabled(False)
        self.detect_ads_button.setEnabled(False)
        self.disable_miui_ads_button.setEnabled(False)
        self.advanced_scan_button.setEnabled(False)
        self.enhanced_scan_button.setEnabled(False)
        self.screen_monitor_button.setEnabled(False)
        self.csi_scan_button.setEnabled(False)
    def on_command_finished(self, result):
        if result:
            self.log_area.append(result)
        self.scan_button.setEnabled(True)
        self.block_unknown_btn.setEnabled(True)
        self.detect_ads_button.setEnabled(True)
        self.advanced_scan_button.setEnabled(True)
        self.enhanced_scan_button.setEnabled(True)
        self.screen_monitor_button.setEnabled(True)
        self.csi_scan_button.setEnabled(True)
        try:
            brand = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop ro.product.brand']).strip().lower()
            is_xiaomi = 'xiaomi' in brand or 'redmi' in brand or 'poco' in brand
            self.disable_miui_ads_button.setEnabled(is_xiaomi)
        except:
            self.disable_miui_ads_button.setEnabled(False)
        try:
            self.adb.finalize_adb_operation()
        except:
            pass
        QTimer.singleShot(1000, self.check_connection)
    def on_command_error(self, error):
        self.log_area.append(f'ÔØî Erro: {error}')
        self.scan_button.setEnabled(True)
        self.block_unknown_btn.setEnabled(True)
        self.detect_ads_button.setEnabled(True)
        self.advanced_scan_button.setEnabled(True)
        self.enhanced_scan_button.setEnabled(True)
        self.screen_monitor_button.setEnabled(True)
        self.csi_scan_button.setEnabled(True)
        try:
            brand = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop ro.product.brand']).strip().lower()
            is_xiaomi = 'xiaomi' in brand or 'redmi' in brand or 'poco' in brand
            self.disable_miui_ads_button.setEnabled(is_xiaomi)
            return
        except:
            self.disable_miui_ads_button.setEnabled(False)
    def refresh_adb_connection(self):
        QTimer.singleShot(500, self.check_connection)
    def detect_adware(self):
        try:
            if not self.adb.is_device_connected():
                self.log_area.append('ÔØî Nenhum dispositivo conectado. Por favor, conecte um dispositivo Android.')
                QMessageBox.warning(self, 'Dispositivo n├úo encontrado', 'Nenhum dispositivo Android conectado!\n\nPor favor, conecte um dispositivo via USB e ative a Depura├º├úo USB.')
                return
            self.log_area.append('\n=== Iniciando detec├º├úo de Virus ===\n')
            self.log_area.append('Ô£à Dispositivo conectado. Iniciando detec├º├úo de aplicativos maliciosos...')
            self.execute_command(self.detect_malicious_apps)
            return
        except Exception as e:
            self.log_area.append(f'ÔØî Erro ao iniciar detec├º├úo: {str(e)}')
            self.logger.error('Falha ao iniciar deteccao: %s', e)
            QMessageBox.critical(self, 'Erro', 'Falha ao iniciar deteccao. Verifique a conexao com o dispositivo.')
    def detect_malicious_apps(self):
        try:
            output = '\n============================================================\n'
            output += '­ƒøí´©Å DETEC├ç├âO DE APPS MALICIOSOS\n'
            output += '============================================================\n\n'
            output += 'Buscando aplicativos suspeitos...\n'
            try:
                brand = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop ro.product.brand']).strip().lower()
                if 'xiaomi' in brand or 'redmi' in brand or 'poco' in brand:
                    miui_ads_status = self.check_miui_ads()
                    if miui_ads_status:
                        output += '­ƒô▒ Dispositivo Xiaomi detectado com an├║ncios nativos do sistema.\n'
                        output += f'ÔÇó {miui_ads_status}\n'
            except Exception as e:
                self.logger.debug(f'Erro ao verificar an├║ncios MIUI: {str(e)}')
            else:
                overlay_apps = self.adb._run_adb_command([self.adb.adb_path, 'shell', "dumpsys window windows | grep -i 'SYSTEM_ALERT_WINDOW'"])
                overlay_packages = []
                for line in overlay_apps.split('\n'):
                    if 'package=' in line:
                        package_start = line.find('package=') + 8
                        package_end = line.find(' ', package_start)
                        if package_end == -1:
                            package_end = len(line)
                        package_name = line[package_start:package_end]
                        if not package_name:
                            continue
                        if package_name not in overlay_packages:
                            overlay_packages.append(package_name)
                output += f'ÔÇó Encontrados {len(overlay_packages)} aplicativos com permiss├úo de overlay\n'
                user_apps_output = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'pm list packages -3'])
                user_apps = []
                if user_apps_output:
                    for line in user_apps_output.split('\n'):
                        if line.startswith('package:'):
                            app_name = line[8:].strip()
                            if not app_name:
                                continue
                            if app_name not in user_apps:
                                user_apps.append(app_name)
                output += f'ÔÇó Encontrados {len(user_apps)} aplicativos instalados pelo usu├írio\n'
                device_admins_output = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys device_policy'])
                admin_apps = []
                if device_admins_output:
                    for line in device_admins_output.split('\n'):
                        if 'admin=' in line:
                            admin_start = line.find('admin=') + 6
                            admin_end = line.find(' ', admin_start)
                            if admin_end == -1:
                                admin_end = len(line)
                            admin_name = line[admin_start:admin_end].strip('{}')
                            if not admin_name:
                                continue
                            if admin_name not in admin_apps:
                                admin_apps.append(admin_name)
                output += f'ÔÇó Encontrados {len(admin_apps)} aplicativos com privil├®gios de administrador\n'
                accessibility_output = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'settings get secure enabled_accessibility_services'])
                accessibility_apps = []
                if accessibility_output and accessibility_output.strip() != 'null':
                    for service in accessibility_output.strip().split(':'):
                        if '/' in service:
                            app_name = service.split('/')[0]
                            if not app_name:
                                continue
                            if app_name not in accessibility_apps:
                                accessibility_apps.append(app_name)
                output += f'ÔÇó Encontrados {len(accessibility_apps)} aplicativos com permiss├Áes de acessibilidade\n'
        except Exception as e:
            logger.error(f'Erro ao verificar aplicativos maliciosos: {str(e)}')
            logger.error(traceback.format_exc())
            error_msg = 'Erro ao verificar aplicativos. Verifique a conexao.'
            QApplication.processEvents()
            QMessageBox.critical(self, 'Erro', error_msg)
            return error_msg
        try:
            boot_apps_output = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys package | grep -i BOOT_COMPLETED | grep -i receive'])
            boot_apps = []
            for line in boot_apps_output.split('\n'):
                if '/' in line:
                    parts = line.strip().split()
                    for part in parts:
                        if '/' in part:
                            app_name = part.split('/')[0]
                            if not app_name.startswith('com.'):
                                continue
                            if app_name not in boot_apps:
                                boot_apps.append(app_name)
            output += f'ÔÇó Encontrados {len(boot_apps)} apps que iniciam no boot\n'
        except Exception:
            boot_apps = []
            output += 'ÔÇó Nao foi possivel verificar apps de boot\n'
        try:
            try:
                hidden_apks = self.adb._run_adb_command([self.adb.adb_path, 'shell', "find /sdcard -name '*.apk' -o -name '*.dex' 2>/dev/null"])
                suspicious_apks = []
                if hidden_apks:
                    for apk in hidden_apks.strip().split('\n'):
                        if not apk:
                            continue
                        if len(apk) > 5:
                            suspicious_apks.append(apk)
                if suspicious_apks:
                    output += f'ÔÇó ÔÜá´©Å ATEN├ç├âO! Encontrados {len(suspicious_apks)} arquivos APK/DEX no armazenamento!\n'
                    output += '  Estes arquivos podem ser usados para reinstalar malware ap├│s a limpeza.\n'
                    suspicious_dirs_check = self.adb._run_adb_command([self.adb.adb_path, 'shell', "find /sdcard -type d -name 'com.mufc.*' -o -name '*dropper*' 2>/dev/null"])
                    if suspicious_dirs_check and len(suspicious_dirs_check.strip()) > 5:
                        output += 'ÔÇó ÔÜá´©Å ALERTA! Encontradas pastas possivelmente associadas com malware persistente!\n'
                        output += '  Detectadas pastas suspeitas que podem ser usadas para reinstala├º├úo persistente de malware.\n'
            except Exception as e:
                output += f'ÔÇó N├úo foi poss├¡vel verificar arquivos APK suspeitos: {str(e)}\n'
        except Exception as e:
            logger.error(f'Erro ao verificar aplicativos maliciosos: {str(e)}')
            logger.error(traceback.format_exc())
            error_msg = 'Erro ao verificar aplicativos. Verifique a conexao.'
            QApplication.processEvents()
            QMessageBox.critical(self, 'Erro', error_msg)
            return error_msg
        self.log_area.append(output)
        QApplication.processEvents()
        self.show_malicious_apps_dialog(overlay_packages, user_apps, admin_apps, boot_apps, accessibility_apps)
        return output
    def abrir_certificado_protecao(self):
        try:
            if not self.adb.is_device_connected():
                QMessageBox.warning(self, 'Dispositivo', 'Nenhum dispositivo conectado.\n\nConecte o aparelho com a depura├º├úo USB ativada e tente novamente.')
                return
            from app.views.protection_certificate import CertificadoProtecaoDialog
            dialog = CertificadoProtecaoDialog(self.adb, parent=self)
            dialog.exec_()
            return
        except Exception:
            self.logger.debug('Falha ao abrir o certificado de prote├º├úo.', exc_info=True)
            QMessageBox.warning(self, 'Certificado', 'N├úo foi poss├¡vel abrir o certificado. Tente novamente.')
    def blindar_dispositivo(self):
        try:
            if not self.adb.is_device_connected():
                QMessageBox.warning(self, 'Dispositivo', 'Nenhum dispositivo conectado.\n\nConecte o aparelho com a depura├º├úo USB ativada e tente novamente.')
                self.block_unknown_btn.setEnabled(True)
                return
            reply = QMessageBox.question(self, 'Blindagem', 'Esta opera├º├úo refor├ºa a prote├º├úo do dispositivo contra aplicativos indesejados, preservando as lojas oficiais.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply != QMessageBox.Yes:
                self.block_unknown_btn.setEnabled(True)
                return
            self.block_unknown_btn.setEnabled(False)
            self.log_area.append('\n­ƒøí´©Å Iniciando blindagem do dispositivo...')
            QApplication.processEvents()
            from app.utils.adware_hardening import DeviceHardening
            def _progresso(msg):
                self.log_area.append(f'  ÔÇó {msg}')
                QApplication.processEvents()
            resumo = DeviceHardening(self.adb).aplicar(progresso=_progresso)
            if resumo.get('ok'):
                self.log_area.append('Ô£à Blindagem conclu├¡da.')
                QMessageBox.information(self, 'Blindagem', 'Blindagem conclu├¡da com sucesso.\n\nO dispositivo est├í mais protegido contra aplicativos indesejados, mantendo as lojas oficiais funcionando normalmente.')
            else:
                self.log_area.append('ÔÜá´©Å Blindagem conclu├¡da parcialmente.')
                QMessageBox.warning(self, 'Blindagem', 'N├úo foi poss├¡vel concluir toda a blindagem neste dispositivo.\n\nAlguns ajustes podem n├úo ser suportados pelo fabricante. Recomenda-se revisar as configura├º├Áes de seguran├ºa do aparelho.')
        except Exception:
            self.logger.debug('Falha ao aplicar blindagem.', exc_info=True)
            self.log_area.append('ÔØî N├úo foi poss├¡vel concluir a blindagem.')
            QMessageBox.warning(self, 'Blindagem', 'N├úo foi poss├¡vel concluir a blindagem.\n\nVerifique a conex├úo do dispositivo e tente novamente.')
        finally:
            self.block_unknown_btn.setEnabled(True)
    def show_malicious_apps_dialog(self, overlay_apps, user_apps, admin_apps, boot_apps, accessibility_apps):
        try:
            if not overlay_apps and not user_apps and not admin_apps and not boot_apps and not accessibility_apps:
                QMessageBox.information(self, 'Sem Aplicativos Suspeitos', 'N├úo foram encontrados aplicativos suspeitos no dispositivo.')
                return
            known_adware_patterns = ['com.sec.spp.push', 'com.splendapps.voicerec', 'br.com.izio.loyalty.novomix', 'com.osp.app.signin.overlay.pt', 'ws.hanzo.Vrih', 'com.android.app.popupcalculator.overlay.pt', 'com.teacapps.barcodescanner', 'com.eggs.bloodflow', 'com.zzkko', 'com.eggs.bloodflow', 'com.releasecly.clyphone.clyphonewarning', 'com.nvt.cs', 'com.iconchanger.widget.theme.shortcut', 'shadow.sw.pper', 'zen.task.zt', 'cn.wps.xiaomi.abroad.lite', 'listify.list.ify', 'com.cyber.clean', 'com.lemon.lvoverseas', 'com.outfit7.mytalkingtomfriends', 'schedule.note.tdl', 'antivirus.virus.cleaner.clean.vpn.booster', 'com.piriform.ccleaner', 'nb.ph.fixer', 'br.com.w12.evobeta', 'com.zhiliaapp.musically', 'com.block.juggle', 'com.blackout.bubble', 'com.lianhezhuli.hyfit', 'com.azurgames.stackball', 'com.zhiliaoapp.musically', 'com.rsupport.rs.activity.rsupport.aas2', 'com.rtbosuro.moodscape', 'SamsungUX.DW.FreshP07.wallpapermulti', 'com.microsoft.office.officehubrow', 'com.eggs.bloodflow', 'com.b2w.americanas', 'com.mobapps.credguia', 'com.spawn.clear.now.clean', 'com.alibaba.aliexpresshd', 'com.F2Games.GBDE', 'br.com.bscash', 'com.motoboy.mottu', 'com.uieodlckeu.sketch', 'com.ONRIStudio.JustPlayground', 'com.mitsofwares.newappbancaapostas', 'com.etg.qr.scanner', 'com.amazon.appmanager', 'com.top.thememorygame', 'br.com.softnex.portal.mobile.romcard.convenio', 'br.com.rs.lp7', 'com.popstar.luckypuzzle.dmmc', 'com.oakever.tiletrip', 'com.aquela_receita_app', 'pdfreader.pdftviewer.officetool.pdfscanner', 'com.cyber.fox', 'pdfscanner.scan.pdf.scanner.free', 'br.com.apcasp.app', 'com.healthbmi.shapetrack.loprot', 'com.applediy.funnymya', 'com.mobile.legends', 'com.junk.security.files.scanner.killer.stcleaner', 'com.playspare.supermarket.store.simulator', 'org.chromium.webapk.a09e446ec24491dfa_v2', 'com.scenery.tile.earn.money.game.challenge', 'gc.good.cleaner', 'ring.glow.call.style.tone', 'cc.clever.ccccleaner', 'br.com.cpfl.android.autoatendimento', 'br.com.dekmobile.cpflite', 'com.Happy.Video', 'com.zhilia0app.musically', 'com.cleanfiner.phoneclean', 'games.spearmint.triplecrush', 'com.cleanplanner', 'com.filesclean.ultraclean.master', 'com.tas.westernsurvival.shooterwar', 'com.wifikeyrecovery.wifiautoconnect.wifipasswordshow.wifiautomaticunlock.internetspeedtest', 'com.king.candycrushsaga', 'com.einnovation.temu', 'com.measure.heartrate.bloodpressure', 'com.bg.shooting.cs.contractsniper', 'com.LoopGames.Domino', 'com.funtomic.matchmasters', 'com.gamovation.tileclub', 'com.playvalve.dominoes', 'com.tellmewow.senior.wheel.fortune', 'com.easybrain.hidden.spots', 'com.rioo.runnersubway', 'br.com.sky.selfcare', 'jigsaw.puzzle.free.games', 'com.tripledot.blockbash', 'com.roblox.client', 'br.com.atacadao.b2c.app', 'com.pdfreader.free.viewer.documentreader', 'com.plusfile.ma', 'heart.pulse.beacon.log', 'com.mobfiq.calzedonia', 'applock.lockapps.fingerprint.password.applocker', 'com.cbs.ca', 'com.mactime.invistity.app', 'sf.smart.file', 'ef.easy.file', 'com.fly.web.smart.browser', 'com.sunoeuyc.nebuduir', 'com.quickemail.quicklogin.emailonline', 'com.check.clashlegends305', 'com.haping.moodawat.emo', 'com.clean.fast.launcher', 'com.mate.vpn', 'com.drink.pal.hy', 'com.refrigeratorwallspapers', 'pdf.pdfreader.viewer.editor.free', 'br.lgfelicio', 'com.learned.guard.jildo', 'com.kaching.merchant', 'com.dailywallpaper.prozg', 'nb.ph.fixer', 'com.devplank.masterfip', 'org.chromium.webapk.a8b685054f1cd9f5e_v2', 'com.niam.smartswitch.phonecloneapp.easytransfer', 'com.gpsnotecam.photonotesandgeotagging', 'com.qrscanner.qrueser', 'com.icedblueberry.shoppinglisteasy', 'com.kms.placafipe', 'com.aquapulse.waterdrink', 'com.rocks.music.videoplayer', 'com.dywx.larkplayer', 'com.self.diary', 'com.jouirlb.emonest', 'task.planner.tp', 'zc.ze.clean', 'com.mobile.file.manage.secretary.media.collect.ssp', 'sinet.startup.inDriver', 'cg.clean.cleango', 'com.filespecialist.storagem', 'com.newleaf.app.android.victor', 'com.browser.privacy.stool.bookmark.security', 'com.ideasyt.photo', 'com.junkfileclean.catcher2', 'kwai.lite.video', 'com.lemon.lvoverseas', 'org.chromium.webapk.ac53e5e316dde28f0_v2', 'eu.livesport.FlashScore.com', 'cn.xiaofengkj.fitpro', 'com.zhilia0app.musically', 'com.nglereactnative', 'com.photo.editor.square.pic.splash', 'com.zkkko', 'com.shopee.br', 'com.herocraft.game.treasuresofthedeep', 'com.hydration.drinkpal', 'com.storytellera.note', 'com.infisecurity.cleaner', 'com.mathgenius.quickresolver', 'com.quickmathto.resolver', 'ads', 'ad.', 'advert', 'notification', 'notify', 'sponsor', 'analytics', 'tracker', 'cleaner', 'booster', 'speedup', 'com.adware', 'com.ads', 'ads.', '.ad.', 'advert', 'notification', 'notify', 'sponsor', 'campaign', 'analytics', 'promo', 'banner', 'push', 'tracking', 'market', 'appsgeyser', 'cleaner', 'speedbooster', 'speed.booster', 'system.clean', 'battery.saver', 'ram.booster', 'optimizer', 'clean.master', 'antivirus', 'security.app', 'browser.fast', 'browser.clean', 'browser.light', 'lighter', 'smart.app', 'super.app', 'boost', 'weather.channel', 'weather.forecast', 'screen.recorder', 'payjoy', 'mdm', 'quickapp', 'quick.app', 'update.service', 'appcenter', 'app.center', 'download.manager', 'downloader', 'nb.ph.fixer', 'myfiles.filemanager.fileexplorer', 'filemanager.fileexplorer', 'com.hroeldueo', 'happyemoji', 'emoji', 'keyboard.theme', 'com.zzkko', 'com.mufc', 'cache.cleaner', 'phone.cleaner', 'splash', 'smart.cleaner', 'master.cleaner', 'speed.clean', 'security.boost', 'virus.clean', 'lite.clean', 'fast.clean', 'battery.doctor', 'power.saver', 'cpu.cooler', 'ram.clean', 'smart.booster', 'memory.optimizer', 'junk.cleaner', 'silent.clean', 'game.booster', 'file.browser', 'file.explorer', 'quick.share', 'share.it', 'vpn.proxy', 'free.vpn', 'flash.light', 'led.torch', 'video.downloader', 'music.downloader', 'mp3.download', 'tube.download', 'com.infisecurity.cleaner', 'com.mathgenius.quickresolver', 'com.quickmathto.resolver', 'quickmath', 'mathgenius', 'quickmath.solver', 'resolver', 'mathto', 'com.nvt.cs', 'com.zhiliaoapp.musically', 'com.rsupport.rs.activity.rsupport.aas2', 'com.fix.duplicate.files.clean', 'com.arabola.bacolom', 'com.phone.cleaner.shineapps', 'com.sec.android.app.sbrowser.webapk', 'com.fc.p.gp.skincare.makeup.makeover.asmr.game', 'sword.drows.sdwp', 'cn.wps.moffice_eng', 'com.funcell.petsimulator', 'com.booking', 'com.Giantstep.Moon', 'com.playstrom.dop2', 'bg.essoftware.ladypopular.fashionarena', 'abstrac.abtt.awpp', 'com.yoosee', 'com.yg.sf.minigames', 'time.tf.flux', 'com.gamee.brainly.homepin3.pullpin.puzzle', 'com.stickermoba.avatarmaker', 'com.duokan.phone.remotecontroller', 'kr.co.alohacorp.BlasttheGiant', 'com.mianglow.mepapers', 'com.glamour.superpapers', 'halo.edge.lighting.show', 'com.xdev.docxreader.docx.docxviewer.document.doc.office.viewer.reader.word', 'com.asyncbyte.moneytracker_int', 'br.com.passagensimperdiveis', 'com.rizwan.simplepdfreader2018', 'com.pdf.read.view.editor.pdfreader.pdfviewer', 'com.graffiti.memos.redyellow', 'com.daily.forecast.weather.radar', 'com.gpsmapcamera.geotagginglocationonphoto', 'com.pdfreader.zone', 'com.end.beach.sleepsound', 'com.led.effect.scroller', 'com.raizen.acelera', 'com.theme.sleepsound.abcd', 'com.einnovation.temu', 'com.gamerman.graderworksimulator', 'com.realGC.roadconstruction', 'com.longpath.trd', 'com.directiongames.autolifebrasil', 'com.dynamicgames.driversjobonlinesimulator', 'com.dynamicgames.worldbusdrivingsimulator', 'com.dynamicgames.worldtruckdrivingsimulator', 'com.turborocketgames.wildcraft', 'com.zuuks.bus.simulator.ultimate', 'com.PtronPlayDigital.EtiketTofask', 'com.lokys.tractor', 'com.sebby.rebaixadoselitebrasil', 'com.gamestopventure.usfarmingtractor3dgames', 'com.blockblast.adventuremaster.blockpuzzle.samsung', 'com.f5game.msdlld', 'com.MaxStudios.EliteBrasilSimulator', 'com.stargameapp.trucksimbrasil.TruckSimBrasil', 'com.trophygames.truckmanager', 'com.stargamesapps.farmingsimbrasil', 'com.BharatiyaAMGames.IndianTractorSimulater24', 'com.heavy.crane.simulator', 'cn.wps.moffice_eng', 'ru.zdevs.zarchiver', 'org.chromium.webapk.a74544ee85262f17b_v2', 'org.chromium.webapk.abc81432d89886e70_v2', 'org.chromium.webapk.ae72bb21ecf69f12c_v2', 'org.chromium.webapk.af3aeac1a9b21f1ec_v2', 'org.chromium.webapk.a94718b3b6f70ab87_v2', 'ball.sort.water.puzzle', 'world.social.group.video.share', 'com.whatsapp.web.dual.app.scanner', 'holiday.traverse.search.festival', 'com.sweetfruit.candy', 'com.novinever.imagepop.ina', 'com.superbox.aos.fire2048', 'com.unicostudio.tilematch', 'com.vitastudio.mahjong', 'nine.grid.cut.photo.maker.for.instagram', 'com.free.speedify', 'com.happymood.apk', 'com.Celltop.SpiralRoll', 'com.bvieopsueiw.lightwiz', 'com.indian.mountain.jeep.drive.nearme.gamecenter', 'media.mp3player.musicplayer', 'de.vsmedia.imagesizer', 'br.org.apphcjds.activity', 'sort.ball.puzzle.color.match.puzzle.sorting', 'com.core.biggames.marble.android', 'com.ikame.pdf.pdfreader.pdfviewer.editor', 'com.ezt.pdfreader.pdfviewer', 'com.alldocument.plus', 'com.supermusic.free.music.player.online.offline.music', 'com.moonvideo.android.resso', 'com.hydration.drinkpal', 'com.storytellera.note', 'com.infisecurity.cleaner', 'com.mathgenius.quickresolver', 'com.quickmathto.resolver', 'ads', 'ad.', 'advert', 'notification', 'notify', 'sponsor', 'analytics', 'tracker', 'cleaner', 'booster', 'speedup', 'com.adware', 'com.ads', 'ads.', '.ad.', 'advert', 'notification', 'notify', 'sponsor', 'campaign', 'analytics', 'promo', 'banner', 'push', 'tracking', 'market', 'appsgeyser', 'cleaner', 'speedbooster', 'speed.booster', 'system.clean', 'battery.saver', 'ram.booster', 'optimizer', 'clean.master', 'antivirus', 'security.app', 'browser.fast', 'browser.clean', 'browser.light', 'lighter', 'smart.app', 'super.app', 'boost', 'weather.channel', 'weather.forecast', 'screen.recorder', 'payjoy', 'mdm', 'quickapp', 'quick.app', 'update.service', 'appcenter', 'app.center', 'download.manager', 'downloader', 'nb.ph.fixer', 'myfiles.filemanager.fileexplorer', 'filemanager.fileexplorer', 'com.hroeldueo', 'happyemoji', 'emoji', 'keyboard.theme', 'com.zzkko', 'com.mufc', 'cache.cleaner', 'phone.cleaner', 'splash', 'smart.cleaner', 'master.cleaner', 'speed.clean', 'security.boost', 'virus.clean', 'lite.clean', 'fast.clean', 'battery.doctor', 'power.saver', 'cpu.cooler', 'ram.clean', 'smart.booster', 'memory.optimizer', 'junk.cleaner', 'silent.clean', 'game.booster', 'file.browser', 'file.explorer', 'quick.share', 'share.it', 'vpn.proxy', 'free.vpn', 'flash.light', 'led.torch', 'video.downloader', 'music.downloader', 'mp3.download', 'tube.download', 'com.infisecurity.cleaner', 'com.mathgenius.quickresolver', 'com.quickmathto.resolver', 'quickmath', 'mathgenius', 'quickmath.solver', 'resolver', 'mathto', 'com.nvt.cs', 'com.zhiliaoapp.musically', 'com.rsupport.rs.activity.rsupport.aas2', 'com.fix.duplicate.files.clean', 'com.arabola.bacolom', 'com.phone.cleaner.shineapps', 'com.sec.android.app.sbrowser.webapk', 'com.fc.p.gp.skincare.makeup.makeover.asmr.game', 'sword.drows.sdwp', 'cn.wps.moffice_eng', 'com.funcell.petsimulator', 'com.booking', 'com.Giantstep.Moon', 'com.playstrom.dop2', 'bg.essoftware.ladypopular.fashionarena', 'abstrac.abtt.awpp', 'com.yoosee', 'com.yg.sf.minigames', 'time.tf.flux', 'com.gamee.brainly.homepin3.pullpin.puzzle', 'com.stickermoba.avatarmaker', 'com.duokan.phone.remotecontroller', 'kr.co.alohacorp.BlasttheGiant', 'com.kwai.video', 'hands.android.webmotors', 'com.mianglow.mepapers', 'com.glamour.superpapers', 'halo.edge.lighting.show', 'com.xdev.docxreader.docx.docxviewer.document.doc.office.viewer.reader.word', 'com.asyncbyte.moneytracker_int', 'br.com.passagensimperdiveis', 'com.rizwan.simplepdfreader2018', 'com.pdf.read.view.editor.pdfreader.pdfviewer', 'com.graffiti.memos.redyellow', 'com.daily.forecast.weather.radar', 'com.gpsmapcamera.geotagginglocationonphoto', 'com.pdfreader.zone', 'com.end.beach.sleepsound', 'com.led.effect.scroller', 'com.raizen.acelera', 'com.theme.sleepsound.abcd', 'com.einnovation.temu', 'com.shopee.br', 'com.gamerman.graderworksimulator', 'com.realGC.roadconstruction', 'com.longpath.trd', 'com.directiongames.autolifebrasil', 'com.dynamicgames.driversjobonlinesimulator', 'com.dynamicgames.worldbusdrivingsimulator', 'com.dynamicgames.worldtruckdrivingsimulator', 'com.turborocketgames.wildcraft', 'com.zuuks.bus.simulator.ultimate', 'com.PtronPlayDigital.EtiketTofask', 'com.lokys.tractor', 'com.sebby.rebaixadoselitebrasil', 'com.gamestopventure.usfarmingtractor3dgames', 'com.blockblast.adventuremaster.blockpuzzle.samsung', 'com.f5game.msdlld', 'com.MaxStudios.EliteBrasilSimulator', 'com.stargameapp.trucksimbrasil.TruckSimBrasil', 'com.trophygames.truckmanager', 'com.stargamesapps.farmingsimbrasil', 'com.BharatiyaAMGames.IndianTractorSimulater24', 'com.heavy.crane.simulator']
            suspicious_apps_patterns = ['br.com.cea.appb2c', 'com.br.com.hering', 'com.yoosee', 'com.buthop.canvasflow']
            mdm_apps = ['com.payjoy.access', 'com.payjoy.permission', 'com.motorola.fota', 'com.motorola.ccc.ota', 'com.motorola.paks', 'com.motorola.paksnotification', 'com.motorola.sysdll', 'com.samsung.android.knox.mdm', 'com.samsung.knox.mdm.agent', 'com.mobileiron', 'com.airwatch.androidagent', 'com.microsoft.intune', 'com.vmware.airwatchagent', 'com.blackberry.uem.agent', 'com.adups.fota', 'com.adups.fota.sysoper', 'com.fw.upgrade.sysoper', 'com.lsdroid.cerberus', 'com.lsdroid.cerberusapp', 'com.ogksoftware.hiddeneye', 'com.invoxia.track', 'com.thetrackr.android', 'org.thoughtcrime.securesms.backup', 'com.qadeer.SmartControls', 'com.neatspy', 'com.phonelive.share', 'com.cell.tracker', 'com.find.location', 'com.phone.tracker']
            try:
                boot_apps_output = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys package | grep -i BOOT_COMPLETED | grep -i receive'])
                boot_apps = []
                for line in boot_apps_output.split('\n'):
                    if '/' in line:
                        parts = line.strip().split()
                        for part in parts:
                            if '/' in part:
                                app_name = part.split('/')[0]
                                if not app_name.startswith('com.'):
                                    continue
                                if app_name not in boot_apps:
                                    boot_apps.append(app_name)
            except:
                boot_apps = []
            else:
                package_labels = {}
                for app in set(overlay_apps + user_apps + admin_apps + boot_apps + accessibility_apps):
                    pass
        except Exception as e:
            logger.error(f'Erro ao criar di├ílogo de apps maliciosos: {str(e)}')
            logger.error(traceback.format_exc())
            self.logger.error('Erro ao exibir lista de aplicativos: %s', e)
            QMessageBox.critical(self, 'Erro', 'Erro ao exibir a lista de aplicativos. Tente novamente.')
        suspicious_apps = set()
        trusted_system_apps = ['com.android.launcher', 'com.android.launcher2', 'com.android.launcher3', 'com.android.systemui', 'com.miui.home', 'com.mi.android.globallauncher', 'com.miui.securitycenter', 'com.miui.securitycore', 'com.miui.systemAdSolution', 'com.miui.cleanmaster', 'com.miui.daemon', 'com.xiaomi.misettings', 'com.xiaomi.account', 'com.xiaomi.finddevice', 'com.sec.android.app.launcher', 'com.sec.android.emergencylauncher', 'com.samsung.android.honeyboard', 'com.samsung.android.oneconnect', 'com.huawei.android.launcher', 'com.hihonor.android.launcher', 'com.huawei.systemmanager', 'com.huawei.hwid', 'com.vivo.launcher', 'com.bbk.launcher2', 'com.oppo.launcher', 'com.color.safecenter', 'com.coloros.safecenter', 'com.oneplus.launcher', 'com.oneplus.security', 'com.motorola.launcher3', 'com.motorola.launcherconfig', 'com.motorola.launcher3overlay', 'com.motorola.systemui', 'com.asus.launcher', 'com.asus.zenui.launcher', 'com.lge.launcher2', 'com.lge.launcher3', 'com.google.android.apps.nexuslauncher', 'com.google.android.permissioncontroller', 'com.teslacoilsw.launcher', 'com.anddoes.launcher', 'com.actionlauncher.playstore', 'com.microsoft.launcher', 'com.lawnchair.launcher', 'com.poco.launcher', 'com.sprd.powersavemodelauncher', 'com.transsion.XOSLauncher', 'com.transsion.XOSLauncher.upgrade', 'com.ontim.launcher3.overlay', 'com.ss.android.ugc.aweme', 'com.google.android.marvin.talkback', 'com.samsung.android.accessibility.talkback']
        filtered_overlay_apps = []
        for app in overlay_apps:
            if any((trusted_app in app for trusted_app in trusted_system_apps)):
                continue
            try:
                pass
            except Exception as e:
                logger.error(f'Erro ao criar di├ílogo de apps maliciosos: {str(e)}')
                logger.error(traceback.format_exc())
                self.logger.error('Erro ao exibir lista de aplicativos: %s', e)
                QMessageBox.critical(self, 'Erro', 'Erro ao exibir a lista de aplicativos. Tente novamente.')
            if 'launcher' in app.lower():
                continue
            try:
                pass
            except Exception as e:
                logger.error(f'Erro ao criar di├ílogo de apps maliciosos: {str(e)}')
                logger.error(traceback.format_exc())
                self.logger.error('Erro ao exibir lista de aplicativos: %s', e)
                QMessageBox.critical(self, 'Erro', 'Erro ao exibir a lista de aplicativos. Tente novamente.')
            if 'systemui' in app.lower():
                continue
        for app in admin_apps:
            if any((trusted_app in app for trusted_app in trusted_system_apps)):
                continue
            if 'launcher' in app.lower():
                continue
            if 'systemui' in app.lower():
                continue
            suspicious_apps.add(app)
        for app in user_apps:
            if any((trusted_app in app for trusted_app in trusted_system_apps)):
                continue
            app_lower = app.lower()
            if any((pattern in app_lower for pattern in known_adware_patterns)):
                suspicious_apps.add(app)
            elif any((pattern in app_lower for pattern in self.json_blacklist)):
                suspicious_apps.add(f'­ƒôï {app} (Identificado na base de ameacas)')
            elif any((pattern in app_lower for pattern in suspicious_apps_patterns)):
                suspicious_apps.add(f'ÔÜá´©Å {app} (Apenas alerta - App leg├¡timo com comportamento suspeito)')
            if app in mdm_apps:
                suspicious_apps.add(app)
            if app not in boot_apps:
                continue
            if 'launcher' in app_lower:
                continue
            if 'systemui' in app_lower:
                continue
            suspicious_apps.add(app)
            continue
        dialog = QDialog(self)
        dialog.setWindowTitle('Remover Aplicativos Maliciosos')
        dialog.setWindowState(Qt.WindowMaximized)
        dialog.setMinimumSize(800, 600)
        dialog.resize(1200, 900)
        dialog.setStyleSheet("\n                QDialog {\n                    background-color: #f5f5f5;\n                }\n                QLabel {\n                    font-size: 13px;\n                    margin-bottom: 10px;\n                    color: #333333;\n                }\n                QLabel#warning {\n                    color: #d32f2f;\n                    font-weight: bold;\n                }\n                QLabel#header {\n                    font-size: 14px;\n                    font-weight: bold;\n                    color: #1976D2;\n                    margin-top: 10px;\n                }\n                QPushButton {\n                    padding: 8px 16px;\n                    background-color: #2196F3;\n                    color: white;\n                    border: none;\n                    border-radius: 4px;\n                    font-weight: bold;\n                    min-height: 35px;\n                }\n                QPushButton:hover {\n                    background-color: #1976D2;\n                }\n                QPushButton:pressed {\n                    background-color: #1565C0;\n                }\n                QPushButton#removeBtn {\n                    background-color: #f44336;\n                }\n                QPushButton#removeBtn:hover {\n                    background-color: #d32f2f;\n                }\n                QListWidget {\n                    border: 1px solid #ccc;\n                    border-radius: 4px;\n                    padding: 5px;\n                    background-color: white;\n                    font-family: 'Segoe UI', Arial, sans-serif;\n                    font-size: 12px;\n                    color: #000000;\n                }\n                QListWidget::item {\n                    padding: 5px;\n                    border-bottom: 1px solid #eee;\n                    min-height: 24px;\n                    color: #000000;\n                }\n                QListWidget::item:hover {\n                    background-color: #e3f2fd;\n                }\n                QListWidget::item:selected {\n                    background-color: #bbdefb;\n                    color: black;\n                }\n                QCheckBox {\n                    padding: 5px;\n                    color: #000000;\n                }\n                QScrollArea {\n                    border: none;\n                    background-color: transparent;\n                }\n                QScrollBar:vertical {\n                    background-color: #f0f0f0;\n                    width: 12px;\n                    border-radius: 6px;\n                    margin: 0px;\n                }\n                QScrollBar::handle:vertical {\n                    background-color: #c0c0c0;\n                    border-radius: 6px;\n                    min-height: 20px;\n                }\n                QScrollBar::handle:vertical:hover {\n                    background-color: #a0a0a0;\n                }\n                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                    border: none;\n                    background: none;\n                }\n            ")
        main_scroll = QScrollArea(dialog)
        main_scroll.setWidgetResizable(True)
        main_scroll.setFrameShape(QScrollArea.NoFrame)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_widget = QWidget()
        main_scroll.setWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(main_scroll)
        header = QLabel('Selecione os aplicativos suspeitos para remover:')
        header.setObjectName('header')
        layout.addWidget(header)
        warning = QLabel('ÔÜá´©Å AVISO: Remova apenas aplicativos que voc├¬ identificou como maliciosos.\nN├úo remova apps de sistema ou apps leg├¡timos necess├írios ao funcionamento do dispositivo.')
        warning.setObjectName('warning')
        layout.addWidget(warning)
        list_widget = QListWidget()
        list_widget.setAlternatingRowColors(True)
        categories = [('­ƒö┤ Aplicativos com OVERLAY (alta prioridade)', overlay_apps, True), ('­ƒƒá Aplicativos com Admin Device (suspeitos)', admin_apps, True), ('­ƒƒí Outros aplicativos instalados pelo usu├írio', user_apps, False), ('­ƒöä Aplicativos que iniciam na inicializa├º├úo', boot_apps, False), ('­ƒöÆ Aplicativos com permiss├Áes de acessibilidade', accessibility_apps, False)]
        for category_name, app_list, is_suspicious in categories:
            if not app_list:
                continue
            header_item = QListWidgetItem(category_name)
            header_item.setFlags(Qt.ItemIsEnabled)
            header_item.setBackground(Qt.lightGray)
            header_item.setForeground(Qt.black)
            header_item.setFont(QFont('Segoe UI', 9, QFont.Bold))
            list_widget.addItem(header_item)
            for app in app_list:
                app_name = package_labels.get(app, app.split('.')[-1].capitalize())
                critical_system_apps = ['com.android.systemui', 'com.android.launcher3', 'com.miui.home', 'com.samsung.android.app.launcher', 'com.google.android.apps.nexuslauncher']
                is_system_critical = app in critical_system_apps
                icon_text = ''
                if is_system_critical:
                    icon_text += 'Ôøö­ƒøí´©Å '
                elif app in overlay_apps:
                    icon_text += '­ƒö┤ '
                if app in admin_apps:
                    icon_text += '­ƒƒá '
                if app in boot_apps:
                    icon_text += '­ƒöä '
                if any((pattern in app.lower() for pattern in known_adware_patterns)):
                    icon_text += 'ÔÜá´©Å '
                if app in mdm_apps:
                    icon_text += '­ƒöÆ '
                if is_system_critical:
                    full_text = f'{icon_text}{app_name} ({app}) - ÔÜá´©Å SISTEMA CR├ìTICO - N├âO REMOVER!'
                else:
                    full_text = f'{icon_text}{app_name} ({app})'
                item = QListWidgetItem(full_text)
                item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                if is_system_critical:
                    item.setCheckState(Qt.Unchecked)
                elif app in suspicious_apps:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)
                if is_system_critical:
                    item.setForeground(QColor(255, 140, 0))
                    item.setBackground(QColor(255, 245, 230))
                    item.setFont(QFont('Segoe UI', 10, QFont.Bold))
                    if app == 'com.android.systemui':
                        item.setToolTip('ÔÜá´©Å PERIGO EXTREMO: SystemUI ├® o n├║cleo da interface do Android!\nRemover este app ir├í QUEBRAR COMPLETAMENTE o sistema!\n­ƒøí´©Å O dispositivo pode n├úo conseguir mais inicializar!\n­ƒÆÇ N├âO marque este item JAMAIS!')
                    else:
                        item.setToolTip(f'ÔÜá´©Å CUIDADO: {app_name} ├® um componente importante do sistema!\nRemover pode causar instabilidade ou problemas!\n­ƒøí´©Å S├│ marque se tiver CERTEZA ABSOLUTA!')
                elif app in suspicious_apps:
                    item.setForeground(Qt.red)
                    item.setFont(QFont('Segoe UI', 9, QFont.Bold))
                item.setData(Qt.UserRole, app)
                list_widget.addItem(item)
                continue
            continue
        layout.addWidget(list_widget)
        selected_count_label = QLabel('0 aplicativos selecionados')
        layout.addWidget(selected_count_label)
        def update_selected_count():
            count = 0
            selected_packages = []
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                if not item.flags() & Qt.ItemIsUserCheckable:
                    continue
                if item.checkState() == Qt.Checked:
                    count += 1
                    app_package = item.data(Qt.UserRole)
                    if app_package:
                        selected_packages.append(app_package)
            selected_count_label.setText(f'{count} aplicativos selecionados')
            return selected_packages
        list_widget.itemChanged.connect((lambda: update_selected_count()))
        button_layout = QHBoxLayout()
        critical_apps_in_list = []
        for category_name, app_list, is_suspicious in categories:
            for app in app_list:
                if app in ('com.android.systemui', 'com.android.launcher3', 'com.miui.home', 'com.samsung.android.app.launcher', 'com.google.android.apps.nexuslauncher'):
                    critical_apps_in_list.append(app)
        if critical_apps_in_list:
            warning_frame = QFrame()
            warning_frame.setStyleSheet('\n                    QFrame {\n                        background-color: #fff3e0;\n                        border: 2px solid #ff9800;\n                        border-radius: 5px;\n                        padding: 10px;\n                        margin-bottom: 10px;\n                    }\n                ')
            warning_layout = QVBoxLayout(warning_frame)
            warning_label = QLabel('ÔÜá´©Å APPS DE SISTEMA DETECTADOS!')
            warning_label.setStyleSheet('font-weight: bold; color: #ff9800; font-size: 14px;')
            warning_layout.addWidget(warning_label)
            warning_text = QLabel('Esta lista cont├®m componentes cr├¡ticos do sistema (marcados com Ôøö­ƒøí´©Å).\nEspecial aten├º├úo: SystemUI pode QUEBRAR o dispositivo se removido!­ƒÆÇ')
            warning_text.setStyleSheet('color: #e65100; font-size: 12px;')
            warning_text.setWordWrap(True)
            warning_layout.addWidget(warning_text)
            layout.insertWidget(layout.count() - 1, warning_frame)
        toggle_all_btn = QPushButton('Marcar/Desmarcar Todos (Protege Sistema)')
        toggle_all_btn.setToolTip('Apps cr├¡ticos do sistema N├âO ser├úo marcados automaticamente')
        def toggle_all():
            all_checked = all((list_widget.item(i).checkState() == Qt.Checked for i in range(list_widget.count()) if list_widget.item(i).flags() & Qt.ItemIsUserCheckable))
            new_state = Qt.Unchecked if all_checked else Qt.Checked
            critical_system_apps = ['com.android.systemui', 'com.android.launcher3', 'com.miui.home', 'com.samsung.android.app.launcher', 'com.google.android.apps.nexuslauncher']
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                if item.flags() & Qt.ItemIsUserCheckable:
                    app = item.data(Qt.UserRole)
                    if new_state == Qt.Checked:
                        if app in critical_system_apps:
                            continue
                    item.setCheckState(new_state)
            update_selected_count()
        toggle_all_btn.clicked.connect(toggle_all)
        button_layout.addWidget(toggle_all_btn)
        mark_suspicious_btn = QPushButton('Marcar Apenas Suspeitos')
        def mark_only_suspicious():
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                if item.flags() & Qt.ItemIsUserCheckable:
                    app = item.data(Qt.UserRole)
                    if app in suspicious_apps:
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)
            update_selected_count()
        mark_suspicious_btn.clicked.connect(mark_only_suspicious)
        button_layout.addWidget(mark_suspicious_btn)
        button_layout.addStretch()
        cancel_btn = QPushButton('Cancelar')
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        remove_btn = QPushButton('Remover Selecionados')
        remove_btn.setObjectName('removeBtn')
        remove_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(remove_btn)
        layout.addLayout(button_layout)
        QTimer.singleShot(100, update_selected_count)
        if dialog.exec_() == QDialog.Accepted:
            selected_apps = update_selected_count()
            if selected_apps:
                critical_system_apps = ['com.android.systemui', 'com.android.launcher3', 'com.miui.home', 'com.samsung.android.app.launcher', 'com.google.android.apps.nexuslauncher']
                try:
                    filtered_overlay_apps.append(app)
                    suspicious_apps.add(app)
                    # WARNING: continue outside loop (unrecovered structure)
                except Exception as e:
                    logger.error(f'Erro ao criar di├ílogo de apps maliciosos: {str(e)}')
                    logger.error(traceback.format_exc())
                    self.logger.error('Erro ao exibir lista de aplicativos: %s', e)
                    QMessageBox.critical(self, 'Erro', 'Erro ao exibir a lista de aplicativos. Tente novamente.')
                    try:
                        critical_selected = [app for app in selected_apps if app in critical_system_apps]
                        if critical_selected:
                            critical_apps_str = '\n'.join([f'­ƒÆÇ {app}' for app in critical_selected])
                            if 'com.android.systemui' in critical_selected:
                                critical_msg = f"­ƒÜ¿ PERIGO EXTREMO DETECTADO! ­ƒÜ¿\n\nVoc├¬ selecionou o SYSTEMUI para remo├º├úo:\n\n{critical_apps_str}\n\nÔÜá´©Å REMOVER O SYSTEMUI IR├ü:\nÔÇó QUEBRAR COMPLETAMENTE a interface do Android\nÔÇó Tornar o dispositivo INUTILIZ├üVEL\nÔÇó Impedir que o sistema inicie corretamente\nÔÇó Requerer FORMATA├ç├âO COMPLETA para restaurar\n\n­ƒÆÇ ISSO ├ë IRREVERS├ìVEL E PERIGOSO!\n\nTem CERTEZA ABSOLUTA que deseja continuar?\nDigite 'CONFIRMO RISCO' para prosseguir:"
                                text, ok = QInputDialog.getText(self, '­ƒÆÇ CONFIRMA├ç├âO DE RISCO EXTREMO', critical_msg, QLineEdit.Normal, '')
                                if not ok or text != 'CONFIRMO RISCO':
                                    QMessageBox.information(self, 'Opera├º├úo Cancelada', 'Remo├º├úo cancelada por seguran├ºa. SystemUI N├âO foi removido.')
                                    return
                            else:
                                critical_msg = f'ÔÜá´©Å ATEN├ç├âO: Apps cr├¡ticos selecionados!\n\n{critical_apps_str}\n\nEstes s├úo componentes importantes do sistema.\nRemover pode causar instabilidade ou problemas.\n\nDeseja continuar mesmo assim?'
                                confirm_critical = QMessageBox.question(self, 'ÔÜá´©Å Apps Cr├¡ticos Selecionados', critical_msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                if confirm_critical != QMessageBox.Yes:
                                    return
                    except Exception as e:
                        logger.error(f'Erro ao criar di├ílogo de apps maliciosos: {str(e)}')
                        logger.error(traceback.format_exc())
                        self.logger.error('Erro ao exibir lista de aplicativos: %s', e)
                        QMessageBox.critical(self, 'Erro', 'Erro ao exibir a lista de aplicativos. Tente novamente.')
            QMessageBox.information(self, 'Informa├º├úo', 'Nenhum aplicativo foi selecionado para remo├º├úo.')
            return
        try:
            apps_str = '\n'.join([f'- {app}' for app in selected_apps])
            confirm_msg = f'Tem certeza que deseja desinstalar os seguintes aplicativos?\n\n{apps_str}'
            confirm = QMessageBox.question(self, 'Confirmar Remo├º├úo', confirm_msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if confirm == QMessageBox.Yes:
                self.remove_selected_apps(selected_apps)
                return
            return
        except Exception as e:
            logger.error(f'Erro ao criar di├ílogo de apps maliciosos: {str(e)}')
            logger.error(traceback.format_exc())
            self.logger.error('Erro ao exibir lista de aplicativos: %s', e)
            QMessageBox.critical(self, 'Erro', 'Erro ao exibir a lista de aplicativos. Tente novamente.')
    def remove_selected_apps(self, app_list):
        try:
            _protegidos = obter_pacotes_protegidos(self.adb)
        except Exception:
            _protegidos = set()
        apps_filtrados = []
        for app in app_list:
            if is_pacote_protegido(app, _protegidos):
                logger.info('remove_selected_apps: pacote do sistema sendo removido por decisao do tecnico: %s', app)
            apps_filtrados.append(app)
        if not apps_filtrados:
            QMessageBox.information(self, 'Aviso', 'Nenhum aplicativo selecionado.')
            return
        try:
            hidden_apks = self.adb._run_adb_command([self.adb.adb_path, 'shell', "find /sdcard -name '*.apk' -o -name '*.dex' 2>/dev/null"])
            suspicious_apks = []
            if hidden_apks:
                for apk in hidden_apks.strip().split('\n'):
                    if not apk:
                        continue
                    if len(apk) > 5:
                        suspicious_apks.append(apk)
            if suspicious_apks:
                log_area.append(f'ÔÜá´©Å Encontrados {len(suspicious_apks)} arquivos APK/DEX suspeitos!')
                QApplication.processEvents()
                reply = QMessageBox.question(progress_dialog, 'Arquivos Suspeitos Encontrados', f'Foram encontrados {len(suspicious_apks)} arquivos APK/DEX no armazenamento que\npodem ser usados para reinstalar malware automaticamente.\n\nDeseja remover esses arquivos?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    log_area.append('­ƒùæ´©Å Removendo arquivos APK/DEX suspeitos...')
                    apk_removed = 0
                    for apk in suspicious_apks:
                        pass
            try:
                self.adb._run_adb_command([self.adb.adb_path, 'shell', f"rm -f '{apk}'"])
                apk_removed += 1
                log_area.append(f'   Ô£à Removido: {apk}')
            except Exception as e:
                log_area.append(f'   ÔØî Erro ao remover {apk}: {str(e)}')
            else:
                log_area.append(f'Ô£à {apk_removed} de {len(suspicious_apks)} arquivos suspeitos removidos')
                log_area.append('ÔÜá´©Å Remo├º├úo de arquivos suspeitos cancelada pelo usu├írio')
                log_area.append('Ô£à N├úo foram encontrados arquivos APK/DEX suspeitos')
                log_area.append('\n­ƒöì Verificando pastas suspeitas conhecidas...')
                suspicious_dirs = self.adb._run_adb_command([self.adb.adb_path, 'shell', "find /sdcard -type d -name 'com.mufc.*' -o -name '*dropper*' 2>/dev/null"])
                if suspicious_dirs and len(suspicious_dirs.strip()) > 5:
                    suspicious_dir_list = []
                    for dir_path in suspicious_dirs.strip().split('\n'):
                        if not dir_path:
                            continue
                        if len(dir_path) > 5:
                            suspicious_dir_list.append(dir_path)
                    if suspicious_dir_list:
                        log_area.append(f'ÔÜá´©Å Encontradas {len(suspicious_dir_list)} pastas suspeitas!')
                        reply = QMessageBox.question(progress_dialog, 'Pastas Suspeitas Encontradas', f'Foram encontradas {len(suspicious_dir_list)} pastas suspeitas que podem\nconter componentes maliciosos (ex: dropper do xHelper).\n\nDeseja remover estas pastas?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if reply == QMessageBox.Yes:
                            log_area.append('­ƒùæ´©Å Removendo pastas suspeitas...')
                            dirs_removed = 0
                            for dir_path in suspicious_dir_list:
                                pass
        except Exception as e:
            log_area.append(f'ÔØî Erro ao verificar/remover arquivos suspeitos: {str(e)}')
            try:
                hidden_apks = self.adb._run_adb_command([self.adb.adb_path, 'shell', "find /sdcard -name '*.apk' -o -name '*.dex' 2>/dev/null"])
                suspicious_apks = []
                if hidden_apks:
                    for apk in hidden_apks.strip().split('\n'):
                        if not apk:
                            continue
                        if len(apk) > 5:
                            suspicious_apks.append(apk)
                if suspicious_apks:
                    log_area.append(f'ÔÜá´©Å Encontrados {len(suspicious_apks)} arquivos APK/DEX suspeitos!')
                    QApplication.processEvents()
                    reply = QMessageBox.question(progress_dialog, 'Arquivos Suspeitos Encontrados', f'Foram encontrados {len(suspicious_apks)} arquivos APK/DEX no armazenamento que\npodem ser usados para reinstalar malware automaticamente.\n\nDeseja remover esses arquivos?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        log_area.append('­ƒùæ´©Å Removendo arquivos APK/DEX suspeitos...')
                        apk_removed = 0
                        for apk in suspicious_apks:
                            pass
                        log_area.append(f'Ô£à {apk_removed} de {len(suspicious_apks)} arquivos suspeitos removidos')
                    else:
                        log_area.append('ÔÜá´©Å Remo├º├úo de arquivos suspeitos cancelada pelo usu├írio')
                else:
                    log_area.append('Ô£à N├úo foram encontrados arquivos APK/DEX suspeitos')
                log_area.append('\n­ƒöì Verificando pastas suspeitas conhecidas...')
                suspicious_dirs = self.adb._run_adb_command([self.adb.adb_path, 'shell', "find /sdcard -type d -name 'com.mufc.*' -o -name '*dropper*' 2>/dev/null"])
                if suspicious_dirs and len(suspicious_dirs.strip()) > 5:
                    suspicious_dir_list = []
                    for dir_path in suspicious_dirs.strip().split('\n'):
                        if not dir_path:
                            continue
                        if len(dir_path) > 5:
                            suspicious_dir_list.append(dir_path)
                    if suspicious_dir_list:
                        log_area.append(f'ÔÜá´©Å Encontradas {len(suspicious_dir_list)} pastas suspeitas!')
                        reply = QMessageBox.question(progress_dialog, 'Pastas Suspeitas Encontradas', f'Foram encontradas {len(suspicious_dir_list)} pastas suspeitas que podem\nconter componentes maliciosos (ex: dropper do xHelper).\n\nDeseja remover estas pastas?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if reply == QMessageBox.Yes:
                            log_area.append('­ƒùæ´©Å Removendo pastas suspeitas...')
                            dirs_removed = 0
                            for dir_path in suspicious_dir_list:
                                try:
                                    try:
                                        self.adb._run_adb_command([self.adb.adb_path, 'shell', f"rm -rf '{dir_path}'"])
                                        dirs_removed += 1
                                        log_area.append(f'   Ô£à Removida pasta: {dir_path}')
                                    except Exception as e:
                                        log_area.append(f'   ÔØî Erro ao remover {dir_path}: {str(e)}')
                                        continue
                                except Exception as e:
                                    log_area.append(f'ÔØî Erro ao verificar/remover arquivos suspeitos: {str(e)}')
                                finally:
                                    if progress_dialog.isVisible():
                                        QTimer.singleShot(3000, progress_dialog.close)
                            log_area.append(f'Ô£à {dirs_removed} de {len(suspicious_dir_list)} pastas suspeitas removidas')
                        else:
                            log_area.append('ÔÜá´©Å Remo├º├úo de pastas suspeitas cancelada pelo usu├írio')
                else:
                    log_area.append('Ô£à N├úo foram encontradas pastas suspeitas conhecidas')
            except Exception as e:
                log_area.append(f'ÔØî Erro ao verificar/remover arquivos suspeitos: {str(e)}')
            finally:
                if progress_dialog.isVisible():
                    QTimer.singleShot(3000, progress_dialog.close)
        log_area.append(f'\nÔ£à Opera├º├úo conclu├¡da! ({success_count} sucessos, {error_count} falhas)')
        QApplication.processEvents()
        status_label.setText('Opera├º├úo conclu├¡da!')
        count_label.setText(f'Resultado: {success_count} sucesso(s), {error_count} falha(s)')
        QApplication.processEvents()
        QTimer.singleShot(2000, progress_dialog.close)
        if progress_dialog.isVisible():
            QTimer.singleShot(3000, progress_dialog.close)
        self.log_area.append('\nÔ£à Opera├º├úo de remo├º├úo conclu├¡da!')
        self.log_area.append(f'­ƒôè Resultado: {success_count} aplicativo(s) removido(s) com sucesso')
        if error_count > 0:
            self.log_area.append(f'ÔÜá´©Å {error_count} aplicativo(s) n├úo p├┤de(puderam) ser removido(s)')
        self.log_area.append('')
        self.log_area.append('======================================================================')
        self.log_area.append('ÔÜá´©Å  PR├ôXIMO PASSO IMPORTANTE:')
        self.log_area.append('­ƒîÉ LIMPE o cache e dados dos navegadores do dispositivo!')
        self.log_area.append('­ƒô▒ Configura├º├Áes > Apps > Chrome/Firefox/etc > Limpar Cache e Dados')
        self.log_area.append('­ƒöÆ Isso elimina rastros maliciosos e protege sua navega├º├úo.')
        self.log_area.append('======================================================================')
        if success_count > 0:
            QMessageBox.information(self, 'Opera├º├úo Conclu├¡da', f'{success_count} aplicativo(s) removido(s) ou desabilitado(s) com sucesso!\n\n{error_count} aplicativo(s) n├úo p├┤de(puderam) ser removido(s).\n\nÔÜá´©Å IMPORTANTE: Limpe o cache e dados dos navegadores!\nRecomendamos tamb├®m bloquear fontes desconhecidas para evitar reinstala├º├úo.')
    def check_miui_ads(self):
        try:
            miui_version = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop ro.miui.ui.version.name']).strip()
            msa_enable = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'settings get global msa_enable']).strip()
            personalized_ad = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'settings get global personalized_ad_enabled']).strip()
            analytics_enabled = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'settings get global analytics_enabled']).strip()
            ad_enable_gdpr = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'settings get global ad_enable_gdpr']).strip()
            is_ads_enabled = msa_enable not in ('null', '0') or personalized_ad not in ('null', '0') or analytics_enabled not in ('null', '0') or ad_enable_gdpr not in ('null', '0')
            if is_ads_enabled:
                self.logger.info(f'Detectados an├║ncios MIUI: MSA={msa_enable}, Pers={personalized_ad}, Analytics={analytics_enabled}')
                return f'An├║ncios MIUI/HyperOS {miui_version} ativos - Recomendamos desativar nas configura├º├Áes'
        except Exception as e:
            self.logger.error(f'Erro ao verificar an├║ncios MIUI: {str(e)}')
    def detect_real_time_ads(self):
        if not self.adb.is_device_connected():
            self.log_area.append('ÔØî Nenhum dispositivo conectado. Por favor, conecte um dispositivo Android.')
            QMessageBox.warning(self, 'Dispositivo n├úo encontrado', 'Nenhum dispositivo Android conectado!\n\nPor favor, conecte um dispositivo via USB e ative a Depura├º├úo USB.')
            return
        dialog = QDialog(self)
        dialog.setWindowTitle('Monitoramento em Tempo Real')
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet('\n            QDialog {\n                background-color: #f5f5f5;\n            }\n            QLabel {\n                font-size: 13px;\n                margin-bottom: 5px;\n            }\n            QLabel#title {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 10px;\n            }\n            QPushButton {\n                padding: 8px 16px;\n                background-color: #2c3e50;\n                color: white;\n                border: none;\n                border-radius: 4px;\n                font-weight: bold;\n                min-height: 30px;\n            }\n            QPushButton:hover {\n                background-color: #34495e;\n            }\n            QPushButton#advanced {\n                background-color: #8e44ad;\n            }\n            QPushButton#advanced:hover {\n                background-color: #9b59b6;\n            }\n        ')
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        title = QLabel('Monitoramento de An├║ncios em Tempo Real')
        title.setObjectName('title')
        layout.addWidget(title)
        description = QLabel('Esta ferramenta ir├í monitorar seu dispositivo em tempo real por alguns minutos, detectando tentativas de exibi├º├úo de an├║ncios, aberturas de navegador e picos de CPU.')
        description.setWordWrap(True)
        layout.addWidget(description)
        mode_layout = QHBoxLayout()
        mode_label = QLabel('Modo de monitoramento:')
        mode_layout.addWidget(mode_label)
        basic_btn = QPushButton('B├ísico')
        basic_btn.clicked.connect((lambda: (dialog.accept(), self.execute_command(self.detect_real_time_ads_impl))))
        mode_layout.addWidget(basic_btn)
        advanced_btn = QPushButton('Avan├ºado')
        advanced_btn.setObjectName('advanced')
        advanced_btn.clicked.connect((lambda: (dialog.accept(), self.run_advanced_realtime_monitoring(duration_spin.value()))))
        mode_layout.addWidget(advanced_btn)
        layout.addLayout(mode_layout)
        duration_layout = QHBoxLayout()
        duration_label = QLabel('Dura├º├úo do monitoramento (segundos):')
        duration_layout.addWidget(duration_label)
        duration_spin = QSpinBox()
        duration_spin.setMinimum(30)
        duration_spin.setMaximum(300)
        duration_spin.setValue(60)
        duration_layout.addWidget(duration_spin)
        layout.addLayout(duration_layout)
        buttons_layout = QHBoxLayout()
        cancel_btn = QPushButton('Cancelar')
        cancel_btn.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_btn)
        start_advanced_btn = QPushButton('Iniciar Monitoramento Avan├ºado')
        start_advanced_btn.setObjectName('advanced')
        start_advanced_btn.clicked.connect((lambda: (dialog.accept(), self.run_advanced_realtime_monitoring(duration_spin.value()))))
        buttons_layout.addWidget(start_advanced_btn)
        layout.addLayout(buttons_layout)
        dialog.exec_()
    def detect_real_time_ads_impl(self):
        try:
            output = '\n============================================================\n'
            output += 'DETECCAO DE ANUNCIOS EM TEMPO REAL\n'
            output += '============================================================\n\n'
            output += 'Buscando aplicativos que podem estar mostrando anuncios em tempo real...\n'
            overlay_apps = self.adb._run_adb_command([self.adb.adb_path, 'shell', "dumpsys window windows | grep -i 'SYSTEM_ALERT_WINDOW'"])
            overlay_packages = []
            for line in overlay_apps.split('\n'):
                if 'package=' in line:
                    package_start = line.find('package=') + 8
                    package_end = line.find(' ', package_start)
                    if package_end == -1:
                        package_end = len(line)
                    package_name = line[package_start:package_end]
                    if not package_name:
                        continue
                    if package_name not in overlay_packages:
                        overlay_packages.append(package_name)
            output += f'ÔÇó Encontrados {len(overlay_packages)} aplicativos com permiss├úo de overlay\n'
            user_apps_output = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'pm list packages -3'])
            user_apps = []
            if user_apps_output:
                for line in user_apps_output.split('\n'):
                    if line.startswith('package:'):
                        app_name = line[8:].strip()
                        if not app_name:
                            continue
                        if app_name not in user_apps:
                            user_apps.append(app_name)
            output += f'ÔÇó Encontrados {len(user_apps)} aplicativos instalados pelo usu├írio\n'
            device_admins_output = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys device_policy'])
            admin_apps = []
            if device_admins_output:
                for line in device_admins_output.split('\n'):
                    if 'admin=' in line:
                        admin_start = line.find('admin=') + 6
                        admin_end = line.find(' ', admin_start)
                        if admin_end == -1:
                            admin_end = len(line)
                        admin_name = line[admin_start:admin_end].strip('{}')
                        if not admin_name:
                            continue
                        if admin_name not in admin_apps:
                            admin_apps.append(admin_name)
            output += f'ÔÇó Encontrados {len(admin_apps)} aplicativos com privil├®gios de administrador\n'
            accessibility_output = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'settings get secure enabled_accessibility_services'])
            accessibility_apps = []
            if accessibility_output and accessibility_output.strip() != 'null':
                for service in accessibility_output.strip().split(':'):
                    if '/' in service:
                        app_name = service.split('/')[0]
                        if not app_name:
                            continue
                        if app_name not in accessibility_apps:
                            accessibility_apps.append(app_name)
            output += f'ÔÇó Encontrados {len(accessibility_apps)} aplicativos com permiss├Áes de acessibilidade\n'
            try:
                boot_apps_output = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys package | grep -i BOOT_COMPLETED | grep -i receive'])
                boot_apps = []
                for line in boot_apps_output.split('\n'):
                    if '/' in line:
                        parts = line.strip().split()
                        for part in parts:
                            if '/' in part:
                                app_name = part.split('/')[0]
                                if not app_name.startswith('com.'):
                                    continue
                                if app_name not in boot_apps:
                                    boot_apps.append(app_name)
                output += f'ÔÇó Encontrados {len(boot_apps)} apps que iniciam no boot\n'
            except Exception:
                boot_apps = []
                output += 'ÔÇó Nao foi possivel verificar apps de boot\n'
            try:
                hidden_apks = self.adb._run_adb_command([self.adb.adb_path, 'shell', "find /sdcard -name '*.apk' -o -name '*.dex' 2>/dev/null"])
                suspicious_apks = []
                if hidden_apks:
                    for apk in hidden_apks.strip().split('\n'):
                        if not apk:
                            continue
                        if len(apk) > 5:
                            suspicious_apks.append(apk)
                if suspicious_apks:
                    output += f'ÔÇó ÔÜá´©Å ATEN├ç├âO! Encontrados {len(suspicious_apks)} arquivos APK/DEX no armazenamento!\n'
                    output += '  Estes arquivos podem ser usados para reinstalar malware ap├│s a limpeza.\n'
                    suspicious_dirs_check = self.adb._run_adb_command([self.adb.adb_path, 'shell', "find /sdcard -type d -name 'com.mufc.*' -o -name '*dropper*' 2>/dev/null"])
                    if suspicious_dirs_check and len(suspicious_dirs_check.strip()) > 5:
                        output += 'ÔÇó ÔÜá´©Å ALERTA! Encontradas pastas possivelmente associadas com malware persistente!\n'
                        output += '  Detectadas pastas suspeitas que podem ser usadas para reinstala├º├úo persistente de malware.\n'
            except Exception as e:
                output += f'ÔÇó N├úo foi poss├¡vel verificar arquivos APK suspeitos: {str(e)}\n'
            else:
                self.log_area.append(output)
                QApplication.processEvents()
                self.show_real_time_ads_dialog(overlay_packages, user_apps, admin_apps, boot_apps, accessibility_apps)
        except Exception as e:
            logger.error(f'Erro ao verificar aplicativos maliciosos: {str(e)}')
            logger.error(traceback.format_exc())
            error_msg = 'Erro ao verificar aplicativos. Verifique a conexao.'
            QApplication.processEvents()
            QMessageBox.critical(self, 'Erro', error_msg)
            return error_msg
        return output
    def show_real_time_ads_dialog(self, overlay_apps, user_apps, admin_apps, boot_apps, accessibility_apps):
        dialog = QDialog(self)
        dialog.setWindowTitle('Monitor de An├║ncios em Tempo Real')
        dialog.setWindowState(Qt.WindowMaximized)
        dialog.setMinimumSize(800, 600)
        dialog.resize(1200, 900)
        dialog.setStyleSheet("\n            QDialog {\n                background-color: #f5f5f5;\n            }\n            QLabel {\n                font-size: 13px;\n                color: #333333;\n            }\n            QLabel#title {\n                font-size: 16px;\n                font-weight: bold;\n                color: #d32f2f;\n                margin-bottom: 15px;\n            }\n            QLabel#instructions {\n                color: #1976D2;\n                font-weight: bold;\n            }\n            QPushButton {\n                padding: 10px 16px;\n                background-color: #2196F3;\n                color: white;\n                border: none;\n                border-radius: 6px;\n                font-weight: bold;\n                min-height: 38px;\n                min-width: 150px;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n            QPushButton:pressed {\n                background-color: #1565C0;\n            }\n            QTextEdit {\n                border: 1px solid #ccc;\n                border-radius: 6px;\n                background-color: white;\n                font-family: 'Consolas', 'Courier New', monospace;\n            }\n            QListWidget {\n                border: 1px solid #ccc;\n                border-radius: 6px;\n                background-color: white;\n                font-family: 'Segoe UI', Arial, sans-serif;\n                font-size: 13px;\n                padding: 5px;\n            }\n            QListWidget::item {\n                padding: 8px;\n                border-bottom: 1px solid #eee;\n                min-height: 30px;\n            }\n            QListWidget::item:hover {\n                background-color: #e3f2fd;\n            }\n            QListWidget::item:selected {\n                background-color: #bbdefb;\n                color: black;\n            }\n            QCheckBox {\n                font-size: 13px;\n                padding: 8px;\n                spacing: 8px;\n            }\n            QScrollArea {\n                border: none;\n                background-color: transparent;\n            }\n            QScrollBar:vertical {\n                background-color: #f0f0f0;\n                width: 12px;\n                border-radius: 6px;\n                margin: 0px;\n            }\n            QScrollBar::handle:vertical {\n                background-color: #c0c0c0;\n                border-radius: 6px;\n                min-height: 20px;\n            }\n            QScrollBar::handle:vertical:hover {\n                background-color: #a0a0a0;\n            }\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                border: none;\n                background: none;\n            }\n        ")
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle('Monitorando An├║ncios')
        progress_dialog.setWindowState(Qt.WindowMaximized)
        progress_dialog.setMinimumSize(800, 600)
        progress_dialog.resize(1200, 900)
        main_scroll = QScrollArea(progress_dialog)
        main_scroll.setWidgetResizable(True)
        main_scroll.setFrameShape(QScrollArea.NoFrame)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_widget = QWidget()
        main_scroll.setWidget(main_widget)
        dialog_layout = QVBoxLayout(progress_dialog)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(main_scroll)
        progress_layout = QVBoxLayout(main_widget)
        progress_layout.setContentsMargins(20, 20, 20, 20)
        progress_layout.setSpacing(15)
        title_label = QLabel('Detectando an├║ncios em tempo real')
        title_label.setObjectName('title')
        progress_layout.addWidget(title_label)
        status_label = QLabel('Monitorando aplicativos que exibem an├║ncios...')
        progress_layout.addWidget(status_label)
        log_area = QTextEdit()
        log_area.setReadOnly(True)
        log_area.setMinimumHeight(200)
        log_area.append('ÔÅ│ Iniciando monitoramento de an├║ncios...\n')
        progress_layout.addWidget(log_area)
        apps_count = len(overlay_apps) + len(user_apps)
        count_label = QLabel(f'Analisando {apps_count} aplicativos...')
        progress_layout.addWidget(count_label)
        progress_dialog.setModal(True)
        progress_dialog.show()
        QApplication.processEvents()
        potential_adware = []
        success_count = 0
        error_count = 0
        try:
            log_area.append('­ƒöì Iniciando detec├º├úo de an├║ncios em tempo real...')
            QApplication.processEvents()
            potential_adware = []
            if overlay_apps:
                log_area.append('\n[*] Verificando apps com permissao de overlay...')
            try:
                _ov_protegidos = obter_pacotes_protegidos(self.adb)
            except Exception:
                _ov_protegidos = set()
            else:
                for app in overlay_apps:
                    potential_adware.append((app, 'overlay'))
                    if is_pacote_protegido(app, _ov_protegidos):
                        log_area.append(f'   [?] {app} - Avalie se e necessario')
                    else:
                        log_area.append(f'   [!] {app} - Permissao de overlay (alta prioridade)')
                known_adware_patterns = ['com.infisecurity.cleaner', 'com.mathgenius.quickresolver', 'com.quickmathto.resolver', 'ads', 'ad.', 'advert', 'notification', 'notify', 'sponsor', 'analytics', 'tracker', 'cleaner', 'booster', 'speedup']
                log_area.append('\n­ƒöì Verificando apps instalados pelo usu├írio...')
                for app in user_apps:
                    app_lower = app.lower()
                    if any((pattern in app_lower for pattern in known_adware_patterns)):
                        potential_adware.append((app, 'adware'))
                        log_area.append(f'   ÔÜá´©Å {app} - Padr├úo de adware conhecido')
                    elif any((pattern in app_lower for pattern in self.json_blacklist)):
                        potential_adware.append((app, 'json_blacklist'))
                        log_area.append(f'   ­ƒôï {app} - Identificado na base de ameacas')
                log_area.append('\n­ƒôè Resultados da detec├º├úo em tempo real:')
                if potential_adware:
                    success_count = len(potential_adware)
                    log_area.append(f'Ô£à Detec├º├úo conclu├¡da! Encontrados {success_count} aplicativos suspeitos.')
                    log_area.append('\n­ƒôï Recomenda├º├Áes:')
                    log_area.append('   1. Use a detec├º├úo de adware para remover apps maliciosos')
                    log_area.append('   2. Desative an├║ncios do sistema MIUI se aplic├ível')
                    log_area.append('   3. Verifique as configura├º├Áes de cada app para desativar an├║ncios')
                    log_area.append('\n­ƒøæ Aplicativos que podem estar exibindo an├║ncios:')
                    for app, reason in potential_adware:
                        if reason == 'overlay':
                            icon = '­ƒö┤'
                        elif reason == 'json_blacklist':
                            icon = '­ƒôï'
                        else:
                            icon = 'ÔÜá´©Å'
                        log_area.append(f'   {icon} {app}')
                else:
                    success_count = 0
                    error_count = 0
                    log_area.append('Ô£à Nenhum aplicativo suspeito de mostrar an├║ncios foi encontrado.')
                    log_area.append('Ôä╣´©Å Se continuar vendo an├║ncios, pode ser devido a:')
                    log_area.append('   1. An├║ncios nativos do sistema MIUI/HyperOS')
                    log_area.append('   2. Apps pr├®-instalados com an├║ncios')
                    log_area.append('   3. Um novo tipo de adware n├úo detectado')
        except Exception as e:
            logger.error(f'Erro ao monitorar an├║ncios: {str(e)}')
            logger.error(traceback.format_exc())
            self.logger.error('Erro ao monitorar anuncios: %s', e)
            QMessageBox.critical(self, 'Erro', 'Erro ao monitorar anuncios. Verifique a conexao com o dispositivo.')
        try:
            brand = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop ro.product.brand']).strip().lower()
            if 'xiaomi' in brand or 'redmi' in brand or 'poco' in brand:
                miui_ads_status = self.check_miui_ads()
                if miui_ads_status:
                    log_area.append(f'\n­ƒô▒ {miui_ads_status}')
                    log_area.append("   Utilize o bot├úo 'Desativar An├║ncios MIUI/HyperOS' para remover an├║ncios do sistema.")
        except Exception as e:
            log_area.append(f'ÔÜá´©Å Erro ao verificar an├║ncios MIUI: {str(e)}')
        status_label.setText('Detec├º├úo conclu├¡da!')
        count_label.setText(f'Encontrados {success_count} app(s) suspeito(s) de exibir an├║ncios')
        QApplication.processEvents()
        buttons_layout = QHBoxLayout()
        if potential_adware:
            selection_dialog = QDialog(self)
            selection_dialog.setWindowTitle('Remover ou Desativar Aplicativos')
            selection_dialog.setMinimumWidth(950)
            selection_dialog.setMinimumHeight(750)
            selection_dialog.resize(1000, 800)
            selection_dialog.setStyleSheet(progress_dialog.styleSheet())
            selection_layout = QVBoxLayout(selection_dialog)
            selection_layout.setContentsMargins(25, 25, 25, 25)
            selection_layout.setSpacing(15)
            selection_title = QLabel('Selecione os aplicativos para remover ou desativar')
            selection_title.setObjectName('title')
            selection_layout.addWidget(selection_title)
            instructions = QLabel('Marque os aplicativos que deseja incluir na opera├º├úo:')
            instructions.setObjectName('instructions')
            selection_layout.addWidget(instructions)
            list_widget = QListWidget()
            list_widget.setMinimumHeight(450)
            try:
                try:
                    _ui_prot = obter_pacotes_protegidos(self.adb)
                except Exception:
                    _ui_prot = set()
            except Exception as e:
                logger.error(f'Erro ao monitorar an├║ncios: {str(e)}')
                logger.error(traceback.format_exc())
                self.logger.error('Erro ao monitorar anuncios: %s', e)
                QMessageBox.critical(self, 'Erro', 'Erro ao monitorar anuncios. Verifique a conexao com o dispositivo.')
            finally:
                if progress_dialog.isVisible():
                    progress_dialog.close()
            for app, reason in potential_adware:
                item = QListWidgetItem()
                item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                item.setCheckState(Qt.Unchecked)
                if is_pacote_protegido(app, _ui_prot):
                    item.setText(f'[?] {app}')
                    item.setForeground(QColor('#b0bec5'))
                    item.setToolTip('Este app pode ser do sistema. Avalie antes de remover.')
                else:
                    icon = '[!]' if reason == 'overlay' else '[?]'
                    item.setText(f'{icon} {app}')
                item.setData(Qt.UserRole, app)
                list_widget.addItem(item)
                continue
            selection_layout.addWidget(list_widget)
            selected_count_label = QLabel(f'Selecionados: {len(potential_adware)} de {len(potential_adware)}')
            selected_count_label.setStyleSheet('font-weight: bold; color: #1976D2;')
            selection_layout.addWidget(selected_count_label)
            def update_selected_count():
                count = 0
                for i in range(list_widget.count()):
                    if list_widget.item(i).checkState() == Qt.Checked:
                        count += 1
                selected_count_label.setText(f'Selecionados: {count} de {list_widget.count()}')
            list_widget.itemChanged.connect(update_selected_count)
            select_all_cb = QCheckBox('Selecionar todos')
            select_all_cb.setChecked(True)
            select_all_cb.setStyleSheet('font-size: 13px; font-weight: bold;')
            def toggle_all():
                state = Qt.Checked if select_all_cb.isChecked() else Qt.Unchecked
                for i in range(list_widget.count()):
                    list_widget.item(i).setCheckState(state)
            select_all_cb.stateChanged.connect(toggle_all)
            selection_layout.addWidget(select_all_cb)
            buttons_layout = QHBoxLayout()
            buttons_layout.setSpacing(15)
            def get_selected_apps():
                selected_apps = []
                for i in range(list_widget.count()):
                    item = list_widget.item(i)
                    if item.checkState() == Qt.Checked:
                        selected_apps.append(item.data(Qt.UserRole))
                return selected_apps
            remove_btn = QPushButton('Remover Selecionados')
            remove_btn.setStyleSheet('\n                    QPushButton {\n                        background-color: #d32f2f;\n                        color: white;\n                        padding: 10px 16px;\n                        font-weight: bold;\n                        min-width: 180px;\n                        min-height: 40px;\n                        border-radius: 6px;\n                    }\n                    QPushButton:hover {\n                        background-color: #b71c1c;\n                    }\n                ')
            def remove_selected():
                apps_to_remove = get_selected_apps()
                if not apps_to_remove:
                    QMessageBox.warning(selection_dialog, 'Aviso', 'Nenhum aplicativo selecionado!')
                    return
                app_list_str = '\n'.join([f'- {app}' for app in apps_to_remove])
                confirm = QMessageBox.question(selection_dialog, 'Confirmar Remo├º├úo', f'Os seguintes aplicativos ser├úo removidos:\n\n{app_list_str}\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if confirm == QMessageBox.Yes:
                    selection_dialog.accept()
                    progress_dialog.accept()
                    self.remove_selected_apps(apps_to_remove)
            remove_btn.clicked.connect(remove_selected)
            buttons_layout.addWidget(remove_btn)
            disable_btn = QPushButton('Desativar Selecionados')
            disable_btn.setStyleSheet('\n                    QPushButton {\n                        background-color: #ff9800;\n                        color: white;\n                        padding: 10px 16px;\n                        font-weight: bold;\n                        min-width: 180px;\n                        min-height: 40px;\n                        border-radius: 6px;\n                    }\n                    QPushButton:hover {\n                        background-color: #f57c00;\n                    }\n                ')
            def disable_selected():
                apps_to_disable = get_selected_apps()
                if not apps_to_disable:
                    QMessageBox.warning(selection_dialog, 'Aviso', 'Nenhum aplicativo selecionado!')
                    return
                selection_dialog.accept()
                progress_dialog.accept()
                disable_dialog = QDialog(self)
                disable_dialog.setWindowTitle('Desativando Aplicativos')
                disable_dialog.setMinimumWidth(950)
                disable_dialog.setMinimumHeight(750)
                disable_dialog.resize(1000, 800)
                disable_layout = QVBoxLayout(disable_dialog)
                disable_layout.setContentsMargins(20, 20, 20, 20)
                disable_layout.setSpacing(15)
                disable_label = QLabel('Desativando aplicativos suspeitos...')
                disable_label.setStyleSheet('font-size: 14px; font-weight: bold;')
                disable_layout.addWidget(disable_label)
                progress_text = QTextEdit()
                progress_text.setReadOnly(True)
                progress_text.setMinimumHeight(200)
                disable_layout.addWidget(progress_text)
                disable_dialog.show()
                QApplication.processEvents()
                success_count = 0
                for app in apps_to_disable:
                    try:
                        progress_text.append(f'ÔÅ│ Desativando {app}...')
                        QApplication.processEvents()
                        result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'pm', 'uninstall', '-k', '--user', '0', app], timeout=30)
                        if result and 'success' in result.lower():
                            progress_text.append('Ô£à App removido com sucesso!')
                            success_count += 1
                        else:
                            progress_text.append(f'ÔÜá´©Å N├úo foi poss├¡vel remover {app}. Tente novamente.')
                    except Exception as e:
                        self.logger.warning('Falha ao desativar %s: %s', app, e)
                        progress_text.append('ÔØî Ocorreu um erro ao processar este app. Tente novamente.')
                        continue
                progress_text.append('\n=== Opera├º├úo conclu├¡da ===')
                progress_text.append(f'Ô£à {success_count} de {len(apps_to_disable)} aplicativos desativados com sucesso')
                close_disable_btn = QPushButton('Fechar')
                close_disable_btn.setMinimumWidth(120)
                close_disable_btn.clicked.connect(disable_dialog.accept)
                disable_layout.addWidget(close_disable_btn, alignment=Qt.AlignRight)
                self.log_area.append(f'Ô£à {success_count} aplicativos desativados com sucesso')
            disable_btn.clicked.connect(disable_selected)
            buttons_layout.addWidget(disable_btn)
            close_btn = QPushButton('Fechar')
            close_btn.setStyleSheet('\n                    QPushButton {\n                        background-color: #607d8b;\n                        color: white;\n                        padding: 10px 16px;\n                        font-weight: bold;\n                        min-width: 120px;\n                        min-height: 40px;\n                        border-radius: 6px;\n                    }\n                    QPushButton:hover {\n                        background-color: #455a64;\n                    }\n                ')
            close_btn.clicked.connect(selection_dialog.reject)
            buttons_layout.addWidget(close_btn)
            selection_layout.addLayout(buttons_layout)
            progress_dialog.accept()
            selection_dialog.exec_()
        else:
            close_btn = QPushButton('Fechar')
            close_btn.setMinimumWidth(150)
            close_btn.setStyleSheet('\n                    QPushButton {\n                        background-color: #607d8b;\n                        color: white;\n                        padding: 10px 16px;\n                        font-weight: bold;\n                        min-height: 40px;\n                        border-radius: 6px;\n                    }\n                    QPushButton:hover {\n                        background-color: #455a64;\n                    }\n                ')
            close_btn.clicked.connect(progress_dialog.accept)
            buttons_layout.addWidget(close_btn)
            progress_layout.addLayout(buttons_layout)
            progress_dialog.exec_()
        if progress_dialog.isVisible():
            progress_dialog.close()
        self.log_area.append('\nÔ£à Opera├º├úo de detec├º├úo conclu├¡da!')
        if potential_adware:
            self.log_area.append(f'­ƒôè Resultado: {len(potential_adware)} aplicativo(s) identificado(s) mostrando an├║ncios')
            apps_to_remove = [app for app, _ in potential_adware]
            apps_str = '\n'.join([f'- {app}' for app, _ in potential_adware])
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle('Opera├º├úo Conclu├¡da')
            msg_box.setText(f'Foram identificados {len(potential_adware)} aplicativos suspeitos de exibir an├║ncios:')
            msg_box.setDetailedText(apps_str)
            remover_btn = msg_box.addButton('Remover Aplicativos', QMessageBox.ActionRole)
            fechar_btn = msg_box.addButton('Fechar', QMessageBox.RejectRole)
            msg_box.setDefaultButton(remover_btn)
            msg_box.exec_()
            if msg_box.clickedButton() == remover_btn:
                self.remove_selected_apps(apps_to_remove)
                return
            return
        self.log_area.append('­ƒôè Nenhum aplicativo identificado mostrando an├║ncios')
        QMessageBox.information(self, 'Opera├º├úo Conclu├¡da', 'Nenhum aplicativo suspeito de exibir an├║ncios foi identificado.\n\nSe ainda estiver tendo problemas, pode ser devido a an├║ncios nativos do sistema ou apps integrados.')
    def disable_miui_ads(self):
        try:
            if not self.adb.is_device_connected():
                self.log_area.append('[!] Nenhum dispositivo conectado.')
                QMessageBox.warning(self, 'Dispositivo nao encontrado', 'Nenhum dispositivo Android conectado!\n\nPor favor, conecte um dispositivo via USB e ative a Depuracao USB.')
                return
            brand = ''
            manufacturer = ''
            try:
                brand = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop ro.product.brand']).strip().lower()
            except Exception:
                pass
            else:
                try:
                    manufacturer = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop ro.product.manufacturer']).strip().lower()
                except Exception:
                    pass
                xiaomi_tokens = ('xiaomi', 'redmi', 'poco', 'mi')
                is_xiaomi = any((t in manufacturer for t in xiaomi_tokens if t in brand))
                if not is_xiaomi:
                    device_name = (brand or manufacturer or 'desconhecido').capitalize()
                    self.log_area.append(f'[!] Funcao especifica para Xiaomi/Redmi/POCO. Detectado: {device_name}')
                    QMessageBox.information(self, 'Dispositivo nao compativel', f'Esta funcao e especifica para dispositivos Xiaomi, Redmi e POCO.\n\nDispositivo atual: {device_name}')
                    return
                reply = QMessageBox.question(self, 'Desativar Anuncios MIUI/HyperOS', 'Esta operacao vai desativar anuncios nativos do sistema MIUI/HyperOS.\n\nO metodo usado e seguro e reversivel:\n- Configuracoes de anuncios serao desativadas\n- Pacotes de anuncio serao removidos para o usuario atual\n- Reversivel via factory reset ou reinstalacao manual\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
                self.log_area.append('\n=== Desativando anuncios MIUI/HyperOS ===\n')
                settings_cmds = [['settings', 'put', 'global', 'msa_enable', '0'], ['settings', 'put', 'global', 'personalized_ad_enabled', '0'], ['settings', 'put', 'global', 'analytics_enabled', '0'], ['settings', 'put', 'global', 'ad_enable_gdpr', '0']]
                pkg_targets = ['com.miui.systemAdSolution', 'com.miui.analytics', 'com.xiaomi.mipicks']
                success_count = 0
                total_commands = len(settings_cmds) + len(pkg_targets)
                self.log_area.append('Processando configuracoes de anuncios...')
                for cmd in settings_cmds:
                    pass
        except Exception as e:
            self.logger.error('Falha ao desativar anuncios MIUI: %s', e)
            self.log_area.append('[ERRO] Falha na operacao. Verifique a conexao.')
            QMessageBox.critical(self, 'Erro', 'Falha ao desativar anuncios. Verifique a conexao com o dispositivo.')
        self.log_area.append('Removendo pacotes de anuncio (usuario atual)...')
        for pkg in pkg_targets:
            try:
                try:
                    result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'pm', 'uninstall', '-k', '--user', '0', pkg], timeout=30)
                    if result and 'success' in result.lower():
                        success_count += 1
                        self.log_area.append(f'  [OK] {pkg} removido')
                        continue
                except Exception as e:
                    self.logger.warning('Pacote MIUI falhou: %s ÔÇö %s', pkg, e)
                    self.log_area.append(f'  [!] {pkg} falhou')
            except Exception as e:
                self.logger.error('Falha ao desativar anuncios MIUI: %s', e)
                self.log_area.append('[ERRO] Falha na operacao. Verifique a conexao.')
                QMessageBox.critical(self, 'Erro', 'Falha ao desativar anuncios. Verifique a conexao com o dispositivo.')
            try:
                try:
                    try:
                        fb = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'pm', 'disable-user', '--user', '0', pkg], timeout=15)
                        if fb and 'disabled' in fb.lower():
                            success_count += 1
                            self.log_area.append(f'  [OK] {pkg} desabilitado (fallback)')
                            continue
                    except Exception:
                        self.log_area.append(f'  [!] {pkg} nao removido: {(result or '').strip()[:60]}')
                except Exception as e:
                    self.logger.warning('Pacote MIUI falhou: %s ÔÇö %s', pkg, e)
                    self.log_area.append(f'  [!] {pkg} falhou')
            except Exception as e:
                self.logger.error('Falha ao desativar anuncios MIUI: %s', e)
                self.log_area.append('[ERRO] Falha na operacao. Verifique a conexao.')
                QMessageBox.critical(self, 'Erro', 'Falha ao desativar anuncios. Verifique a conexao com o dispositivo.')
            try:
                try:
                    try:
                        self.log_area.append(f'  [!] {pkg} nao removido: {(result or '').strip()[:60]}')
                    except Exception:
                        self.log_area.append(f'  [!] {pkg} nao removido: {(result or '').strip()[:60]}')
                except Exception as e:
                    self.logger.warning('Pacote MIUI falhou: %s ÔÇö %s', pkg, e)
                    self.log_area.append(f'  [!] {pkg} falhou')
            except Exception as e:
                self.logger.error('Falha ao desativar anuncios MIUI: %s', e)
                self.log_area.append('[ERRO] Falha na operacao. Verifique a conexao.')
                QMessageBox.critical(self, 'Erro', 'Falha ao desativar anuncios. Verifique a conexao com o dispositivo.')
            continue
        self.log_area.append(f'\nConcluido: {success_count}/{total_commands} operacoes realizadas.')
        miui_ads_status = self.check_miui_ads()
        if miui_ads_status:
            self.log_area.append('')
            self.log_area.append('[!] Alguns servicos de anuncios ainda podem estar ativos.')
            self.log_area.append('    Verifique: Configuracoes > Anuncios > Desativar')
        else:
            self.log_area.append('[OK] Anuncios MIUI/HyperOS desativados com sucesso.')
        QMessageBox.information(self, 'Operacao Concluida', f'{success_count} de {total_commands} operacoes realizadas.\n\nPara garantir remocao completa, verifique:\nConfiguracoes > Anuncios > Desativar')
    def run_advanced_analysis(self):
        try:
            if not self.adb.is_device_connected():
                self.log_area.append('ÔØî Nenhum dispositivo conectado. Por favor, conecte um dispositivo Android.')
                QMessageBox.warning(self, 'Dispositivo n├úo encontrado', 'Nenhum dispositivo Android conectado!\n\nPor favor, conecte um dispositivo via USB e ative a Depura├º├úo USB.')
                return
            self.log_area.append('\n=== Iniciando an├ílise avan├ºada de adware ===\n')
            self.log_area.append('Ô£à Dispositivo conectado. Iniciando an├ílise avan├ºada...')
            self.scan_button.setEnabled(False)
            self.advanced_scan_button.setEnabled(False)
            self.detect_ads_button.setEnabled(False)
            self.disable_miui_ads_button.setEnabled(False)
            self.block_unknown_btn.setEnabled(False)
            detector = AdvancedAdwareDetector(self.adb)
            progress_dialog = QDialog(self)
            progress_dialog.setWindowTitle('An├ílise Avan├ºada')
            progress_dialog.setMinimumWidth(700)
            progress_dialog.setMinimumHeight(450)
            progress_dialog.setStyleSheet("\n                QDialog {\n                    background-color: #f5f5f5;\n                }\n                QLabel {\n                    font-size: 13px;\n                    margin-bottom: 5px;\n                }\n                QLabel#title {\n                    font-size: 16px;\n                    font-weight: bold;\n                    color: #8e44ad;\n                    margin-bottom: 15px;\n                }\n                QTextEdit {\n                    border: 1px solid #ccc;\n                    border-radius: 4px;\n                    background-color: white;\n                    font-family: 'Consolas', 'Courier New', monospace;\n                }\n                QPushButton {\n                    padding: 8px 15px;\n                    background-color: #8e44ad;\n                    color: white;\n                    border: none;\n                    border-radius: 4px;\n                    font-weight: bold;\n                    min-height: 30px;\n                }\n                QPushButton:hover {\n                    background-color: #9b59b6;\n                }\n                QProgressBar {\n                    border: 1px solid #bdc3c7;\n                    border-radius: 3px;\n                    text-align: center;\n                    height: 25px;\n                }\n                QProgressBar::chunk {\n                    background-color: #8e44ad;\n                    width: 10px;\n                    margin: 0.5px;\n                }\n            ")
            progress_layout = QVBoxLayout(progress_dialog)
            progress_layout.setContentsMargins(20, 20, 20, 20)
            progress_layout.setSpacing(15)
            title_label = QLabel('An├ílise Avan├ºada de Adware com Sistema de Pontua├º├úo')
            title_label.setObjectName('title')
            progress_layout.addWidget(title_label)
            status_label = QLabel('Iniciando an├ílise avan├ºada...')
            progress_layout.addWidget(status_label)
            log_area = QTextEdit()
            log_area.setReadOnly(True)
            log_area.setMinimumHeight(250)
            log_area.append('ÔÅ│ Inicializando detector avan├ºado...\n')
            progress_layout.addWidget(log_area)
            progress_dialog.setModal(True)
            progress_dialog.show()
            QApplication.processEvents()
            def update_log(message):
                log_area.append(message)
                status_label.setText(message)
                QApplication.processEvents()
            def run_analysis():
                try:
                    results = detector.analyze_device(callback=update_log)
                    if 'error' in results:
                        update_log(f'ÔØî Erro: {results['error']}')
                        self.scan_button.setEnabled(True)
                        self.advanced_scan_button.setEnabled(True)
                        self.detect_ads_button.setEnabled(True)
                        self.disable_miui_ads_button.setEnabled(True)
                        self.block_unknown_btn.setEnabled(True)
                        return
                    update_log('\nÔ£à An├ílise conclu├¡da com sucesso!\n')
                    progress_dialog.accept()
                    self.show_advanced_results(results)
                except Exception as e:
                    update_log(f'ÔØî Erro na an├ílise: {str(e)}')
                    logger.error(f'Erro na an├ílise avan├ºada: {str(e)}')
                    logger.error(traceback.format_exc())
                finally:
                    self.scan_button.setEnabled(True)
                    self.advanced_scan_button.setEnabled(True)
                    self.detect_ads_button.setEnabled(True)
                    self.disable_miui_ads_button.setEnabled(True)
                    self.block_unknown_btn.setEnabled(True)
            if self._USE_MONITOR_WORKER:
                _pd = progress_dialog
                _log = log_area
                _status = status_label
                def _on_results_advanced(results):
                    try:
                        if results is None:
                            return
                        if isinstance(results, dict) and 'error' in results:
                            try:
                                _log.append(f'ÔØî Erro: {results['error']}')
                                _status.setText('Erro na an├ílise')
                            except Exception:
                                pass
                            return
                    except Exception:
                        logger.error(traceback.format_exc())
                    try:
                        _log.append('\nÔ£à An├ílise conclu├¡da com sucesso!\n')
                        _status.setText('An├ílise conclu├¡da')
                    except Exception:
                        pass
                    try:
                        _pd.accept()
                    except Exception:
                        pass
                    try:
                        self.show_advanced_results(results)
                    except Exception as e:
                        self.log_area.append(f'ÔØî Erro ao exibir resultados: {str(e)}')
                        logger.error(traceback.format_exc())
                def _on_error_advanced(error_msg):
                    try:
                        _log.append(f'ÔØî Erro na an├ílise: {error_msg}')
                        _status.setText('Erro na an├ílise')
                    except Exception:
                        pass
                    logger.error(f'Erro na an├ílise avan├ºada: {error_msg}')
                    try:
                        _pd.reject()
                    except Exception:
                        return
                def _cleanup_advanced():
                    self.scan_button.setEnabled(True)
                    self.advanced_scan_button.setEnabled(True)
                    self.detect_ads_button.setEnabled(True)
                    self.disable_miui_ads_button.setEnabled(True)
                    self.block_unknown_btn.setEnabled(True)
                self._iniciar_monitor_worker(target_callable=(lambda cb: detector.analyze_device(callback=cb)), on_results=_on_results_advanced, on_error=_on_error_advanced, log_target=_log, status_label=_status, cleanup=_cleanup_advanced)
                return
            QTimer.singleShot(100, run_analysis)
            return
        except Exception as e:
            self.log_area.append(f'ÔØî Erro ao iniciar an├ílise avan├ºada: {str(e)}')
            logger.error(f'Erro ao iniciar an├ílise avan├ºada: {str(e)}')
            logger.error(traceback.format_exc())
            self.scan_button.setEnabled(True)
            self.advanced_scan_button.setEnabled(True)
            self.detect_ads_button.setEnabled(True)
            self.disable_miui_ads_button.setEnabled(True)
            self.block_unknown_btn.setEnabled(True)
    def show_advanced_results(self, results):
        dialog = QDialog(self)
        dialog.setWindowTitle('Resultados da An├ílise Avan├ºada')
        dialog.setWindowState(Qt.WindowMaximized)
        dialog.setMinimumSize(800, 600)
        dialog.resize(1200, 900)
        dialog.setStyleSheet("\n            QDialog {\n                background-color: #f5f5f5;\n            }\n            QLabel {\n                font-size: 13px;\n            }\n            QLabel#title {\n                font-size: 16px;\n                font-weight: bold;\n                color: #8e44ad;\n                margin-bottom: 10px;\n            }\n            QLabel#subtitle {\n                font-size: 14px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-top: 10px;\n            }\n            QLabel#high {\n                color: #c0392b;\n                font-weight: bold;\n            }\n            QLabel#medium {\n                color: #d35400;\n                font-weight: bold;\n            }\n            QLabel#low {\n                color: #27ae60;\n                font-weight: bold;\n            }\n            QListWidget {\n                border: 1px solid #bdc3c7;\n                border-radius: 5px;\n            }\n            QListWidget::item {\n                padding: 5px;\n                border-bottom: 1px solid #ecf0f1;\n            }\n            QListWidget::item:selected {\n                background-color: #e8f5e9;\n                color: #2c3e50;\n            }\n            QPushButton {\n                padding: 8px 16px;\n                background-color: #8e44ad;\n                color: white;\n                border: none;\n                border-radius: 4px;\n                font-weight: bold;\n                min-height: 30px;\n                min-width: 100px;\n            }\n            QPushButton:hover {\n                background-color: #9b59b6;\n            }\n            QPushButton#remove {\n                background-color: #c0392b;\n            }\n            QPushButton#remove:hover {\n                background-color: #e74c3c;\n            }\n            QTextEdit {\n                border: 1px solid #bdc3c7;\n                border-radius: 5px;\n                background-color: white;\n                font-family: 'Consolas', 'Courier New', monospace;\n                font-size: 12px;\n            }\n            QScrollArea {\n                border: none;\n                background-color: transparent;\n            }\n            QScrollBar:vertical {\n                background-color: #f0f0f0;\n                width: 12px;\n                border-radius: 6px;\n                margin: 0px;\n            }\n            QScrollBar::handle:vertical {\n                background-color: #c0c0c0;\n                border-radius: 6px;\n                min-height: 20px;\n            }\n            QScrollBar::handle:vertical:hover {\n                background-color: #a0a0a0;\n            }\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                border: none;\n                background: none;\n            }\n        ")
        main_scroll = QScrollArea(dialog)
        main_scroll.setWidgetResizable(True)
        main_scroll.setFrameShape(QScrollArea.NoFrame)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_widget = QWidget()
        main_scroll.setWidget(main_widget)
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(main_scroll)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        title = QLabel('Resultados da An├ílise Avan├ºada de Adware')
        title.setObjectName('title')
        layout.addWidget(title)
        device_info = results.get('device_info', {})
        device_text = f'Dispositivo: {device_info.get('brand', 'Desconhecido')} {device_info.get('model', 'Desconhecido')} (Android {device_info.get('android', 'Desconhecido')})'
        device_label = QLabel(device_text)
        layout.addWidget(device_label)
        summary_frame = QFrame()
        summary_frame.setStyleSheet('\n            QFrame {\n                background-color: #f0f0f0;\n                border-radius: 5px;\n                padding: 10px;\n            }\n        ')
        summary_layout = QHBoxLayout(summary_frame)
        total_box = QFrame()
        total_box.setStyleSheet('background-color: #ecf0f1; border-radius: 5px; padding: 10px;')
        total_layout = QVBoxLayout(total_box)
        total_layout.setSpacing(5)
        total_label = QLabel('Apps Analisados')
        total_label.setAlignment(Qt.AlignCenter)
        total_value = QLabel(str(results.get('total_apps', 0)))
        total_value.setStyleSheet('font-size: 24px; font-weight: bold;')
        total_value.setAlignment(Qt.AlignCenter)
        total_layout.addWidget(total_label)
        total_layout.addWidget(total_value)
        summary_layout.addWidget(total_box)
        suspicious_box = QFrame()
        suspicious_box.setStyleSheet('background-color: #e8f5e9; border-radius: 5px; padding: 10px;')
        suspicious_layout = QVBoxLayout(suspicious_box)
        suspicious_layout.setSpacing(5)
        suspicious_label = QLabel('Apps Suspeitos')
        suspicious_label.setAlignment(Qt.AlignCenter)
        suspicious_value = QLabel(str(results.get('total_suspicious', 0)))
        suspicious_value.setStyleSheet('font-size: 24px; font-weight: bold;')
        suspicious_value.setAlignment(Qt.AlignCenter)
        suspicious_layout.addWidget(suspicious_label)
        suspicious_layout.addWidget(suspicious_value)
        summary_layout.addWidget(suspicious_box)
        high_box = QFrame()
        high_box.setStyleSheet('background-color: #ffebee; border-radius: 5px; padding: 10px;')
        high_layout = QVBoxLayout(high_box)
        high_layout.setSpacing(5)
        high_label = QLabel('Alto Risco')
        high_label.setAlignment(Qt.AlignCenter)
        high_value = QLabel(str(results.get('high_risk', 0)))
        high_value.setStyleSheet('font-size: 24px; font-weight: bold; color: #c0392b;')
        high_value.setAlignment(Qt.AlignCenter)
        high_layout.addWidget(high_label)
        high_layout.addWidget(high_value)
        summary_layout.addWidget(high_box)
        medium_box = QFrame()
        medium_box.setStyleSheet('background-color: #fff8e1; border-radius: 5px; padding: 10px;')
        medium_layout = QVBoxLayout(medium_box)
        medium_layout.setSpacing(5)
        medium_label = QLabel('M├®dio Risco')
        medium_label.setAlignment(Qt.AlignCenter)
        medium_value = QLabel(str(results.get('medium_risk', 0)))
        medium_value.setStyleSheet('font-size: 24px; font-weight: bold; color: #d35400;')
        medium_value.setAlignment(Qt.AlignCenter)
        medium_layout.addWidget(medium_label)
        medium_layout.addWidget(medium_value)
        summary_layout.addWidget(medium_box)
        low_box = QFrame()
        low_box.setStyleSheet('background-color: #e0f2f1; border-radius: 5px; padding: 10px;')
        low_layout = QVBoxLayout(low_box)
        low_layout.setSpacing(5)
        low_label = QLabel('Baixo Risco')
        low_label.setAlignment(Qt.AlignCenter)
        low_value = QLabel(str(results.get('low_risk', 0)))
        low_value.setStyleSheet('font-size: 24px; font-weight: bold; color: #27ae60;')
        low_value.setAlignment(Qt.AlignCenter)
        low_layout.addWidget(low_label)
        low_layout.addWidget(low_value)
        summary_layout.addWidget(low_box)
        layout.addWidget(summary_frame)
        apps_subtitle = QLabel('Lista de Aplicativos Suspeitos')
        apps_subtitle.setObjectName('subtitle')
        layout.addWidget(apps_subtitle)
        content_layout = QHBoxLayout()
        list_widget = QListWidget()
        list_widget.setMinimumWidth(300)
        details_frame = QFrame()
        details_frame.setStyleSheet('\n            QFrame {\n                background-color: white;\n                border: 1px solid #bdc3c7;\n                border-radius: 5px;\n                padding: 10px;\n            }\n            QScrollArea {\n                border: none;\n                background-color: transparent;\n            }\n        ')
        details_layout = QVBoxLayout(details_frame)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        details_container = QWidget()
        details_container_layout = QVBoxLayout(details_container)
        details_container_layout.setContentsMargins(0, 0, 5, 0)
        details_container_layout.setSpacing(10)
        details_title = QLabel('Detalhes do Aplicativo')
        details_title.setObjectName('subtitle')
        details_container_layout.addWidget(details_title)
        app_name_label = QLabel('Selecione um aplicativo para ver detalhes')
        app_name_label.setWordWrap(True)
        details_container_layout.addWidget(app_name_label)
        score_label = QLabel('')
        details_container_layout.addWidget(score_label)
        risk_label = QLabel('')
        details_container_layout.addWidget(risk_label)
        reasons_title = QLabel('Raz├Áes para suspeita:')
        reasons_title.setVisible(False)
        details_container_layout.addWidget(reasons_title)
        reasons_text = QTextEdit()
        reasons_text.setReadOnly(True)
        reasons_text.setMinimumHeight(200)
        reasons_text.setVisible(False)
        details_container_layout.addWidget(reasons_text)
        details_container_layout.addStretch()
        scroll_area.setWidget(details_container)
        details_layout.addWidget(scroll_area)
        content_layout.addWidget(list_widget, 1)
        content_layout.addWidget(details_frame, 2)
        layout.addLayout(content_layout, 1)
        suspicious_apps = results.get('suspicious_apps', {})
        for package, data in suspicious_apps.items():
            score = data.get('score', 0)
            risk_level = data.get('risk_level', 'Baixo')
            app_name = data.get('app_name', package.split('.')[-1].capitalize())
            item = QListWidgetItem()
            if risk_level == 'Alto':
                item.setText(f'­ƒö┤ {app_name}')
            elif risk_level == 'M├®dio':
                item.setText(f'­ƒƒá {app_name}')
            else:
                item.setText(f'­ƒƒí {app_name}')
            item.setData(Qt.UserRole, {'package': package, 'data': data})
            list_widget.addItem(item)
        def show_app_details():
            item = list_widget.currentItem()
            if not item:
                return
            item_data = item.data(Qt.UserRole)
            package = item_data['package']
            data = item_data['data']
            app_name_label.setText(f'App: {data.get('app_name', package)}')
            score_label.setText(f'Pontua├º├úo de Risco: {data.get('score', 0)}/100')
            risk_level = data.get('risk_level', 'Baixo')
            risk_label.setText(f'N├¡vel de Risco: {risk_level}')
            if risk_level == 'Alto':
                risk_label.setObjectName('high')
                risk_label.setStyleSheet('color: #c0392b; font-weight: bold;')
            elif risk_level == 'M├®dio':
                risk_label.setObjectName('medium')
                risk_label.setStyleSheet('color: #d35400; font-weight: bold;')
            else:
                risk_label.setObjectName('low')
                risk_label.setStyleSheet('color: #27ae60; font-weight: bold;')
            reasons_title.setVisible(True)
            reasons_text.setVisible(True)
            reasons = data.get('reasons', [])
            if reasons:
                reasons_text.clear()
                for reason in reasons:
                    reasons_text.append(f'ÔÇó {reason}')
                if 'permissions' in data:
                    reasons_text.append('\n­ƒô▒ Permiss├Áes solicitadas:')
                    for perm in data['permissions']:
                        reasons_text.append(f'  - {perm}')
                if 'flags' in data:
                    reasons_text.append('\n­ƒÜ® Flags de comportamento:')
                    for flag in data['flags']:
                        reasons_text.append(f'  - {flag}')
            else:
                reasons_text.setText('Nenhuma raz├úo espec├¡fica encontrada.')
            scroll_area.verticalScrollBar().setValue(0)
        list_widget.currentItemChanged.connect(show_app_details)
        buttons_layout = QHBoxLayout()
        remove_btn = QPushButton('Remover Selecionados')
        remove_btn.setObjectName('remove')
        def remove_selected_apps():
            selected_items = list_widget.selectedItems()
            if not selected_items:
                QMessageBox.warning(dialog, 'Aviso', 'Nenhum aplicativo selecionado!')
                return
            selected_packages = []
            for item in selected_items:
                item_data = item.data(Qt.UserRole)
                package = item_data['package']
                selected_packages.append(package)
            apps_str = '\n'.join([f'- {app}' for app in selected_packages])
            confirm_msg = f'Tem certeza que deseja desinstalar os seguintes aplicativos?\n\n{apps_str}'
            confirm = QMessageBox.question(dialog, 'Confirmar Remo├º├úo', confirm_msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if confirm == QMessageBox.Yes:
                dialog.accept()
                self.remove_selected_apps(selected_packages)
        remove_btn.clicked.connect(remove_selected_apps)
        buttons_layout.addWidget(remove_btn)
        close_btn = QPushButton('Fechar')
        close_btn.clicked.connect(dialog.accept)
        buttons_layout.addWidget(close_btn)
        layout.addLayout(buttons_layout)
        dialog.exec_()
    def run_advanced_realtime_monitoring(self, duration=60):
        try:
            if not self.adb.is_device_connected():
                self.log_area.append('ÔØî Nenhum dispositivo conectado. Por favor, conecte um dispositivo Android.')
                return
            self.log_area.append('\n=== Iniciando monitoramento avan├ºado em tempo real ===\n')
            self.log_area.append(f'Ô£à Monitorando o dispositivo por {duration} segundos...')
            self.scan_button.setEnabled(False)
            self.advanced_scan_button.setEnabled(False)
            self.detect_ads_button.setEnabled(False)
            self.disable_miui_ads_button.setEnabled(False)
            self.block_unknown_btn.setEnabled(False)
            detector = AdvancedAdwareDetector(self.adb)
            progress_dialog = QDialog(self)
            progress_dialog.setWindowTitle('Monitoramento em Tempo Real')
            progress_dialog.setMinimumWidth(700)
            progress_dialog.setMinimumHeight(450)
            progress_dialog.setStyleSheet("\n                QDialog {\n                    background-color: #f5f5f5;\n                }\n                QLabel {\n                    font-size: 13px;\n                    margin-bottom: 5px;\n                }\n                QLabel#title {\n                    font-size: 16px;\n                    font-weight: bold;\n                    color: #2c3e50;\n                    margin-bottom: 15px;\n                }\n                QTextEdit {\n                    border: 1px solid #ccc;\n                    border-radius: 4px;\n                    background-color: white;\n                    font-family: 'Consolas', 'Courier New', monospace;\n                }\n                QPushButton {\n                    padding: 8px 15px;\n                    background-color: #2c3e50;\n                    color: white;\n                    border: none;\n                    border-radius: 4px;\n                    font-weight: bold;\n                    min-height: 30px;\n                }\n                QPushButton:hover {\n                    background-color: #34495e;\n                }\n            ")
            progress_layout = QVBoxLayout(progress_dialog)
            progress_layout.setContentsMargins(20, 20, 20, 20)
            progress_layout.setSpacing(15)
            title_label = QLabel('Monitoramento Avan├ºado de An├║ncios em Tempo Real')
            title_label.setObjectName('title')
            progress_layout.addWidget(title_label)
            status_label = QLabel(f'Monitorando o dispositivo por {duration} segundos...')
            progress_layout.addWidget(status_label)
            log_area = QTextEdit()
            log_area.setReadOnly(True)
            log_area.setMinimumHeight(250)
            log_area.append('ÔÅ│ Iniciando monitoramento em tempo real...\n')
            progress_layout.addWidget(log_area)
            progress_dialog.setModal(True)
            progress_dialog.show()
            QApplication.processEvents()
            def update_log(message):
                log_area.append(message)
                status_label.setText(message)
                QApplication.processEvents()
            def run_monitoring():
                try:
                    results = detector.scan_realtime(duration=duration, callback=update_log)
                    update_log('\nÔ£à Monitoramento conclu├¡do com sucesso!\n')
                    progress_dialog.accept()
                    self.show_realtime_results(results)
                except Exception as e:
                    update_log(f'ÔØî Erro no monitoramento: {str(e)}')
                    logger.error(f'Erro no monitoramento em tempo real: {str(e)}')
                    logger.error(traceback.format_exc())
                finally:
                    self.scan_button.setEnabled(True)
                    self.advanced_scan_button.setEnabled(True)
                    self.detect_ads_button.setEnabled(True)
                    self.disable_miui_ads_button.setEnabled(True)
                    self.block_unknown_btn.setEnabled(True)
            if self._USE_MONITOR_WORKER:
                _pd = progress_dialog
                _log = log_area
                _status = status_label
                def _on_results_realtime(results):
                    try:
                        if results is None:
                            return
                    except Exception:
                        logger.error(traceback.format_exc())
                    try:
                        _log.append('\nÔ£à Monitoramento conclu├¡do com sucesso!\n')
                        _status.setText('Monitoramento conclu├¡do')
                    except Exception:
                        pass
                    try:
                        _pd.accept()
                    except Exception:
                        pass
                    try:
                        self.show_realtime_results(results)
                    except Exception as e:
                        self.log_area.append(f'ÔØî Erro ao exibir resultados: {str(e)}')
                        logger.error(traceback.format_exc())
                def _on_error_realtime(error_msg):
                    try:
                        _log.append(f'ÔØî Erro no monitoramento: {error_msg}')
                        _status.setText('Erro no monitoramento')
                    except Exception:
                        pass
                    logger.error(f'Erro no monitoramento em tempo real: {error_msg}')
                    try:
                        _pd.reject()
                    except Exception:
                        return
                def _cleanup_realtime():
                    self.scan_button.setEnabled(True)
                    self.advanced_scan_button.setEnabled(True)
                    self.detect_ads_button.setEnabled(True)
                    self.disable_miui_ads_button.setEnabled(True)
                    self.block_unknown_btn.setEnabled(True)
                self._iniciar_monitor_worker(target_callable=(lambda cb: detector.scan_realtime(duration=duration, callback=cb)), on_results=_on_results_realtime, on_error=_on_error_realtime, log_target=_log, status_label=_status, cleanup=_cleanup_realtime)
                return
            QTimer.singleShot(100, run_monitoring)
            return
        except Exception as e:
            self.log_area.append(f'ÔØî Erro ao iniciar monitoramento em tempo real: {str(e)}')
            logger.error(f'Erro ao iniciar monitoramento em tempo real: {str(e)}')
            logger.error(traceback.format_exc())
            self.scan_button.setEnabled(True)
            self.advanced_scan_button.setEnabled(True)
            self.detect_ads_button.setEnabled(True)
            self.disable_miui_ads_button.setEnabled(True)
            self.block_unknown_btn.setEnabled(True)
    def show_realtime_results(self, results):
        dialog = QDialog(self)
        dialog.setWindowTitle('Resultados do Monitoramento em Tempo Real')
        dialog.setWindowState(Qt.WindowMaximized)
        dialog.setMinimumSize(800, 600)
        dialog.resize(1200, 900)
        dialog.setStyleSheet("\n            QDialog {\n                background-color: #f5f5f5;\n            }\n            QLabel {\n                font-size: 13px;\n            }\n            QLabel#title {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 10px;\n            }\n            QLabel#subtitle {\n                font-size: 14px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-top: 10px;\n            }\n            QListWidget {\n                border: 1px solid #bdc3c7;\n                border-radius: 5px;\n            }\n            QListWidget::item {\n                padding: 5px;\n                border-bottom: 1px solid #ecf0f1;\n            }\n            QListWidget::item:selected {\n                background-color: #e8f5e9;\n                color: #2c3e50;\n            }\n            QPushButton {\n                padding: 8px 16px;\n                background-color: #2c3e50;\n                color: white;\n                border: none;\n                border-radius: 4px;\n                font-weight: bold;\n                min-height: 30px;\n                min-width: 100px;\n            }\n            QPushButton:hover {\n                background-color: #34495e;\n            }\n            QPushButton#remove {\n                background-color: #c0392b;\n            }\n            QPushButton#remove:hover {\n                background-color: #e74c3c;\n            }\n            QTextEdit {\n                border: 1px solid #bdc3c7;\n                border-radius: 5px;\n                background-color: white;\n                font-family: 'Consolas', 'Courier New', monospace;\n                font-size: 12px;\n            }\n            QScrollArea {\n                border: none;\n                background-color: transparent;\n            }\n            QScrollBar:vertical {\n                background-color: #f0f0f0;\n                width: 12px;\n                border-radius: 6px;\n                margin: 0px;\n            }\n            QScrollBar::handle:vertical {\n                background-color: #c0c0c0;\n                border-radius: 6px;\n                min-height: 20px;\n            }\n            QScrollBar::handle:vertical:hover {\n                background-color: #a0a0a0;\n            }\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                border: none;\n                background: none;\n            }\n        ")
        main_scroll = QScrollArea(dialog)
        main_scroll.setWidgetResizable(True)
        main_scroll.setFrameShape(QScrollArea.NoFrame)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_widget = QWidget()
        main_scroll.setWidget(main_widget)
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(main_scroll)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        title = QLabel('Resultados do Monitoramento em Tempo Real')
        title.setObjectName('title')
        layout.addWidget(title)
        info_text = f'In├¡cio: {results.get('start_time', 'Desconhecido')} | Dura├º├úo: {results.get('duration', 0)} segundos'
        info_label = QLabel(info_text)
        layout.addWidget(info_label)
        suspicious_activities = results.get('suspicious_activities', [])
        if not suspicious_activities:
            no_results_label = QLabel('Ô£à Nenhuma atividade suspeita detectada durante o monitoramento.')
            no_results_label.setStyleSheet('font-size: 14px; color: #27ae60; font-weight: bold; margin: 20px 0;')
            layout.addWidget(no_results_label)
            active_apps = results.get('active_apps', set())
            if active_apps:
                active_title = QLabel('Apps Ativos Durante o Monitoramento:')
                active_title.setObjectName('subtitle')
                layout.addWidget(active_title)
                active_list = QListWidget()
                for app in active_apps:
                    QListWidgetItem(app, active_list)
                layout.addWidget(active_list)
                buttons_layout = QHBoxLayout()
                remove_apps_btn = QPushButton(f'Remover Apps Ativos ({len(active_apps)})')
                remove_apps_btn.setStyleSheet('\n                    QPushButton {\n                        background-color: #f39c12;\n                        color: white;\n                        padding: 10px 16px;\n                        font-weight: bold;\n                        min-width: 220px;\n                        min-height: 40px;\n                        border-radius: 6px;\n                    }\n                    QPushButton:hover {\n                        background-color: #f1c40f;\n                    }\n                ')
                def remove_active_apps():
                    apps_list = list(active_apps)
                    if not apps_list:
                        QMessageBox.warning(dialog, 'Aviso', 'Nenhum aplicativo ativo para selecionar!')
                        return
                    selection_dialog = QDialog(dialog)
                    selection_dialog.setWindowTitle('Selecionar Apps para Remo├º├úo')
                    selection_dialog.setWindowState(Qt.WindowMaximized)
                    selection_dialog.setMinimumSize(800, 600)
                    selection_dialog.resize(1000, 800)
                    selection_layout = QVBoxLayout(selection_dialog)
                    warning_label = QLabel('[!] Estes apps NAO apresentaram padroes nocivos durante o monitoramento!')
                    warning_label.setStyleSheet('color: #e74c3c; font-weight: bold; margin-bottom: 10px;')
                    selection_layout.addWidget(warning_label)
                    info_label = QLabel('Selecione os aplicativos que deseja remover:')
                    selection_layout.addWidget(info_label)
                    try:
                        _rt_protegidos = obter_pacotes_protegidos(self.adb)
                    except Exception:
                        _rt_protegidos = set()
                    check_list = QListWidget()
                    for app in apps_list:
                        item = QListWidgetItem(app)
                        item.setData(Qt.UserRole, app)
                        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                        item.setCheckState(Qt.Unchecked)
                        if is_pacote_protegido(app, _rt_protegidos):
                            item.setForeground(QColor('#b0bec5'))
                            item.setToolTip('Este app pode ser do sistema. Avalie antes de remover.')
                        check_list.addItem(item)
                    selection_layout.addWidget(check_list)
                    count_label = QLabel('0 apps selecionados')
                    selection_layout.addWidget(count_label)
                    def update_count():
                        selected = 0
                        for i in range(check_list.count()):
                            it = check_list.item(i)
                            if not it.flags() & Qt.ItemIsUserCheckable:
                                continue
                            if it.checkState() == Qt.Checked:
                                selected += 1
                        count_label.setText(f'{selected} apps selecionados')
                    check_list.itemChanged.connect(update_count)
                    buttons_layout = QHBoxLayout()
                    toggle_btn = QPushButton('Selecionar Todos')
                    toggle_state = False
                    def toggle_all():
                        nonlocal toggle_state
                        toggle_state = not toggle_state
                        state = Qt.Checked if toggle_state else Qt.Unchecked
                        for i in range(check_list.count()):
                            it = check_list.item(i)
                            if it.flags() & Qt.ItemIsUserCheckable:
                                it.setCheckState(state)
                        if toggle_state:
                            toggle_btn.setText('Desselecionar Todos')
                            return
                        None('Selecionar Todos')
                    toggle_btn.clicked.connect(toggle_all)
                    buttons_layout.addWidget(toggle_btn)
                    remove_btn = QPushButton('Remover Selecionados')
                    def do_remove_selected():
                        selected_apps = []
                        for i in range(check_list.count()):
                            item = check_list.item(i)
                            if item.checkState() != Qt.Checked:
                                continue
                            selected_apps.append(item.data(Qt.UserRole) or item.text())
                        if not selected_apps:
                            QMessageBox.warning(selection_dialog, 'Aviso', 'Nenhum aplicativo selecionado!')
                            return
                        apps_str = '\n'.join([f'- {app}' for app in selected_apps])
                        confirm = QMessageBox.question(selection_dialog, 'Confirmar Remocao', f'Deseja desinstalar os seguintes aplicativos?\n\n{apps_str}', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if confirm == QMessageBox.Yes:
                            selection_dialog.accept()
                            dialog.accept()
                            self.remove_selected_apps(selected_apps)
                    remove_btn.clicked.connect(do_remove_selected)
                    buttons_layout.addWidget(remove_btn)
                    cancel_btn = QPushButton('Cancelar')
                    cancel_btn.clicked.connect(selection_dialog.reject)
                    buttons_layout.addWidget(cancel_btn)
                    selection_layout.addLayout(buttons_layout)
                    selection_dialog.exec_()
                remove_apps_btn.clicked.connect(remove_active_apps)
                buttons_layout.addWidget(remove_apps_btn)
                close_btn = QPushButton('Fechar')
                close_btn.clicked.connect(dialog.accept)
                buttons_layout.addWidget(close_btn)
                layout.addLayout(buttons_layout)
                info_label = QLabel('Ôä╣´©Å Embora nenhuma atividade suspeita tenha sido detectada, voc├¬ ainda pode remover os aplicativos ativos se desejar.')
                info_label.setStyleSheet('font-style: italic; color: #7f8c8d; margin-top: 10px;')
                info_label.setWordWrap(True)
                layout.addWidget(info_label)
            else:
                buttons_layout = QHBoxLayout()
                close_btn = QPushButton('Fechar')
                close_btn.clicked.connect(dialog.accept)
                buttons_layout.addWidget(close_btn)
                layout.addLayout(buttons_layout)
        else:
            suspicious_title = QLabel(f'ÔÜá´©Å Foram detectadas {len(suspicious_activities)} atividades suspeitas:')
            suspicious_title.setStyleSheet('font-size: 14px; color: #c0392b; font-weight: bold; margin: 10px 0;')
            layout.addWidget(suspicious_title)
            activities_list = QListWidget()
            for activity in suspicious_activities:
                app = activity.get('app', 'Desconhecido')
                timestamp = activity.get('timestamp', '')
                activity_desc = activity.get('activity', 'Atividade suspeita')
                item = QListWidgetItem(f'[{timestamp}] {app}: {activity_desc}')
                activity_type = activity.get('type', '')
                if 'url' in activity_type:
                    item.setText(f'­ƒîÉ {item.text()}')
                elif 'playstore' in activity_type:
                    item.setText(f'­ƒô▒ {item.text()}')
                elif 'cpu' in activity_type:
                    item.setText(f'ÔÜí {item.text()}')
                activities_list.addItem(item)
            layout.addWidget(activities_list, 1)
            details_frame = QFrame()
            details_frame.setStyleSheet('\n                background-color: white;\n                border: 1px solid #bdc3c7;\n                border-radius: 5px;\n                padding: 10px;\n                QScrollArea {\n                    border: none;\n                    background-color: transparent;\n                }\n            ')
            details_layout = QVBoxLayout(details_frame)
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameShape(QScrollArea.NoFrame)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            details_container = QWidget()
            details_container_layout = QVBoxLayout(details_container)
            details_container_layout.setContentsMargins(0, 0, 5, 0)
            details_container_layout.setSpacing(10)
            details_title = QLabel('Detalhes da Atividade')
            details_title.setObjectName('subtitle')
            details_container_layout.addWidget(details_title)
            details_text = QTextEdit()
            details_text.setReadOnly(True)
            details_container_layout.addWidget(details_text)
            details_container_layout.addStretch()
            scroll_area.setWidget(details_container)
            details_layout.addWidget(scroll_area)
            layout.addWidget(details_frame)
            def show_activity_details():
                item = activities_list.currentItem()
                if not item:
                    return
                index = activities_list.row(item)
                if 0 <= index < len(suspicious_activities):
                    activity = suspicious_activities[index]
                    details = []
                    details.append(f'App: {activity.get('app', 'Desconhecido')}')
                    details.append(f'Hor├írio: {activity.get('timestamp', 'Desconhecido')}')
                    details.append(f'Atividade: {activity.get('activity', 'Desconhecido')}')
                    details.append(f'Tipo: {activity.get('type', 'Desconhecido')}')
                    if 'details' in activity:
                        details.append('\nDetalhes t├®cnicos:')
                        details.append(activity.get('details', ''))
                    if 'cpu_usage' in activity:
                        details.append(f'\nUso de CPU: {activity.get('cpu_usage')}%')
                    if 'memory_usage' in activity:
                        details.append(f'Uso de mem├│ria: {activity.get('memory_usage')} MB')
                    if 'url' in activity:
                        details.append(f'\nURL detectada: {activity.get('url')}')
                    if 'permissions' in activity:
                        details.append('\nPermiss├Áes utilizadas:')
                        for perm in activity.get('permissions', []):
                            details.append(f'  - {perm}')
                    details_text.setText('\n'.join(details))
                    scroll_area.verticalScrollBar().setValue(0)
            activities_list.currentItemChanged.connect(show_activity_details)
            if activities_list.count() > 0:
                activities_list.setCurrentRow(0)
        if suspicious_activities:
            buttons_layout = QHBoxLayout()
            suspicious_apps = set()
            for activity in suspicious_activities:
                app = activity.get('app')
                if not app:
                    continue
                if app != 'Desconhecido':
                    suspicious_apps.add(app)
            if suspicious_apps:
                remove_btn = QPushButton(f'Remover Apps Suspeitos ({len(suspicious_apps)})')
                remove_btn.setObjectName('remove')
                remove_btn.setStyleSheet('\n                    QPushButton {\n                        background-color: #c0392b;\n                        color: white;\n                        padding: 10px 16px;\n                        font-weight: bold;\n                        min-width: 220px;\n                        min-height: 40px;\n                        border-radius: 6px;\n                    }\n                    QPushButton:hover {\n                        background-color: #e74c3c;\n                    }\n                ')
                def remove_suspicious_apps():
                    apps_list = list(suspicious_apps)
                    if not apps_list:
                        QMessageBox.warning(dialog, 'Aviso', 'Nenhum aplicativo suspeito para selecionar!')
                        return
                    selection_dialog = QDialog(dialog)
                    selection_dialog.setWindowTitle('Selecionar Apps Suspeitos para Remo├º├úo')
                    selection_dialog.setMinimumWidth(600)
                    selection_dialog.setMinimumHeight(400)
                    selection_layout = QVBoxLayout(selection_dialog)
                    warning_label = QLabel('ÔÜá´©Å Selecione os aplicativos suspeitos que deseja remover:')
                    warning_label.setStyleSheet('color: #e74c3c; font-weight: bold; margin-bottom: 10px;')
                    selection_layout.addWidget(warning_label)
                    check_list = QListWidget()
                    for app in apps_list:
                        item = QListWidgetItem(app)
                        item.setData(Qt.UserRole, app)
                        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                        item.setCheckState(Qt.Unchecked)
                        check_list.addItem(item)
                    selection_layout.addWidget(check_list)
                    count_label = QLabel('0 apps selecionados')
                    selection_layout.addWidget(count_label)
                    def update_count():
                        selected = 0
                        for i in range(check_list.count()):
                            if check_list.item(i).checkState() == Qt.Checked:
                                selected += 1
                        count_label.setText(f'{selected} apps selecionados')
                    check_list.itemChanged.connect(update_count)
                    buttons_layout = QHBoxLayout()
                    toggle_btn = QPushButton('Selecionar Todos')
                    toggle_state = False
                    def toggle_all():
                        nonlocal toggle_state
                        toggle_state = not toggle_state
                        state = Qt.Checked if toggle_state else Qt.Unchecked
                        for i in range(check_list.count()):
                            check_list.item(i).setCheckState(state)
                        if toggle_state:
                            toggle_btn.setText('Desselecionar Todos')
                            return
                        None('Selecionar Todos')
                    toggle_btn.clicked.connect(toggle_all)
                    buttons_layout.addWidget(toggle_btn)
                    remove_btn = QPushButton('Remover Selecionados')
                    def do_remove_selected():
                        selected_apps = []
                        for i in range(check_list.count()):
                            item = check_list.item(i)
                            if item.checkState() != Qt.Checked:
                                continue
                            selected_apps.append(item.data(Qt.UserRole) or item.text())
                        if not selected_apps:
                            QMessageBox.warning(selection_dialog, 'Aviso', 'Nenhum aplicativo selecionado!')
                            return
                        apps_str = '\n'.join([f'- {app}' for app in selected_apps])
                        confirm = QMessageBox.question(selection_dialog, 'Confirmar Remo├º├úo', f'Tem certeza que deseja desinstalar os seguintes aplicativos?\n\n{apps_str}', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if confirm == QMessageBox.Yes:
                            selection_dialog.accept()
                            dialog.accept()
                            self.remove_selected_apps(selected_apps)
                    remove_btn.clicked.connect(do_remove_selected)
                    buttons_layout.addWidget(remove_btn)
                    cancel_btn = QPushButton('Cancelar')
                    cancel_btn.clicked.connect(selection_dialog.reject)
                    buttons_layout.addWidget(cancel_btn)
                    selection_layout.addLayout(buttons_layout)
                    selection_dialog.exec_()
                remove_btn.clicked.connect(remove_suspicious_apps)
                buttons_layout.addWidget(remove_btn)
                show_apps_btn = QPushButton('Ver Lista de Apps')
                show_apps_btn.setStyleSheet('\n                    QPushButton {\n                        background-color: #2980b9;\n                        color: white;\n                        padding: 10px 16px;\n                        font-weight: bold;\n                        min-width: 150px;\n                        min-height: 40px;\n                        border-radius: 6px;\n                    }\n                    QPushButton:hover {\n                        background-color: #3498db;\n                    }\n                ')
                def show_apps_list():
                    apps_list = list(suspicious_apps)
                    apps_str = '\n'.join([f'- {app}' for app in apps_list])
                    apps_dialog = QDialog(dialog)
                    apps_dialog.setWindowTitle('Aplicativos Suspeitos Detectados')
                    apps_dialog.setMinimumWidth(600)
                    apps_dialog.setMinimumHeight(400)
                    apps_layout = QVBoxLayout(apps_dialog)
                    title = QLabel(f'Lista de {len(apps_list)} aplicativos suspeitos:')
                    title.setStyleSheet('font-size: 14px; font-weight: bold; margin-bottom: 10px;')
                    apps_layout.addWidget(title)
                    apps_text = QTextEdit()
                    apps_text.setReadOnly(True)
                    apps_text.setPlainText(apps_str)
                    apps_layout.addWidget(apps_text)
                    close_btn = QPushButton('Fechar')
                    close_btn.clicked.connect(apps_dialog.accept)
                    apps_layout.addWidget(close_btn, alignment=Qt.AlignRight)
                    apps_dialog.exec_()
                show_apps_btn.clicked.connect(show_apps_list)
                buttons_layout.addWidget(show_apps_btn)
            close_btn = QPushButton('Fechar')
            close_btn.clicked.connect(dialog.accept)
            buttons_layout.addWidget(close_btn)
            layout.addLayout(buttons_layout)
        dialog.exec_()
    def run_enhanced_analysis(self):
        try:
            if not self.adb.is_device_connected():
                self.log_area.append('ÔØî Erro: Nenhum dispositivo conectado!')
                return
            self.scan_button.setEnabled(False)
            self.advanced_scan_button.setEnabled(False)
            self.enhanced_scan_button.setEnabled(False)
            self.detect_ads_button.setEnabled(False)
            self.disable_miui_ads_button.setEnabled(False)
            self.block_unknown_btn.setEnabled(False)
            self.screen_monitor_button.setEnabled(False)
            self.csi_scan_button.setEnabled(False)
            self.log_area.append('­ƒÜÇ Iniciando an├ílise aprimorada com novos recursos...')
            from app.utils.adware_advanced_detector import AdvancedAdwareDetector
            detector = AdvancedAdwareDetector(self.adb)
            def update_log(message):
                self.log_area.append(message)
                self.log_area.repaint()
                QApplication.processEvents()
            def run_analysis():
                try:
                    results = detector.analyze_device_enhanced(callback=update_log)
                    if 'error' in results:
                        self.log_area.append(f'ÔØî Erro na an├ílise: {results['error']}')
                        self.scan_button.setEnabled(True)
                        self.advanced_scan_button.setEnabled(True)
                        self.enhanced_scan_button.setEnabled(True)
                        self.detect_ads_button.setEnabled(True)
                        self.disable_miui_ads_button.setEnabled(True)
                        self.block_unknown_btn.setEnabled(True)
                        self.screen_monitor_button.setEnabled(True)
                        self.csi_scan_button.setEnabled(True)
                        return
                    self.show_enhanced_results(results)
                except Exception as e:
                    self.log_area.append(f'ÔØî Erro durante an├ílise aprimorada: {str(e)}')
                    logger.error(f'Erro na an├ílise aprimorada: {str(e)}')
                    logger.error(traceback.format_exc())
                finally:
                    self.scan_button.setEnabled(True)
                    self.advanced_scan_button.setEnabled(True)
                    self.enhanced_scan_button.setEnabled(True)
                    self.detect_ads_button.setEnabled(True)
                    self.disable_miui_ads_button.setEnabled(True)
                    self.block_unknown_btn.setEnabled(True)
                    self.screen_monitor_button.setEnabled(True)
                    self.csi_scan_button.setEnabled(True)
            if self._USE_MONITOR_WORKER:
                def _on_results_enhanced(results):
                    try:
                        if results is None:
                            return
                        if isinstance(results, dict) and 'error' in results:
                            self.log_area.append(f'ÔØî Erro na an├ílise: {results['error']}')
                            return
                        self.show_enhanced_results(results)
                        return
                    except Exception as e:
                        self.log_area.append(f'ÔØî Erro ao exibir resultados: {str(e)}')
                        logger.error(traceback.format_exc())
                def _on_error_enhanced(error_msg):
                    self.log_area.append(f'ÔØî Erro durante an├ílise aprimorada: {error_msg}')
                    logger.error(f'Erro na an├ílise aprimorada: {error_msg}')
                def _cleanup_enhanced():
                    self.scan_button.setEnabled(True)
                    self.advanced_scan_button.setEnabled(True)
                    self.enhanced_scan_button.setEnabled(True)
                    self.detect_ads_button.setEnabled(True)
                    self.disable_miui_ads_button.setEnabled(True)
                    self.block_unknown_btn.setEnabled(True)
                    self.screen_monitor_button.setEnabled(True)
                    self.csi_scan_button.setEnabled(True)
                self._iniciar_monitor_worker(target_callable=(lambda cb: detector.analyze_device_enhanced(callback=cb)), on_results=_on_results_enhanced, on_error=_on_error_enhanced, log_target=self.log_area, status_label=None, cleanup=_cleanup_enhanced)
                return
            QTimer.singleShot(100, run_analysis)
            return
        except Exception as e:
            self.log_area.append(f'ÔØî Erro ao iniciar an├ílise aprimorada: {str(e)}')
            logger.error(f'Erro ao iniciar an├ílise aprimorada: {str(e)}')
            logger.error(traceback.format_exc())
            self.scan_button.setEnabled(True)
            self.advanced_scan_button.setEnabled(True)
            self.enhanced_scan_button.setEnabled(True)
            self.detect_ads_button.setEnabled(True)
            self.disable_miui_ads_button.setEnabled(True)
            self.block_unknown_btn.setEnabled(True)
            self.screen_monitor_button.setEnabled(True)
            self.csi_scan_button.setEnabled(True)
    def show_enhanced_results(self, results):
        dialog = QDialog(self)
        dialog.setWindowTitle('Resultados da An├ílise Aprimorada V2.0')
        dialog.setWindowState(Qt.WindowMaximized)
        dialog.setMinimumSize(800, 600)
        dialog.resize(1200, 900)
        main_scroll = QScrollArea(dialog)
        main_scroll.setWidgetResizable(True)
        main_scroll.setFrameShape(QScrollArea.NoFrame)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_widget = QWidget()
        main_scroll.setWidget(main_widget)
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(main_scroll)
        layout = QVBoxLayout(main_widget)
        title = QLabel('­ƒÜÇ An├ílise Aprimorada de Adware V2.0')
        title.setStyleSheet('font-size: 18px; font-weight: bold; color: #e74c3c; margin-bottom: 15px;')
        layout.addWidget(title)
        summary_frame = QFrame()
        summary_frame.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border: 1px solid #dee2e6;\n                border-radius: 8px;\n                padding: 15px;\n                margin-bottom: 15px;\n            }\n        ')
        summary_layout = QVBoxLayout(summary_frame)
        summary_title = QLabel('­ƒôè Resumo da An├ílise')
        summary_title.setStyleSheet('font-size: 14px; font-weight: bold; margin-bottom: 10px;')
        summary_layout.addWidget(summary_title)
        basic_stats = QLabel(f'\n        ÔÇó Total de Apps Analisados: {results.get('total_apps', 0)}\n        ÔÇó Apps Suspeitos Encontrados: {results.get('total_suspicious', 0)}\n        ÔÇó Alto Risco: {results.get('high_risk', 0)} | M├®dio Risco: {results.get('medium_risk', 0)} | Baixo Risco: {results.get('low_risk', 0)}\n        ÔÇó Data/Hora da An├ílise: {results.get('scan_time', 'N/A')}\n        ')
        summary_layout.addWidget(basic_stats)
        if 'enhanced_features' in results:
            enhanced_features = results['enhanced_features']
            enhanced_stats = QLabel('­ƒö¼ Recursos Aprimorados:')
            enhanced_stats.setStyleSheet('font-weight: bold; margin-top: 10px;')
            summary_layout.addWidget(enhanced_stats)
            stats_text = ''
            if 'network_analysis' in enhanced_features:
                net_data = enhanced_features['network_analysis']
                stats_text += f'ÔÇó Conex├Áes de Rede: {net_data.get('total_connections', 0)} (Suspeitas: {len(net_data.get('ad_related', []))})\n'
            if 'services_analysis' in enhanced_features:
                serv_data = enhanced_features['services_analysis']
                stats_text += f'ÔÇó Servi├ºos Suspeitos: {serv_data.get('total_services', 0)}\n'
            if 'battery_analysis' in enhanced_features:
                bat_data = enhanced_features['battery_analysis']
                stats_text += f'ÔÇó Apps com Alto Consumo: {bat_data.get('total_high_battery', 0)}\n'
            if 'intents_analysis' in enhanced_features:
                int_data = enhanced_features['intents_analysis']
                stats_text += f'ÔÇó Intents Suspeitos: {int_data.get('total_intents', 0)}\n'
            enhanced_stats_label = QLabel(stats_text)
            summary_layout.addWidget(enhanced_stats_label)
        layout.addWidget(summary_frame)
        tabs = QTabWidget()
        apps_tab = QWidget()
        apps_layout = QVBoxLayout(apps_tab)
        apps_label = QLabel(f'Apps Suspeitos Detectados ({len(results.get('suspicious_apps', {}))})')
        apps_label.setStyleSheet('font-weight: bold; margin-bottom: 10px;')
        apps_layout.addWidget(apps_label)
        apps_list = QListWidget()
        for package, info in results.get('suspicious_apps', {}).items():
            item_text = f'[{info['risk_level']}] {info.get('app_name', package)} - Score: {info['score']}'
            item = QListWidgetItem(item_text)
            if info['risk_level'] == 'Alto':
                item.setBackground(QColor('#ffebee'))
            elif info['risk_level'] == 'M├®dio':
                item.setBackground(QColor('#fff8e1'))
            else:
                item.setBackground(QColor('#f3e5f5'))
            apps_list.addItem(item)
        apps_layout.addWidget(apps_list)
        tabs.addTab(apps_tab, '­ƒÄ» Apps Suspeitos')
        if 'enhanced_features' in results and 'network_analysis' in results['enhanced_features']:
            network_tab = QWidget()
            network_layout = QVBoxLayout(network_tab)
            net_data = results['enhanced_features']['network_analysis']
            net_label = QLabel(f'Conex├Áes de Rede Detectadas ({net_data.get('total_connections', 0)})')
            net_label.setStyleSheet('font-weight: bold; margin-bottom: 10px;')
            network_layout.addWidget(net_label)
            net_list = QListWidget()
            for conn in net_data.get('suspicious_connections', []):
                item_text = f'[{'ÔÜá´©Å SUSPEITA' if conn.get('suspicious') else 'Normal'}] Porto {conn.get('port')}: {conn.get('line')}'
                item = QListWidgetItem(item_text)
                if conn.get('suspicious'):
                    item.setBackground(QColor('#ffebee'))
                net_list.addItem(item)
            network_layout.addWidget(net_list)
            tabs.addTab(network_tab, '­ƒîÉ Rede')
        layout.addWidget(tabs)
        buttons_layout = QHBoxLayout()
        if results.get('suspicious_apps'):
            remove_btn = QPushButton('­ƒùæ´©Å Selecionar Apps para Remover')
            remove_btn.setStyleSheet('\n                QPushButton {\n                    background-color: #c0392b;\n                    color: white;\n                    padding: 10px 20px;\n                    font-weight: bold;\n                    border-radius: 6px;\n                }\n                QPushButton:hover {\n                    background-color: #e74c3c;\n                }\n            ')
            def remove_apps():
                selection_dialog = QDialog(dialog)
                selection_dialog.setWindowTitle('Selecionar Aplicativos para Remo├º├úo')
                selection_dialog.setWindowState(Qt.WindowMaximized)
                selection_dialog.setMinimumSize(800, 600)
                selection_dialog.resize(1200, 900)
                selection_layout = QVBoxLayout(selection_dialog)
                warning_label = QLabel('ÔÜá´©Å Selecione os aplicativos que deseja remover:')
                warning_label.setStyleSheet('color: #e74c3c; font-weight: bold; margin-bottom: 10px; font-size: 14px;')
                selection_layout.addWidget(warning_label)
                info_label = QLabel('Voc├¬ pode remover tanto aplicativos maliciosos quanto aplicativos n├úo desejados.')
                info_label.setStyleSheet('color: #666; margin-bottom: 15px;')
                selection_layout.addWidget(info_label)
                apps_list = QListWidget()
                apps_list.setStyleSheet('\n                    QListWidget {\n                        border: 1px solid #ddd;\n                        border-radius: 6px;\n                        background-color: white;\n                    }\n                    QListWidget::item {\n                        padding: 8px;\n                        border-bottom: 1px solid #f0f0f0;\n                    }\n                    QListWidget::item:hover {\n                        background-color: #f8f9fa;\n                    }\n                ')
                for package, info in results['suspicious_apps'].items():
                    app_name = info.get('app_name', package)
                    risk_level = info.get('risk_level', 'Baixo')
                    score = info.get('score', 0)
                    reasons = info.get('reasons', [])
                    item_text = f'{app_name}\n'
                    item_text += f'Pacote: {package}\n'
                    item_text += f'Risco: {risk_level} (Score: {score})\n'
                    item_text += f'Motivos: {'; '.join(reasons[:2])}{'...' if len(reasons) > 2 else ''}'
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, package)
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    item.setCheckState(Qt.Unchecked)
                    if risk_level == 'Alto':
                        item.setBackground(QColor('#ffebee'))
                    elif risk_level == 'M├®dio':
                        item.setBackground(QColor('#fff8e1'))
                    else:
                        item.setBackground(QColor('#f3e5f5'))
                    apps_list.addItem(item)
                    continue
                selection_layout.addWidget(apps_list)
                count_label = QLabel('0 aplicativos selecionados')
                count_label.setStyleSheet('font-weight: bold; color: #666; margin-top: 10px;')
                selection_layout.addWidget(count_label)
                def update_count():
                    selected = 0
                    for i in range(apps_list.count()):
                        if apps_list.item(i).checkState() == Qt.Checked:
                            selected += 1
                    count_label.setText(f'{selected} aplicativo(s) selecionado(s)')
                apps_list.itemChanged.connect(update_count)
                control_layout = QHBoxLayout()
                toggle_btn = QPushButton('Selecionar Todos')
                toggle_state = False
                def toggle_all():
                    nonlocal toggle_state
                    toggle_state = not toggle_state
                    state = Qt.Checked if toggle_state else Qt.Unchecked
                    for i in range(apps_list.count()):
                        apps_list.item(i).setCheckState(state)
                    if toggle_state:
                        toggle_btn.setText('Desselecionar Todos')
                        return
                    None('Selecionar Todos')
                toggle_btn.clicked.connect(toggle_all)
                control_layout.addWidget(toggle_btn)
                high_risk_btn = QPushButton('Selecionar Alto Risco')
                def select_high_risk():
                    for i in range(apps_list.count()):
                        item = apps_list.item(i)
                        package = item.data(Qt.UserRole)
                        if package in results['suspicious_apps']:
                            risk_level = results['suspicious_apps'][package].get('risk_level', 'Baixo')
                            if risk_level == 'Alto':
                                item.setCheckState(Qt.Checked)
                            else:
                                item.setCheckState(Qt.Unchecked)
                high_risk_btn.clicked.connect(select_high_risk)
                control_layout.addWidget(high_risk_btn)
                selection_layout.addLayout(control_layout)
                buttons_layout = QHBoxLayout()
                confirm_remove_btn = QPushButton('Remover Selecionados')
                confirm_remove_btn.setStyleSheet('\n                    QPushButton {\n                        background-color: #e74c3c;\n                        color: white;\n                        padding: 10px 20px;\n                        font-weight: bold;\n                        border-radius: 6px;\n                    }\n                    QPushButton:hover {\n                        background-color: #c0392b;\n                    }\n                ')
                def do_remove_selected():
                    selected_apps = []
                    for i in range(apps_list.count()):
                        item = apps_list.item(i)
                        if item.checkState() == Qt.Checked:
                            package = item.data(Qt.UserRole)
                            selected_apps.append(package)
                    if not selected_apps:
                        QMessageBox.warning(selection_dialog, 'Aviso', 'Nenhum aplicativo selecionado!')
                        return
                    app_names = []
                    for package in selected_apps:
                        if package in results['suspicious_apps']:
                            app_name = results['suspicious_apps'][package].get('app_name', package)
                            app_names.append(f'- {app_name} ({package})')
                    confirm_msg = 'Tem certeza que deseja desinstalar os seguintes aplicativos?\n\n' + '\n'.join(app_names)
                    confirm = QMessageBox.question(selection_dialog, 'Confirmar Remo├º├úo', confirm_msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if confirm == QMessageBox.Yes:
                        selection_dialog.accept()
                        dialog.accept()
                        self.remove_selected_apps(selected_apps)
                confirm_remove_btn.clicked.connect(do_remove_selected)
                buttons_layout.addWidget(confirm_remove_btn)
                cancel_btn = QPushButton('Cancelar')
                cancel_btn.clicked.connect(selection_dialog.reject)
                buttons_layout.addWidget(cancel_btn)
                selection_layout.addLayout(buttons_layout)
                selection_dialog.exec_()
            remove_btn.clicked.connect(remove_apps)
            buttons_layout.addWidget(remove_btn)
        close_btn = QPushButton('Fechar')
        close_btn.clicked.connect(dialog.accept)
        buttons_layout.addWidget(close_btn)
        layout.addLayout(buttons_layout)
        dialog.exec_()
    def run_screen_monitoring(self):
        try:
            if not self.adb.is_device_connected():
                self.log_area.append('ÔØî Erro: Nenhum dispositivo conectado!')
                return
            duration, ok = QInputDialog.getInt(self, 'Dura├º├úo do Monitoramento', 'Por quantos segundos deseja monitorar a tela?', 30, 10, 300, 10)
            if not ok:
                return
            self.scan_button.setEnabled(False)
            self.advanced_scan_button.setEnabled(False)
            self.enhanced_scan_button.setEnabled(False)
            self.detect_ads_button.setEnabled(False)
            self.disable_miui_ads_button.setEnabled(False)
            self.block_unknown_btn.setEnabled(False)
            self.screen_monitor_button.setEnabled(False)
            self.csi_scan_button.setEnabled(False)
            self.log_area.append(f'­ƒô▒ Iniciando monitoramento de tela por {duration} segundos...')
            from app.utils.adware_advanced_detector import AdvancedAdwareDetector
            detector = AdvancedAdwareDetector(self.adb)
            def update_log(message):
                self.log_area.append(message)
                self.log_area.repaint()
                QApplication.processEvents()
            def run_monitoring():
                try:
                    results = detector.monitor_screen_changes(duration=duration, callback=update_log)
                    if 'error' in results:
                        self.log_area.append(f'ÔØî Erro no monitoramento: {results['error']}')
                        self.scan_button.setEnabled(True)
                        self.advanced_scan_button.setEnabled(True)
                        self.enhanced_scan_button.setEnabled(True)
                        self.detect_ads_button.setEnabled(True)
                        self.disable_miui_ads_button.setEnabled(True)
                        self.block_unknown_btn.setEnabled(True)
                        self.screen_monitor_button.setEnabled(True)
                        self.csi_scan_button.setEnabled(True)
                        return
                    self.show_screen_monitoring_results(results)
                except Exception as e:
                    self.log_area.append(f'ÔØî Erro durante monitoramento: {str(e)}')
                    logger.error(f'Erro no monitoramento de tela: {str(e)}')
                    logger.error(traceback.format_exc())
                finally:
                    self.scan_button.setEnabled(True)
                    self.advanced_scan_button.setEnabled(True)
                    self.enhanced_scan_button.setEnabled(True)
                    self.detect_ads_button.setEnabled(True)
                    self.disable_miui_ads_button.setEnabled(True)
                    self.block_unknown_btn.setEnabled(True)
                    self.screen_monitor_button.setEnabled(True)
                    self.csi_scan_button.setEnabled(True)
            if self._USE_MONITOR_WORKER:
                def _on_results_screen(results):
                    try:
                        if results is None:
                            return
                        if isinstance(results, dict) and 'error' in results:
                            self.log_area.append(f'ÔØî Erro no monitoramento: {results['error']}')
                            return
                        self.show_screen_monitoring_results(results)
                        return
                    except Exception as e:
                        self.log_area.append(f'ÔØî Erro ao exibir resultados: {str(e)}')
                        logger.error(traceback.format_exc())
                def _on_error_screen(error_msg):
                    self.log_area.append(f'ÔØî Erro durante monitoramento: {error_msg}')
                    logger.error(f'Erro no monitoramento de tela: {error_msg}')
                def _cleanup_screen():
                    self.scan_button.setEnabled(True)
                    self.advanced_scan_button.setEnabled(True)
                    self.enhanced_scan_button.setEnabled(True)
                    self.detect_ads_button.setEnabled(True)
                    self.disable_miui_ads_button.setEnabled(True)
                    self.block_unknown_btn.setEnabled(True)
                    self.screen_monitor_button.setEnabled(True)
                    self.csi_scan_button.setEnabled(True)
                self._iniciar_monitor_worker(target_callable=(lambda cb: detector.monitor_screen_changes(duration=duration, callback=cb)), on_results=_on_results_screen, on_error=_on_error_screen, log_target=self.log_area, status_label=None, cleanup=_cleanup_screen)
                return
            QTimer.singleShot(100, run_monitoring)
            return
        except Exception as e:
            self.log_area.append(f'ÔØî Erro ao iniciar monitoramento: {str(e)}')
            logger.error(f'Erro ao iniciar monitoramento de tela: {str(e)}')
            logger.error(traceback.format_exc())
            self.scan_button.setEnabled(True)
            self.advanced_scan_button.setEnabled(True)
            self.enhanced_scan_button.setEnabled(True)
            self.detect_ads_button.setEnabled(True)
            self.disable_miui_ads_button.setEnabled(True)
            self.block_unknown_btn.setEnabled(True)
            self.screen_monitor_button.setEnabled(True)
            self.csi_scan_button.setEnabled(True)
    def show_screen_monitoring_results(self, results):
        dialog = QDialog(self)
        dialog.setWindowTitle('Resultados do Monitoramento de Tela')
        dialog.setWindowState(Qt.WindowMaximized)
        dialog.setMinimumSize(800, 600)
        dialog.resize(1200, 900)
        dialog.setStyleSheet('\n            QScrollArea {\n                border: none;\n                background-color: transparent;\n            }\n            QScrollBar:vertical {\n                background-color: #f0f0f0;\n                width: 12px;\n                border-radius: 6px;\n                margin: 0px;\n            }\n            QScrollBar::handle:vertical {\n                background-color: #c0c0c0;\n                border-radius: 6px;\n                min-height: 20px;\n            }\n            QScrollBar::handle:vertical:hover {\n                background-color: #a0a0a0;\n            }\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                border: none;\n                background: none;\n            }\n        ')
        main_scroll = QScrollArea(dialog)
        main_scroll.setWidgetResizable(True)
        main_scroll.setFrameShape(QScrollArea.NoFrame)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_widget = QWidget()
        main_scroll.setWidget(main_widget)
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(main_scroll)
        layout = QVBoxLayout(main_widget)
        title = QLabel('­ƒô▒ Monitor de Atividade na Tela')
        title.setStyleSheet('font-size: 18px; font-weight: bold; color: #f39c12; margin-bottom: 15px;')
        layout.addWidget(title)
        screen_changes = results.get('screen_changes', [])
        suspicious_count = results.get('suspicious_events', 0)
        summary_text = f'  ÔÇó Dura├º├úo do Monitoramento: {results.get('duration', 0)} segundos\n  ÔÇó Tecnologia: Tech Union Solutions\n  ÔÇó Apps suspeitos detectados: {suspicious_count}'
        summary_label = QLabel(summary_text)
        summary_label.setStyleSheet('\n            background-color: #f8f9fa;\n            border: 1px solid #dee2e6;\n            border-radius: 8px;\n            padding: 15px;\n            margin-bottom: 15px;\n        ')
        layout.addWidget(summary_label)
        if screen_changes:
            events_label = QLabel('­ƒÜ¿ Apps que for├ºaram o primeiro plano repetidamente:')
            events_label.setStyleSheet('font-weight: bold; margin-bottom: 10px;')
            layout.addWidget(events_label)
            events_list = QListWidget()
            for change in screen_changes:
                timestamp = change.get('timestamp', 'N/A')
                packages = ', '.join(change.get('active_overlays', []))
                count = change.get('count', 3)
                item_text = f'[{timestamp}] ÔÜá´©Å SUSPEITO ÔÇö {packages} (apareceu {count}x na tela)'
                item = QListWidgetItem(item_text)
                item.setBackground(QColor('#ffebee'))
                events_list.addItem(item)
            layout.addWidget(events_list)
        else:
            no_events_label = QLabel('Ô£à Nenhum app suspeito detectado durante o monitoramento.')
            no_events_label.setStyleSheet('color: #27ae60; font-weight: bold; padding: 20px;')
            layout.addWidget(no_events_label)
        buttons_layout = QHBoxLayout()
        if screen_changes:
            detected_packages = []
            for change in screen_changes:
                for pkg in change.get('active_overlays', []):
                    if pkg not in detected_packages:
                        detected_packages.append(pkg)
            remove_btn = QPushButton(f'­ƒùæ´©Å Selecionar Apps para Remover ({len(detected_packages)})')
            remove_btn.setStyleSheet('\n                QPushButton {\n                    background-color: #c0392b;\n                    color: white;\n                    border-radius: 6px;\n                    padding: 10px 18px;\n                    font-weight: bold;\n                    font-size: 13px;\n                    min-height: 40px;\n                }\n                QPushButton:hover { background-color: #e74c3c; }\n                QPushButton:pressed { background-color: #a93226; }\n            ')
            def _on_open_selection():
                if not detected_packages:
                    QMessageBox.warning(dialog, 'Aviso', 'Nenhum aplicativo detectado!')
                    return
                selection_dialog = QDialog(dialog)
                selection_dialog.setWindowTitle('Selecionar Apps para Remo├º├úo')
                selection_dialog.setWindowState(Qt.WindowMaximized)
                selection_dialog.setMinimumSize(800, 600)
                selection_dialog.resize(1000, 800)
                sel_layout = QVBoxLayout(selection_dialog)
                info_label = QLabel('ÔÜá´©Å Verifique a lista antes de remover.\nSelecione apenas os apps que confirmou serem maliciosos:')
                info_label.setStyleSheet('color: #e74c3c; font-weight: bold; margin-bottom: 10px;')
                sel_layout.addWidget(info_label)
                try:
                    _ui_protegidos = obter_pacotes_protegidos(self.adb)
                except Exception:
                    _ui_protegidos = set()
                check_list = QListWidget()
                for pkg in detected_packages:
                    item = QListWidgetItem(pkg)
                    item.setData(Qt.UserRole, pkg)
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    item.setCheckState(Qt.Unchecked)
                    if is_pacote_protegido(pkg, _ui_protegidos):
                        item.setForeground(QColor('#b0bec5'))
                        item.setToolTip('Este app pode ser do sistema. Avalie antes de remover.')
                    check_list.addItem(item)
                sel_layout.addWidget(check_list)
                count_label = QLabel('0 apps selecionados')
                sel_layout.addWidget(count_label)
                def _update_count():
                    total = sum((1 for i in range(check_list.count()) if check_list.item(i).flags() & Qt.ItemIsUserCheckable or check_list.item(i).checkState() == Qt.Checked))
                    count_label.setText(f'{total} app(s) selecionado(s)')
                check_list.itemChanged.connect(_update_count)
                btn_layout = QHBoxLayout()
                toggle_btn = QPushButton('Selecionar Todos')
                _toggle_state = [False]
                def _toggle_all():
                    _toggle_state[0] = not _toggle_state[0]
                    state = Qt.Checked if _toggle_state[0] else Qt.Unchecked
                    for i in range(check_list.count()):
                        it = check_list.item(i)
                        if it.flags() & Qt.ItemIsUserCheckable:
                            it.setCheckState(state)
                    if _toggle_state[0]:
                        toggle_btn.setText('Desselecionar Todos')
                        return
                    None('Selecionar Todos')
                toggle_btn.clicked.connect(_toggle_all)
                btn_layout.addWidget(toggle_btn)
                confirm_btn = QPushButton('Remover Selecionados')
                confirm_btn.setStyleSheet('\n                    QPushButton {\n                        background-color: #c0392b; color: white;\n                        border-radius: 5px; padding: 8px 16px; font-weight: bold;\n                    }\n                    QPushButton:hover { background-color: #e74c3c; }\n                ')
                def _do_remove():
                    selected = [check_list.item(i).data(Qt.UserRole) or check_list.item(i).text() for i in range(check_list.count()) if check_list.item(i).checkState() == Qt.Checked]
                    if not selected:
                        QMessageBox.warning(selection_dialog, 'Aviso', 'Nenhum app selecionado!')
                        return
                    apps_str = '\n'.join((f'ÔÇó {a}' for a in selected))
                    confirm = QMessageBox.question(selection_dialog, 'Confirmar Remo├º├úo', f'Deseja remover {len(selected)} app(s)?\n\n{apps_str}', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if confirm == QMessageBox.Yes:
                        selection_dialog.accept()
                        dialog.accept()
                        self.remove_selected_apps(selected)
                confirm_btn.clicked.connect(_do_remove)
                btn_layout.addWidget(confirm_btn)
                cancel_btn = QPushButton('Cancelar')
                cancel_btn.clicked.connect(selection_dialog.reject)
                btn_layout.addWidget(cancel_btn)
                sel_layout.addLayout(btn_layout)
                selection_dialog.exec_()
            remove_btn.clicked.connect(_on_open_selection)
            buttons_layout.addWidget(remove_btn)
        close_btn = QPushButton('Fechar')
        close_btn.clicked.connect(dialog.accept)
        buttons_layout.addWidget(close_btn)
        layout.addLayout(buttons_layout)
        dialog.exec_()
    def run_csi_investigation(self):
        try:
            if not self.adb.is_device_connected():
                self.log_area.append('ÔØî Erro: Nenhum dispositivo conectado!')
                QMessageBox.warning(self, 'Dispositivo n├úo encontrado', 'Nenhum dispositivo Android conectado!\n\nPor favor, conecte um dispositivo via USB e ative a Depura├º├úo USB.')
                return
            self.scan_button.setEnabled(False)
            self.advanced_scan_button.setEnabled(False)
            self.enhanced_scan_button.setEnabled(False)
            self.detect_ads_button.setEnabled(False)
            self.disable_miui_ads_button.setEnabled(False)
            self.block_unknown_btn.setEnabled(False)
            self.screen_monitor_button.setEnabled(False)
            self.csi_scan_button.setEnabled(False)
            self.log_area.append('\n============================================================')
            self.log_area.append('­ƒòÁ´©Å [CSI] CRIME SCENE INVESTIGATION - Triagem Inteligente')
            self.log_area.append('============================================================')
            csi = AdwareCSI(self.adb)
            def update_log(message):
                self.log_area.append(message)
                self.log_area.repaint()
                QApplication.processEvents()
            def run_investigation():
                try:
                    results = csi.investigate(callback=update_log)
                    if 'error' in results and results['error']:
                        self.log_area.append(f'ÔØî Erro na investiga├º├úo: {results['error']}')
                        self.scan_button.setEnabled(True)
                        self.advanced_scan_button.setEnabled(True)
                        self.enhanced_scan_button.setEnabled(True)
                        self.detect_ads_button.setEnabled(True)
                        self.disable_miui_ads_button.setEnabled(True)
                        self.block_unknown_btn.setEnabled(True)
                        self.screen_monitor_button.setEnabled(True)
                        self.csi_scan_button.setEnabled(True)
                        return
                    if results.get('suspects'):
                        self.show_csi_results(results)
                    else:
                        QMessageBox.information(self, 'CSI - Investiga├º├úo Conclu├¡da', 'Ô£à Nenhum aplicativo suspeito encontrado!\n\nO dispositivo parece estar limpo baseado nos crit├®rios:\nÔÇó Instala├º├úo recente (Ôëñ10 dias)\nÔÇó Abuso de bateria e atividade suspeita\nÔÇó Padr├Áes de ads no logcat\nÔÇó Combina├º├Áes perigosas de permiss├Áes')
                except Exception as e:
                    self.log_area.append(f'ÔØî Erro durante investiga├º├úo CSI: {str(e)}')
                    logger.error(f'Erro na investiga├º├úo CSI: {str(e)}')
                    logger.error(traceback.format_exc())
                finally:
                    self.scan_button.setEnabled(True)
                    self.advanced_scan_button.setEnabled(True)
                    self.enhanced_scan_button.setEnabled(True)
                    self.detect_ads_button.setEnabled(True)
                    self.disable_miui_ads_button.setEnabled(True)
                    self.block_unknown_btn.setEnabled(True)
                    self.screen_monitor_button.setEnabled(True)
                    self.csi_scan_button.setEnabled(True)
            if self._USE_MONITOR_WORKER:
                def _on_results_csi(results):
                    try:
                        if results is None:
                            return
                        if isinstance(results, dict) and results.get('error'):
                            self.log_area.append(f'ÔØî Erro na investiga├º├úo: {results['error']}')
                            return
                        if isinstance(results, dict) and results.get('suspects'):
                            self.show_csi_results(results)
                            return
                        QMessageBox.information(self, 'CSI - Investiga├º├úo Conclu├¡da', 'Ô£à Nenhum aplicativo suspeito encontrado!\n\nO dispositivo parece estar limpo baseado nos crit├®rios:\nÔÇó Instala├º├úo recente (Ôëñ10 dias)\nÔÇó Abuso de bateria e atividade suspeita\nÔÇó Padr├Áes de ads no logcat\nÔÇó Combina├º├Áes perigosas de permiss├Áes')
                        return
                    except Exception as e:
                        self.log_area.append(f'ÔØî Erro ao exibir resultados CSI: {str(e)}')
                        logger.error(traceback.format_exc())
                def _on_error_csi(error_msg):
                    self.log_area.append(f'ÔØî Erro durante investiga├º├úo CSI: {error_msg}')
                    logger.error(f'Erro na investiga├º├úo CSI: {error_msg}')
                def _cleanup_csi():
                    self.scan_button.setEnabled(True)
                    self.advanced_scan_button.setEnabled(True)
                    self.enhanced_scan_button.setEnabled(True)
                    self.detect_ads_button.setEnabled(True)
                    self.disable_miui_ads_button.setEnabled(True)
                    self.block_unknown_btn.setEnabled(True)
                    self.screen_monitor_button.setEnabled(True)
                    self.csi_scan_button.setEnabled(True)
                self._iniciar_monitor_worker(target_callable=(lambda cb: csi.investigate(callback=cb)), on_results=_on_results_csi, on_error=_on_error_csi, log_target=self.log_area, status_label=None, cleanup=_cleanup_csi)
                return
            QTimer.singleShot(100, run_investigation)
            return
        except Exception as e:
            self.log_area.append(f'ÔØî Erro ao iniciar investiga├º├úo CSI: {str(e)}')
            logger.error(f'Erro ao iniciar investiga├º├úo CSI: {str(e)}')
            logger.error(traceback.format_exc())
            self.scan_button.setEnabled(True)
            self.advanced_scan_button.setEnabled(True)
            self.enhanced_scan_button.setEnabled(True)
            self.detect_ads_button.setEnabled(True)
            self.disable_miui_ads_button.setEnabled(True)
            self.block_unknown_btn.setEnabled(True)
            self.screen_monitor_button.setEnabled(True)
            self.csi_scan_button.setEnabled(True)
    def show_csi_results(self, results):
        dialog = QDialog(self)
        dialog.setWindowTitle('­ƒòÁ´©Å CSI - Resultados da Investiga├º├úo')
        dialog.setWindowState(Qt.WindowMaximized)
        dialog.setMinimumSize(900, 700)
        dialog.resize(1200, 900)
        dialog.setStyleSheet("\n            QDialog {\n                background-color: #1a1a2e;\n            }\n            QLabel {\n                color: #eee;\n                font-size: 13px;\n            }\n            QLabel#title {\n                font-size: 20px;\n                font-weight: bold;\n                color: #00ff88;\n                margin-bottom: 15px;\n            }\n            QLabel#subtitle {\n                font-size: 14px;\n                font-weight: bold;\n                color: #00d4ff;\n                margin-top: 10px;\n            }\n            QListWidget {\n                background-color: #16213e;\n                border: 1px solid #0f3460;\n                border-radius: 8px;\n                color: #eee;\n                font-family: 'Consolas', 'Courier New', monospace;\n                font-size: 12px;\n                padding: 6px;\n                outline: none;\n            }\n            QListWidget::item {\n                padding: 10px;\n                border-bottom: 1px solid #0f3460;\n            }\n            QListWidget::item:selected {\n                background-color: #0f3460;\n            }\n            QListWidget::item:hover {\n                background-color: #1a3a5c;\n            }\n            /* Checkbox interno dos QListWidgetItem (cirurgico ÔÇö fix\n               principal da invisibilidade reportada). */\n            QListWidget::indicator {\n                width: 18px;\n                height: 18px;\n                border-radius: 4px;\n                border: 2px solid #00d4ff;\n                background-color: rgba(255, 255, 255, 25);\n                margin-right: 6px;\n            }\n            QListWidget::indicator:hover {\n                border: 2px solid #00ff88;\n                background-color: rgba(0, 255, 136, 40);\n            }\n            QListWidget::indicator:checked {\n                border: 2px solid #00ff88;\n                background-color: #00ff88;\n                image: url();  /* sem imagem ÔÇö usa pseudo-fill via background */\n            }\n            QListWidget::indicator:checked:hover {\n                border: 2px solid #00d4ff;\n                background-color: #10b981;\n            }\n            QListWidget::indicator:disabled {\n                border: 2px solid #444;\n                background-color: rgba(255, 255, 255, 10);\n            }\n            /* Scrollbar dark consistente com o tema CSI. */\n            QListWidget QScrollBar:vertical,\n            QScrollArea QScrollBar:vertical {\n                background: #0f1a2e;\n                width: 12px;\n                margin: 2px;\n                border-radius: 6px;\n            }\n            QListWidget QScrollBar::handle:vertical,\n            QScrollArea QScrollBar::handle:vertical {\n                background: #0f3460;\n                min-height: 30px;\n                border-radius: 6px;\n            }\n            QListWidget QScrollBar::handle:vertical:hover,\n            QScrollArea QScrollBar::handle:vertical:hover {\n                background: #1a4d8f;\n            }\n            QListWidget QScrollBar::add-line:vertical,\n            QListWidget QScrollBar::sub-line:vertical,\n            QScrollArea QScrollBar::add-line:vertical,\n            QScrollArea QScrollBar::sub-line:vertical {\n                height: 0px;\n                background: transparent;\n            }\n            QPushButton {\n                padding: 10px 20px;\n                background-color: #059669;\n                color: white;\n                border: none;\n                border-radius: 6px;\n                font-weight: bold;\n                min-height: 35px;\n            }\n            QPushButton:hover {\n                background-color: #10b981;\n            }\n            QPushButton:pressed {\n                background-color: #047857;\n            }\n            QPushButton:disabled {\n                background-color: #374151;\n                color: #9ca3af;\n            }\n            QPushButton#remove {\n                background-color: #dc2626;\n            }\n            QPushButton#remove:hover {\n                background-color: #ef4444;\n            }\n            QPushButton#remove:pressed {\n                background-color: #b91c1c;\n            }\n            QTextEdit {\n                background-color: #16213e;\n                color: #00ff88;\n                border: 1px solid #0f3460;\n                border-radius: 8px;\n                font-family: 'Consolas', 'Courier New', monospace;\n                font-size: 12px;\n            }\n            QFrame#stats {\n                background-color: #16213e;\n                border: 1px solid #0f3460;\n                border-radius: 10px;\n                padding: 15px;\n            }\n        ")
        main_scroll = QScrollArea(dialog)
        main_scroll.setWidgetResizable(True)
        main_scroll.setFrameShape(QScrollArea.NoFrame)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_widget = QWidget()
        main_scroll.setWidget(main_widget)
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(main_scroll)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        title = QLabel('­ƒòÁ´©Å CSI: CRIME SCENE INVESTIGATION')
        title.setObjectName('title')
        layout.addWidget(title)
        stats = results.get('statistics', {})
        stats_frame = QFrame()
        stats_frame.setObjectName('stats')
        stats_layout = QHBoxLayout(stats_frame)
        stat_cards = [('­ƒôè Analisados', str(stats.get('total_apps_analyzed', 0)), '#3b82f6'), ('­ƒÜ¿ Suspeitos', str(stats.get('total_suspects', 0)), '#f59e0b'), ('­ƒö┤ Cr├¡tico', str(stats.get('critical_risk', 0)), '#dc2626'), ('­ƒƒá Alto', str(stats.get('high_risk', 0)), '#ea580c'), ('­ƒƒí M├®dio', str(stats.get('medium_risk', 0)), '#eab308'), ('­ƒƒó Baixo', str(stats.get('low_risk', 0)), '#22c55e')]
        for label_text, value, color in stat_cards:
            card = QFrame()
            card.setStyleSheet(f'\n                QFrame {{\n                    background-color: {color}22;\n                    border: 1px solid {color};\n                    border-radius: 8px;\n                    padding: 10px;\n                }}\n            ')
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(5)
            value_label = QLabel(value)
            value_label.setStyleSheet(f'font-size: 28px; font-weight: bold; color: {color}; text-align: center;')
            value_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(value_label)
            text_label = QLabel(label_text)
            text_label.setStyleSheet('font-size: 11px; color: #aaa; text-align: center;')
            text_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(text_label)
            stats_layout.addWidget(card)
        layout.addWidget(stats_frame)
        suspects_subtitle = QLabel(f'­ƒôï Suspeitos Detectados ({len(results.get('suspects', []))})')
        suspects_subtitle.setObjectName('subtitle')
        layout.addWidget(suspects_subtitle)
        suspects_list = QListWidget()
        suspects_list.setMinimumHeight(300)
        suspects = results.get('suspects', [])
        for suspect in suspects:
            pkg = suspect.get('package', '')
            app_name = suspect.get('app_name', pkg.split('.')[-1])
            score = suspect.get('score', 0)
            risk = suspect.get('risk_level', 'BAIXO')
            reasons = suspect.get('reasons', [])
            days = suspect.get('days_since_install')
            risk_icon = {'CR├ìTICO': '­ƒö┤', 'ALTO': '­ƒƒá', 'M├ëDIO': '­ƒƒí', 'BAIXO': '­ƒƒó'}.get(risk, 'ÔÜ¬')
            item_text = f'{risk_icon} [{risk}] {app_name} (Score: {score})\n'
            item_text += f'   ­ƒôª {pkg}\n'
            if days is not None:
                item_text += f'   ­ƒôà Instalado h├í {days} dias\n'
            item_text += f'   ­ƒôØ {', '.join(reasons[:3])}'
            if len(reasons) > 3:
                item_text += f' (+{len(reasons) - 3} motivos)'
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, pkg)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            risk_colors = {'CR├ìTICO': '#dc262633', 'ALTO': '#ea580c33', 'M├ëDIO': '#eab30833', 'BAIXO': '#22c55e22'}
            item.setBackground(QColor(risk_colors.get(risk, '#22222222')))
            suspects_list.addItem(item)
            continue
        layout.addWidget(suspects_list)
        count_label = QLabel('0 aplicativo(s) selecionado(s)')
        count_label.setStyleSheet('color: #aaa; font-size: 12px;')
        layout.addWidget(count_label)
        def update_count():
            selected = sum((1 for i in range(suspects_list.count()) if suspects_list.item(i).checkState() == Qt.Checked))
            count_label.setText(f'{selected} aplicativo(s) selecionado(s)')
        suspects_list.itemChanged.connect(update_count)
        buttons_layout = QHBoxLayout()
        select_all_btn = QPushButton('Selecionar Todos')
        select_state = [False]
        def toggle_all():
            select_state[0] = not select_state[0]
            state = Qt.Checked if select_state[0] else Qt.Unchecked
            for i in range(suspects_list.count()):
                suspects_list.item(i).setCheckState(state)
            if select_state[0]:
                select_all_btn.setText('Desselecionar')
                return
            None('Selecionar Todos')
        select_all_btn.clicked.connect(toggle_all)
        buttons_layout.addWidget(select_all_btn)
        select_critical_btn = QPushButton('Selecionar Cr├¡ticos/Altos')
        def select_critical():
            for i in range(suspects_list.count()):
                item = suspects_list.item(i)
                pkg = item.data(Qt.UserRole)
                for s in suspects:
                    if s.get('package') != pkg:
                        continue
                    if s.get('risk_level') in ('CR├ìTICO', 'ALTO'):
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)
                    break
        select_critical_btn.clicked.connect(select_critical)
        buttons_layout.addWidget(select_critical_btn)
        buttons_layout.addStretch()
        remove_btn = QPushButton('­ƒùæ´©Å Remover Selecionados')
        remove_btn.setObjectName('remove')
        def remove_selected():
            selected_apps = []
            for i in range(suspects_list.count()):
                item = suspects_list.item(i)
                if item.checkState() == Qt.Checked:
                    selected_apps.append(item.data(Qt.UserRole))
            if not selected_apps:
                QMessageBox.warning(dialog, 'Aviso', 'Nenhum aplicativo selecionado!')
                return
            confirm = QMessageBox.question(dialog, 'Confirmar Remo├º├úo', f'Deseja remover {len(selected_apps)} aplicativo(s) selecionado(s)?\n\n' + '\n'.join([f'ÔÇó {app}' for app in selected_apps[:10]]) + (f'\n... e mais {len(selected_apps) - 10}' if len(selected_apps) > 10 else ''), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if confirm == QMessageBox.Yes:
                dialog.accept()
                self.remove_selected_apps(selected_apps)
        remove_btn.clicked.connect(remove_selected)
        buttons_layout.addWidget(remove_btn)
        close_btn = QPushButton('Fechar')
        close_btn.clicked.connect(dialog.accept)
        buttons_layout.addWidget(close_btn)
        layout.addLayout(buttons_layout)
        dialog.exec_()
# WARNING: Decompyle incomplete
