'''
XIAOMI SIDELOAD TOOLS
=====================
TECH UNION SOLUTIONS
Ferramentas para opera├º├Áes em modo Sideload do Recovery:
- Remo├º├úo de Mi Account e FRP
- Factory Reset (Hard Reset)
- Wipe Cache/Dalvik
'''
import os
import sys
import subprocess
import ctypes
import re
import tempfile
from typing import (Dict, List, Optional, Tuple)
from dataclasses import dataclass
from enum import Enum
if sys.platform == 'win32':
    ctypes.windll.kernel32.SetErrorMode(32769)
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFrame, QGroupBox, QProgressBar, QMessageBox, QScrollArea, QSizePolicy, QApplication, QMainWindow, QGridLayout, QComboBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import (Qt, QThread, pyqtSignal, QTimer)
from PyQt5.QtGui import QFont, QTextCursor
class Cores:
    '''Paleta de cores padronizada'''
    LARANJA_PRINCIPAL = '#FF6900'
    LARANJA_ESCURO = '#E55A00'
    FUNDO_BRANCO = '#ffffff'
    FUNDO_CLARO = '#f5f5f5'
    FUNDO_CARD = '#fafafa'
    TEXTO_ESCURO = '#333333'
    TEXTO_CINZA = '#666666'
    BORDA = '#dddddd'
    AVISO_AMARELO = '#FFA500'
    ERRO_VERMELHO = '#E53935'
    SUCESSO_VERDE = '#43A047'
class OperationType(Enum):
    '''Tipo de opera├º├úo'''
    MI_BYPASS = 'mi_bypass'
    FORMAT_DATA = 'format_data'
    FACTORY_RESET = 'factory_reset'
    WIPE_CACHE = 'wipe_cache'
    REBOOT_BOOTLOADER = 'reboot_bootloader'
    REBOOT_RECOVERY = 'reboot_recovery'
class BypassStatus(Enum):
    '''Status do processo'''
    AGUARDANDO = 'aguardando'
    DETECTANDO = 'detectando'
    COMPATIVEL = 'compativel'
    INCOMPATIVEL = 'incompativel'
    PROCESSANDO = 'processando'
    SUCESSO = 'sucesso'
    ERRO = 'erro'
@dataclass
class DeviceConfig:
    '''Configura├º├úo de parti├º├Áes por dispositivo'''
    codename: str
    modelo: str
    modem_source: str
    modem_dest: str
    persist_dest: str
    frp_dest: str
DISPOSITIVOS_SUPORTADOS: Dict[str, DeviceConfig] = {'agate': DeviceConfig('agate', 'Xiaomi 11T', 'md1img_a', '/dev/block/sdc19', '/dev/block/sdc14', '/dev/block/sdc4'), 'alioth': DeviceConfig('alioth', 'POCO F3', 'modem_a', '/dev/block/sde5', '/dev/block/sda22', '/dev/block/sda9'), 'apollo': DeviceConfig('apollo', 'Mi 10T/10T Pro/K30S', 'modem', '/dev/block/sde51', '/dev/block/sda22', '/dev/block/sda9'), 'cmi': DeviceConfig('cmi', 'Mi 10 Pro', 'modem', '/dev/block/sde51', '/dev/block/sda22', '/dev/block/sda9'), 'courbet': DeviceConfig('courbet', 'Mi 11 Lite 4G', 'modem', '/dev/block/sde52', '/dev/block/sdf7', '/dev/block/sda9'), 'curtana': DeviceConfig('curtana', 'Note 9S/Note 9 Pro/Note 10 Lite', 'modem', '/dev/block/sde4', '/dev/block/sda2', '/dev/block/sda5'), 'davinci': DeviceConfig('davinci', 'Redmi K20 / Mi 9T', 'modem', '/dev/block/sde51', '/dev/block/sdf7', '/dev/block/sda9'), 'excalibur': DeviceConfig('excalibur', 'Redmi Note 9 Pro Max', 'modem', '/dev/block/sde4', '/dev/block/sda2', '/dev/block/sda5'), 'fog': DeviceConfig('fog', 'Redmi 10C', 'modem_a', '/dev/block/sde4', '/dev/block/sda2', '/dev/block/sda6'), 'gauguin': DeviceConfig('gauguin', 'Mi 10T Lite / Mi 10i', 'modem', '/dev/block/sde48', '/dev/block/sda23', '/dev/block/sda9'), 'ginkgo': DeviceConfig('ginkgo', 'Redmi Note 8 / 8T', 'modem', '/dev/block/mmcblk0p80', '/dev/block/mmcblk0p69', '/dev/block/mmcblk0p30'), 'gram': DeviceConfig('gram', 'POCO M2 Pro', 'modem', '/dev/block/sde4', '/dev/block/sda2', '/dev/block/sda5'), 'joyeuse': DeviceConfig('joyeuse', 'Redmi Note 9 Pro', 'modem', '/dev/block/sde4', '/dev/block/sda2', '/dev/block/sda5'), 'lime': DeviceConfig('lime', 'Redmi Note 9 4G/9T/9 Power', 'modem', '/dev/block/sde52', '/dev/block/sda7', '/dev/block/sda4'), 'lisa': DeviceConfig('lisa', 'Mi 11 LE / Xiaomi 11 Lite 5G', 'modem_a', '/dev/block/sde4', '/dev/block/sda8', '/dev/block/sda14'), 'mojito': DeviceConfig('mojito', 'Redmi Note 10', 'modem_a', '/dev/block/sde4', '/dev/block/sda2', '/dev/block/sda6'), 'phoenixin': DeviceConfig('phoenixin', 'POCO X2', 'modem', '/dev/block/sde52', '/dev/block/sdf7', '/dev/block/sda9'), 'raphael': DeviceConfig('raphael', 'Redmi K20 Pro / Mi 9T Pro', 'modem', '/dev/block/sde52', '/dev/block/sda23', '/dev/block/sda9'), 'renoir': DeviceConfig('renoir', 'Mi 11 Lite 5G', 'modem_a', '/dev/block/sde4', '/dev/block/sda8', '/dev/block/sda14'), 'rosemary': DeviceConfig('rosemary', 'Redmi Note 10S / POCO M5S', 'md1img_a', '/dev/block/sdc26', '/dev/block/sdc21', '/dev/block/sdc10'), 'spes': DeviceConfig('spes', 'Redmi Note 11', 'modem_a', '/dev/block/sde4', '/dev/block/sda2', '/dev/block/sda6'), 'spesn': DeviceConfig('spesn', 'Redmi Note 11 NFC', 'modem_a', '/dev/block/sde4', '/dev/block/sda2', '/dev/block/sda6'), 'Star': DeviceConfig('Star', 'Redmi Note 11 Pro', 'modem_a', '/dev/block/sde5', '/dev/block/sda21', '/dev/block/sda9'), 'sunny': DeviceConfig('sunny', 'Redmi Note 10', 'modem_a', '/dev/block/sde4', '/dev/block/sda2', '/dev/block/sda6'), 'surya': DeviceConfig('surya', 'POCO X3 NFC', 'modem', '/dev/block/sde4', '/dev/block/sda2', '/dev/block/sda5'), 'sweet': DeviceConfig('sweet', 'Redmi Note 10 Pro', 'modem', '/dev/block/sde52', '/dev/block/sdf7', '/dev/block/sda9'), 'sweetin': DeviceConfig('sweetin', 'Redmi Note 10 Pro / Pro Max', 'modem', '/dev/block/sde52', '/dev/block/sdf7', '/dev/block/sda9'), 'toco': DeviceConfig('toco', 'Mi Note 10 Lite', 'modem', '/dev/block/sde52', '/dev/block/sdf7', '/dev/block/sda9'), 'umi': DeviceConfig('umi', 'Mi 10', 'modem', '/dev/block/sde51', '/dev/block/sda22', '/dev/block/sda9'), 'vayu': DeviceConfig('vayu', 'POCO X3 Pro', 'modem', '/dev/block/sde52', '/dev/block/sdf7', '/dev/block/sda9'), 'veux': DeviceConfig('veux', 'Note 11 Pro 5G', 'modem_a', '/dev/block/sde4', '/dev/block/sda11', '/dev/block/sda5'), 'vili': DeviceConfig('vili', 'Xiaomi 11T Pro', 'modem_a', '/dev/block/sde5', '/dev/block/sda21', '/dev/block/sda9'), 'zeus': DeviceConfig('zeus', 'Xiaomi 12 Pro', 'md1img_a', '/dev/block/sde7', '/dev/block/sda21', '/dev/block/sda9')}
class SideloadWorker(QThread):
    '''Worker thread para opera├º├Áes em sideload'''
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, tools_dir: str, operation: OperationType, device_config: Optional[DeviceConfig]=None):
        super().__init__()
        self.tools_dir = tools_dir
        self.operation = operation
        self.device_config = device_config
        self.adb_path = os.path.join(tools_dir, 'adb.exe')
        self.replace_path = os.path.join(tools_dir, 'replace.exe')
        self.frp_path = os.path.join(tools_dir, 'frp')
        self._cancelled = False
        self.temp_dir = tempfile.mkdtemp(prefix='sideload_')
    def cancel(self):
        self._cancelled = True
    def _run_adb(self, args: List[str], timeout: int=60) -> Tuple[bool, str]:
        '''Executa comando ADB'''
        cmd = [self.adb_path] + args
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=self.tools_dir, creationflags=subprocess.CREATE_NO_WINDOW)
            output = result.stdout + result.stderr
            return result.returncode == 0, output.strip()
        except subprocess.TimeoutExpired:
            return (False, 'Timeout na opera├º├úo')
        except Exception:
            return (False, 'Falha na execu├º├úo')
    def _run_replace(self, file_path: str, search: str, replace: str) -> bool:
        '''Executa replace.exe para patching'''
        cmd = [self.replace_path, file_path, search, replace]
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=30, cwd=self.temp_dir, creationflags=subprocess.CREATE_NO_WINDOW)
            return result.returncode == 0
        except:
            return False
    def run(self):
        '''Executa a opera├º├úo selecionada'''
        if self.operation == OperationType.MI_BYPASS:
            self._run_mi_bypass()
            return
        if self.operation == OperationType.FORMAT_DATA:
            self._run_format_data()
            return
        if self.operation == OperationType.FACTORY_RESET:
            self._run_factory_reset()
            return
        if self.operation == OperationType.WIPE_CACHE:
            self._run_wipe_cache()
            return
        if self.operation == OperationType.REBOOT_BOOTLOADER:
            self._run_reboot('bootloader')
            return
        if self.operation == OperationType.REBOOT_RECOVERY:
            self._run_reboot('recovery')
    def _run_format_data(self):
        '''Executa format-data (limpa apps/config, preserva fotos/arquivos)'''
        try:
            self.progress_signal.emit(20)
            self.log_signal.emit('­ƒùæ´©Å Formatando dispositivo...')
            self.log_signal.emit('   (Apaga todos os dados do usu├írio)')
            self.status_signal.emit('Formatando...')
            success, output = self._run_adb(['format-data'], timeout=120)
            self.progress_signal.emit(80)
            if success or 'success' in output.lower():
                self.log_signal.emit('Ô£à Formata├º├úo conclu├¡da')
                self.log_signal.emit('­ƒöä Reiniciando dispositivo...')
                self._run_adb(['reboot'], timeout=10)
                self.progress_signal.emit(100)
                self.finished_signal.emit(True, 'Dispositivo formatado com sucesso!')
                return
            self.log_signal.emit('ÔØî Falha na formata├º├úo')
            self.log_signal.emit('   Tente novamente ou use Factory Reset')
            self.finished_signal.emit(False, 'Falha na formata├º├úo')
            return
        except Exception as e:
            self.finished_signal.emit(False, 'Erro na opera├º├úo')
    def _run_factory_reset(self):
        '''Executa factory reset via sideload'''
        try:
            self.progress_signal.emit(20)
            self.log_signal.emit('­ƒùæ´©Å Iniciando Factory Reset...')
            self.status_signal.emit('Executando wipe...')
            success, output = self._run_adb(['shell', 'recovery', '--wipe_data'], timeout=120)
            if not success:
                success, output = self._run_adb(['shell', 'wipe', 'data'], timeout=120)
            self.progress_signal.emit(80)
            if success:
                self.log_signal.emit('Ô£à Factory Reset executado')
                self.log_signal.emit('­ƒöä Reiniciando dispositivo...')
                self._run_adb(['reboot'], timeout=10)
                self.progress_signal.emit(100)
                self.finished_signal.emit(True, 'Factory Reset conclu├¡do!')
                return
            self.log_signal.emit('ÔÜá´©Å Este m├®todo n├úo funcionou neste dispositivo')
            self.log_signal.emit("   Use a op├º├úo 'Formatar Dispositivo' em vez disso")
            self.finished_signal.emit(False, "Use 'Formatar Dispositivo' para este modelo")
            return
        except Exception as e:
            self.finished_signal.emit(False, 'Erro na opera├º├úo')
    def _run_wipe_cache(self):
        '''Executa wipe cache via sideload'''
        try:
            self.progress_signal.emit(20)
            self.log_signal.emit('­ƒº╣ Limpando Cache...')
            self.status_signal.emit('Limpando cache...')
            success, output = self._run_adb(['shell', 'recovery', '--wipe_cache'], timeout=60)
            self.progress_signal.emit(80)
            if success:
                self.log_signal.emit('Ô£à Cache limpo com sucesso')
                self.log_signal.emit('­ƒöä Reiniciando dispositivo...')
                self._run_adb(['reboot'], timeout=10)
                self.progress_signal.emit(100)
                self.finished_signal.emit(True, 'Wipe Cache conclu├¡do!')
                return
            self.log_signal.emit('ÔÜá´©Å Comando n├úo suportado neste recovery')
            self.finished_signal.emit(False, 'Wipe Cache n├úo dispon├¡vel')
            return
        except Exception as e:
            self.finished_signal.emit(False, 'Erro na opera├º├úo')
    def _run_reboot(self, mode: str):
        '''Reinicia para modo espec├¡fico'''
        try:
            self.progress_signal.emit(50)
            self.log_signal.emit(f'­ƒöä Reiniciando para {mode}...')
            self.status_signal.emit('Reiniciando...')
            success, _ = self._run_adb(['reboot', mode], timeout=15)
            self.progress_signal.emit(100)
            self.log_signal.emit('Ô£à Comando enviado')
            self.finished_signal.emit(True, f'Reiniciando para {mode}')
            return
        except Exception as e:
            self.finished_signal.emit(False, 'Erro na opera├º├úo')
    def _run_mi_bypass(self):
        '''Executa bypass de Mi Account'''
        try:
            if not self.device_config:
                self.finished_signal.emit(False, 'Configura├º├úo do dispositivo n├úo encontrada')
                return
            cfg = self.device_config
            modem_file = cfg.modem_source
            modem_local = os.path.join(self.temp_dir, modem_file)
            persist_local = os.path.join(self.temp_dir, 'persist')
            self.progress_signal.emit(10)
            self.log_signal.emit('­ƒôÑ Extraindo parti├º├úo persist...')
            self.status_signal.emit('Extraindo dados...')
            success, _ = self._run_adb(['pull', '/dev/block/by-name/persist', persist_local], timeout=120)
            if not success or self._cancelled:
                self.log_signal.emit('   ÔØî Acesso negado ├ás parti├º├Áes')
                self.log_signal.emit('')
                self.log_signal.emit('ÔÜá´©Å PATCH DE SEGURAN├çA N├âO SUPORTADO')
                self.log_signal.emit('   Este dispositivo possui prote├º├úo contra')
                self.log_signal.emit('   acesso direto ├ás parti├º├Áes.')
                self.log_signal.emit('')
                self.log_signal.emit('­ƒÆí Recomenda├º├úo: Use AUTH ou outro m├®todo')
                self.finished_signal.emit(False, 'Patch de seguran├ºa n├úo suportado - Requer AUTH')
                return
            self.log_signal.emit('   Ô£à Persist extra├¡do')
            self.progress_signal.emit(25)
            self.log_signal.emit(f'­ƒôÑ Extraindo parti├º├úo {modem_file}...')
            success, _ = self._run_adb(['pull', f'/dev/block/by-name/{modem_file}', modem_local], timeout=180)
            if not success or self._cancelled:
                self.log_signal.emit('   ÔØî Acesso negado ├ás parti├º├Áes')
                self.log_signal.emit('')
                self.log_signal.emit('ÔÜá´©Å PATCH DE SEGURAN├çA N├âO SUPORTADO')
                self.log_signal.emit('   Use AUTH ou outro m├®todo')
                self.finished_signal.emit(False, 'Patch de seguran├ºa n├úo suportado - Requer AUTH')
                return
            self.log_signal.emit(f'   Ô£à {modem_file} extra├¡do')
            self.progress_signal.emit(40)
            self.log_signal.emit('­ƒöº Aplicando patches...')
            self.status_signal.emit('Aplicando patches...')
            self._run_replace(modem_local, 'CARDAPP MDT', 'CARDAPP RNX')
            self._run_replace(modem_local, '#*#cardapp#*#*', '#*#.......#*#*')
            self._run_replace(persist_local, 'fdsd', 'frnx')
            self.log_signal.emit('   Ô£à Patches aplicados')
            self.progress_signal.emit(60)
            self.log_signal.emit('­ƒôñ Gravando parti├º├Áes...')
            self.status_signal.emit('Gravando...')
            success, _ = self._run_adb(['push', modem_local, cfg.modem_dest], timeout=180)
            if not success or self._cancelled:
                self.log_signal.emit('   ÔØî Falha na grava├º├úo')
                self.log_signal.emit('   Dispositivo pode estar protegido')
                self.finished_signal.emit(False, 'Falha na grava├º├úo - Requer AUTH')
                return
            self.progress_signal.emit(75)
            success, _ = self._run_adb(['push', persist_local, cfg.persist_dest], timeout=120)
            if not success or self._cancelled:
                self.log_signal.emit('   ÔØî Falha na grava├º├úo')
                self.finished_signal.emit(False, 'Falha na grava├º├úo - Requer AUTH')
                return
            self.progress_signal.emit(85)
            self.log_signal.emit('­ƒùæ´©Å Limpando FRP...')
            self._run_adb(['push', self.frp_path, cfg.frp_dest], timeout=60)
            self.progress_signal.emit(95)
            self.log_signal.emit('­ƒöä Reiniciando...')
            self._run_adb(['reboot'], timeout=10)
            self._run_adb(['kill-server'], timeout=5)
            self.progress_signal.emit(100)
            self.log_signal.emit('')
            self.log_signal.emit('==================================================')
            self.log_signal.emit('Ô£à OPERA├ç├âO CONCLU├ìDA COM SUCESSO!')
            self.log_signal.emit('==================================================')
            try:
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except:
                pass
            else:
                self.finished_signal.emit(True, 'Mi Account/FRP removido com sucesso!')
        except Exception:
            self.finished_signal.emit(False, 'Falha na opera├º├úo de bypass')
class XiaomiSideloadWidget(QWidget):
    '''Widget para opera├º├Áes Xiaomi via Sideload'''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tools_dir = os.path.join(os.path.dirname(__file__), 'tools')
        self._sideload_dir = self._resolve_sideload_dir()
        self.adb_path = os.path.join(self._sideload_dir, 'adb.exe')
        self.worker = None
        self.device_info = {}
        self.device_config = None
        self.status = BypassStatus.AGUARDANDO
        self.operation = OperationType.MI_BYPASS
        self.setup_ui()
        self.verify_tools()
    def _resolve_sideload_dir(self) -> str:
        try:
            from app.utils.path_manager import PathManager
            sd = PathManager.get_sideload_dir()
            if sd:
                required = ['adb.exe', 'replace.exe', 'frp']
                if all((os.path.isfile(os.path.join(sd, f)) for f in required)):
                    return sd
        except Exception:
            pass
        return self.tools_dir
    def setup_ui(self):
        '''Configura a interface'''
        self.setStyleSheet(f'background-color: {Cores.FUNDO_BRANCO};')
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        header = self._create_header()
        main_layout.addWidget(header)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)
        left_panel = self._create_left_panel()
        content_layout.addWidget(left_panel, stretch=4)
        right_panel = self._create_log_panel()
        content_layout.addWidget(right_panel, stretch=6)
        main_layout.addLayout(content_layout)
        action_bar = self._create_action_bar()
        main_layout.addWidget(action_bar)
    def _create_header(self) -> QFrame:
        '''Cria o header'''
        header = QFrame()
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header.setMinimumHeight(50)
        header.setStyleSheet(f'\n            QFrame {{\n                background-color: {Cores.LARANJA_PRINCIPAL};\n                border-radius: 8px;\n            }}\n        ')
        layout = QHBoxLayout(header)
        layout.setContentsMargins(15, 10, 15, 10)
        title = QLabel('XIAOMI SIDELOAD TOOLS')
        title.setStyleSheet(f'\n            color: {Cores.FUNDO_BRANCO};\n            font-size: 16px;\n            font-weight: bold;\n        ')
        layout.addWidget(title)
        layout.addStretch()
        subtitle = QLabel('Recovery Mode Operations')
        subtitle.setStyleSheet('color: rgba(255,255,255,0.8); font-size: 11px;')
        layout.addWidget(subtitle)
        return header
    def _create_left_panel(self) -> QScrollArea:
        '''Cria o painel esquerdo com scroll'''
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f'\n            QScrollArea {{\n                background-color: {Cores.FUNDO_CARD};\n                border: 1px solid {Cores.BORDA};\n                border-radius: 8px;\n            }}\n            QScrollBar:vertical {{\n                background: {Cores.FUNDO_BRANCO};\n                width: 8px;\n                border-radius: 4px;\n            }}\n            QScrollBar::handle:vertical {{\n                background: {Cores.LARANJA_PRINCIPAL};\n                border-radius: 4px;\n                min-height: 20px;\n            }}\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{\n                height: 0px;\n            }}\n        ')
        panel = QWidget()
        panel.setStyleSheet(f'background-color: {Cores.FUNDO_CARD};')
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        op_group = QGroupBox('OPERACAO')
        op_group.setStyleSheet(f'\n            QGroupBox {{\n                color: {Cores.TEXTO_ESCURO};\n                font-weight: bold;\n                border: 1px solid {Cores.BORDA};\n                border-radius: 5px;\n                margin-top: 10px;\n                padding-top: 10px;\n                background: {Cores.FUNDO_BRANCO};\n            }}\n            QGroupBox::title {{\n                subcontrol-origin: margin;\n                left: 10px;\n                padding: 0 5px;\n            }}\n        ')
        op_layout = QVBoxLayout(op_group)
        self.op_group = QButtonGroup(self)
        radio_style = f'\n            QRadioButton {{\n                color: {Cores.TEXTO_ESCURO};\n                font-size: 11px;\n                padding: 5px;\n            }}\n            QRadioButton::indicator {{\n                width: 14px;\n                height: 14px;\n            }}\n        '
        self.radio_bypass = QRadioButton('Remover Mi Account / FRP')
        self.radio_bypass.setStyleSheet(radio_style)
        self.radio_bypass.setChecked(True)
        self.radio_bypass.toggled.connect((lambda checked: None))
        self.op_group.addButton(self.radio_bypass)
        op_layout.addWidget(self.radio_bypass)
        self.radio_format = QRadioButton('Formatar Dispositivo (apaga tudo)')
        self.radio_format.setStyleSheet(radio_style)
        self.radio_format.toggled.connect((lambda checked: None))
        self.op_group.addButton(self.radio_format)
        op_layout.addWidget(self.radio_format)
        self.radio_reset = QRadioButton('Factory Reset (alternativo)')
        self.radio_reset.setStyleSheet(radio_style)
        self.radio_reset.toggled.connect((lambda checked: None))
        self.op_group.addButton(self.radio_reset)
        op_layout.addWidget(self.radio_reset)
        self.radio_cache = QRadioButton('Limpar Cache / Dalvik')
        self.radio_cache.setStyleSheet(radio_style)
        self.radio_cache.toggled.connect((lambda checked: None))
        self.op_group.addButton(self.radio_cache)
        op_layout.addWidget(self.radio_cache)
        self.radio_bootloader = QRadioButton('Reiniciar ÔåÆ Bootloader')
        self.radio_bootloader.setStyleSheet(radio_style)
        self.radio_bootloader.toggled.connect((lambda checked: None))
        self.op_group.addButton(self.radio_bootloader)
        op_layout.addWidget(self.radio_bootloader)
        self.radio_recovery = QRadioButton('Reiniciar ÔåÆ Recovery')
        self.radio_recovery.setStyleSheet(radio_style)
        self.radio_recovery.toggled.connect((lambda checked: None))
        self.op_group.addButton(self.radio_recovery)
        op_layout.addWidget(self.radio_recovery)
        layout.addWidget(op_group)
        device_group = QGroupBox('DISPOSITIVO')
        device_group.setStyleSheet(f'\n            QGroupBox {{\n                color: {Cores.TEXTO_ESCURO};\n                font-weight: bold;\n                border: 1px solid {Cores.BORDA};\n                border-radius: 5px;\n                margin-top: 10px;\n                padding-top: 10px;\n                background: {Cores.FUNDO_BRANCO};\n            }}\n            QGroupBox::title {{\n                subcontrol-origin: margin;\n                left: 10px;\n                padding: 0 5px;\n            }}\n        ')
        device_layout = QVBoxLayout(device_group)
        label_style = f'color: {Cores.TEXTO_CINZA}; font-size: 11px;'
        self.lbl_modelo = QLabel('Modelo: Aguardando...')
        self.lbl_modelo.setStyleSheet(label_style)
        device_layout.addWidget(self.lbl_modelo)
        self.lbl_codename = QLabel('Codename: --')
        self.lbl_codename.setStyleSheet(label_style)
        device_layout.addWidget(self.lbl_codename)
        self.lbl_android = QLabel('Android: --')
        self.lbl_android.setStyleSheet(label_style)
        device_layout.addWidget(self.lbl_android)
        self.lbl_serial = QLabel('Serial: --')
        self.lbl_serial.setStyleSheet(label_style)
        device_layout.addWidget(self.lbl_serial)
        self.lbl_status = QLabel('Status: Nao conectado')
        self.lbl_status.setStyleSheet(f'color: {Cores.TEXTO_CINZA}; font-size: 11px; font-weight: bold;')
        device_layout.addWidget(self.lbl_status)
        self.btn_detect = QPushButton('Detectar Dispositivo')
        self.btn_detect.setStyleSheet(f'\n            QPushButton {{\n                background-color: {Cores.LARANJA_PRINCIPAL};\n                color: white;\n                border: none;\n                padding: 10px;\n                border-radius: 5px;\n                font-weight: bold;\n            }}\n            QPushButton:hover {{\n                background-color: {Cores.LARANJA_ESCURO};\n            }}\n            QPushButton:disabled {{\n                background-color: #cccccc;\n            }}\n        ')
        self.btn_detect.clicked.connect(self.detect_device)
        device_layout.addWidget(self.btn_detect)
        layout.addWidget(device_group)
        self.bypass_notice = QFrame()
        self.bypass_notice.setStyleSheet(f'\n            QFrame {{\n                background-color: #FFF3E0;\n                border: 1px solid {Cores.AVISO_AMARELO};\n                border-radius: 5px;\n                padding: 5px;\n            }}\n        ')
        notice_layout = QVBoxLayout(self.bypass_notice)
        notice_layout.setContentsMargins(8, 8, 8, 8)
        notice_text = QLabel('Mi Account/FRP: Funciona em patches de seguranca especificos. Se nao funcionar, o dispositivo requer AUTH (servico pago).')
        notice_text.setStyleSheet(f'color: {Cores.TEXTO_ESCURO}; font-size: 10px;')
        notice_text.setWordWrap(True)
        notice_layout.addWidget(notice_text)
        layout.addWidget(self.bypass_notice)
        layout.addStretch()
        scroll.setWidget(panel)
        return scroll
    def _create_log_panel(self) -> QFrame:
        '''Cria o painel de logs'''
        panel = QFrame()
        panel.setStyleSheet(f'\n            QFrame {{\n                background-color: {Cores.FUNDO_CARD};\n                border: 1px solid {Cores.BORDA};\n                border-radius: 8px;\n            }}\n        ')
        layout = QVBoxLayout(panel)
        header = QLabel('LOG DE OPERACOES')
        header.setStyleSheet(f'\n            color: {Cores.TEXTO_ESCURO};\n            font-weight: bold;\n            font-size: 12px;\n            padding: 5px;\n        ')
        layout.addWidget(header)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet(f"\n            QTextEdit {{\n                background-color: {Cores.FUNDO_BRANCO};\n                color: {Cores.TEXTO_ESCURO};\n                font-family: 'Consolas', 'Courier New', monospace;\n                font-size: 11px;\n                border: 1px solid {Cores.BORDA};\n                border-radius: 5px;\n            }}\n        ")
        layout.addWidget(self.log_area)
        self._log_welcome()
        return panel
    def _create_action_bar(self) -> QFrame:
        '''Cria a barra de a├º├Áes'''
        bar = QFrame()
        bar.setStyleSheet(f'\n            QFrame {{\n                background-color: {Cores.FUNDO_CARD};\n                border: 1px solid {Cores.BORDA};\n                border-radius: 8px;\n                padding: 10px;\n            }}\n        ')
        layout = QHBoxLayout(bar)
        self.progress = QProgressBar()
        self.progress.setStyleSheet(f'\n            QProgressBar {{\n                border: 1px solid {Cores.BORDA};\n                border-radius: 5px;\n                text-align: center;\n                color: {Cores.TEXTO_ESCURO};\n                background-color: {Cores.FUNDO_BRANCO};\n            }}\n            QProgressBar::chunk {{\n                background-color: {Cores.LARANJA_PRINCIPAL};\n                border-radius: 4px;\n            }}\n        ')
        self.progress.setMinimumHeight(25)
        layout.addWidget(self.progress, stretch=6)
        self.btn_cancel = QPushButton('Cancelar')
        self.btn_cancel.setStyleSheet('\n            QPushButton {\n                background-color: #999999;\n                color: white;\n                border: none;\n                padding: 10px 20px;\n                border-radius: 5px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #888888;\n            }\n            QPushButton:disabled {\n                background-color: #cccccc;\n            }\n        ')
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_operation)
        layout.addWidget(self.btn_cancel)
        self.btn_start = QPushButton('EXECUTAR')
        self.btn_start.setStyleSheet(f'\n            QPushButton {{\n                background-color: {Cores.SUCESSO_VERDE};\n                color: white;\n                border: none;\n                padding: 10px 30px;\n                border-radius: 5px;\n                font-weight: bold;\n                font-size: 14px;\n            }}\n            QPushButton:hover {{\n                background-color: #388E3C;\n            }}\n            QPushButton:disabled {{\n                background-color: #cccccc;\n            }}\n        ')
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.start_operation)
        layout.addWidget(self.btn_start)
        return bar
    def _on_operation_changed(self, operation: OperationType):
        '''Quando muda a opera├º├úo selecionada'''
        self.operation = operation
        if operation == OperationType.MI_BYPASS:
            self.bypass_notice.setVisible(True)
            if self.device_config:
                self.btn_start.setEnabled(True)
                return
            self.btn_start.setEnabled(False)
            return
        self.bypass_notice.setVisible(False)
        if self.device_info.get('connected'):
            self.btn_start.setEnabled(True)
    def _log_welcome(self):
        '''Mensagem de boas-vindas'''
        self.log_area.clear()
        self.log(f'{'======================================================='}')
        self.log('  Ôÿü´©Å XIAOMI SIDELOAD TOOLS')
        self.log('  TECH UNION SOLUTIONS')
        self.log(f'{'======================================================='}')
        self.log('')
        self.log('­ƒô▒ Opera├º├Áes dispon├¡veis via Recovery Sideload:')
        self.log('   ÔÇó Remo├º├úo de Mi Account / FRP')
        self.log('   ÔÇó Factory Reset (Hard Reset)')
        self.log('   ÔÇó Limpar Cache / Dalvik')
        self.log('')
        self.log('-------------------------------------------------------')
    def log(self, message: str):
        '''Adiciona mensagem ao log'''
        self.log_area.append(message)
        self.log_area.moveCursor(QTextCursor.End)
    def _sanitize_tools_dir(self):
        '''Remove DLLs n├úo autorizadas da pasta tools (preven├º├úo contra malware dropper)'''
        allowed_dlls = {'adbwinapi.dll', 'adbwinusbapi.dll'}
        cleaned = False
        try:
            for f in os.listdir(self.tools_dir):
                if not f.lower().endswith('.dll'):
                    continue
                if f.lower() not in allowed_dlls:
                    try:
                        try:
                            os.remove(os.path.join(self.tools_dir, f))
                            cleaned = True
                        except Exception:
                            continue
                    except Exception:
                        break
        except Exception:
            pass
        if cleaned:
            self.log('­ƒøí´©Å Verifica├º├úo de seguran├ºa conclu├¡da - sistema pronto para uso')
    def verify_tools(self):
        '''Verifica integridade das ferramentas com auto-restaura├º├úo'''
        self._sanitize_tools_dir()
        tools_ok = True
        backup_zip = os.path.join(self.tools_dir, 'tools_backup.zip')
        required_tools = ['adb.exe', 'replace.exe', 'frp']
        for tool in required_tools:
            tool_path = os.path.join(self._sideload_dir, tool)
            if os.path.exists(tool_path):
                continue
            tools_ok = False
            break
        if not tools_ok:
            if os.path.exists(backup_zip):
                self.log('­ƒöº Restaurando ferramentas...')
                try:
                    import zipfile
                    with zipfile.ZipFile(backup_zip, 'r') as zf:
                        zf.extractall(self.tools_dir)
                    self._sideload_dir = self._resolve_sideload_dir()
                    self.adb_path = os.path.join(self._sideload_dir, 'adb.exe')
                    self.log('   Ô£à Ferramentas restauradas')
                    tools_ok = True
                except Exception:
                    self.log('   ÔØî Falha na restaura├º├úo')
                    tools_ok = False
            else:
                self.log('ÔØî Ferramentas n├úo dispon├¡veis')
                self.btn_detect.setEnabled(False)
                return False
        if tools_ok:
            try:
                result = subprocess.run([self.adb_path, 'version'], capture_output=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode != 0:
                    raise Exception()
                self.log('Ô£à Ferramentas verificadas')
            except Exception:
                if os.path.exists(backup_zip):
                    self.log('­ƒöº ADB corrompido, restaurando...')
                    try:
                        os.remove(self.adb_path)
                    except Exception:
                        pass
                    try:
                        import zipfile
                        with zipfile.ZipFile(backup_zip, 'r') as zf:
                            zf.extractall(self.tools_dir)
                    except Exception:
                        self.log('   ÔØî Falha na restaura├º├úo')
                        self.btn_detect.setEnabled(False)
                        return False
                    if not None:
                        pass
                    try:
                        self._sideload_dir = self._resolve_sideload_dir()
                        self.adb_path = os.path.join(self._sideload_dir, 'adb.exe')
                        self.log('   Ô£à Restaurado com sucesso')
                    except Exception:
                        self.log('   ÔØî Falha na restaura├º├úo')
                        self.btn_detect.setEnabled(False)
                        return False
                    return True
            return True
        return tools_ok
    def detect_device(self):
        '''Detecta dispositivo em sideload'''
        self.log('')
        self.log('=======================================================')
        self.log('­ƒöì DETECTANDO DISPOSITIVO')
        self.log('=======================================================')
        self.btn_detect.setEnabled(False)
        self.device_config = None
        self.btn_start.setEnabled(False)
        try:
            result = subprocess.run([self.adb_path, 'devices'], capture_output=True, text=True, timeout=10, cwd=self._sideload_dir, creationflags=subprocess.CREATE_NO_WINDOW)
            if 'sideload' not in result.stdout.lower() and 'recovery' not in result.stdout.lower():
                self.log('')
                self.log('ÔÜá´©Å Nenhum dispositivo em Sideload/Recovery encontrado!')
                self.log('   Coloque o dispositivo em Recovery > Apply from ADB')
                self.lbl_status.setText('Status: Nao detectado')
                self.lbl_status.setStyleSheet(f'color: {Cores.AVISO_AMARELO}; font-size: 11px; font-weight: bold;')
                self.btn_detect.setEnabled(True)
                self.btn_detect.setEnabled(True)
                return
            self.log('Ô£à Dispositivo detectado!')
            self.device_info['connected'] = True
            self.log('­ƒôï Obtendo informa├º├Áes...')
            def run_cmd(args):
                try:
                    r = subprocess.run([self.adb_path] + args, capture_output=True, text=True, timeout=10, cwd=self._sideload_dir, creationflags=subprocess.CREATE_NO_WINDOW)
                    out = (r.stdout + r.stderr).strip()
                    for line in out.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith('*'):
                            continue
                        if 'daemon' in line.lower():
                            continue
                        if not 'symsrv' not in line.lower():
                            continue
                        return line
                    return ''
                except:
                    return ''
            codename_raw = run_cmd(['getdevice'])
            codename = codename_raw.split('_')[0] if '_' in codename_raw else codename_raw
            android_version = run_cmd(['getcodebase']) or '?'
            serial = run_cmd(['getsn']) or '?'
            miui_version = run_cmd(['getversion']) or ''
            language = run_cmd(['getlanguage']) or ''
            region = run_cmd(['getregion']) or ''
            self.device_info = {'codename': codename, 'android': android_version, 'serial': serial, 'miui': miui_version, 'language': language, 'region': region, 'connected': True}
            self.log(f'   Codename: {codename}')
            self.log(f'   Android: {android_version}')
            if miui_version:
                self.log(f'   MIUI: {miui_version}')
            if region:
                self.log(f'   Regi├úo: {region}')
            if language:
                self.log(f'   Idioma: {language.upper()}')
            serial_display = f'{serial[:12]}...' if len(serial) > 12 else serial
            self.log(f'   Serial: {serial_display}')
            self.lbl_modelo.setText(f'Modelo: {codename}')
            self.lbl_codename.setText(f'Codename: {codename}' + (f' ({region})' if region else ''))
            android_display = f'Android: {android_version}'
            if miui_version:
                android_display += f' | {miui_version}'
            self.lbl_android.setText(android_display)
            self.lbl_serial.setText(f'Serial: {serial_display}')
            self._check_compatibility(codename, android_version)
        except subprocess.TimeoutExpired:
            self.log('ÔØî Timeout ao detectar dispositivo')
            self.lbl_status.setText('Status: Timeout')
            self.lbl_status.setStyleSheet(f'color: {Cores.ERRO_VERMELHO}; font-size: 11px; font-weight: bold;')
        except Exception as e:
            self.log('ÔØî Erro na detec├º├úo')
            self.lbl_status.setText('Status: Erro')
            self.lbl_status.setStyleSheet(f'color: {Cores.ERRO_VERMELHO}; font-size: 11px; font-weight: bold;')
        finally:
            self.btn_detect.setEnabled(True)
    def _check_compatibility(self, codename: str, android_version: str):
        '''Verifica compatibilidade para Mi Bypass'''
        self.log('')
        self.log('­ƒöÄ Verificando compatibilidade...')
        try:
            android_num = int(android_version.split('.')[0]) if android_version else 0
        except:
            android_num = 0
        if self.operation != OperationType.MI_BYPASS:
            self.lbl_status.setText('Status: Pronto')
            self.lbl_status.setStyleSheet(f'color: {Cores.SUCESSO_VERDE}; font-size: 11px; font-weight: bold;')
            self.btn_start.setEnabled(True)
            self.log('Ô£à Dispositivo pronto para opera├º├úo')
            return
        if android_num in (8, 9, 10):
            self.log(f'ÔØî Requer AUTH - Android {android_version} n├úo suportado')
            self.lbl_status.setText('Status: Requer AUTH (servico pago)')
            self.lbl_status.setStyleSheet(f'color: {Cores.ERRO_VERMELHO}; font-size: 11px; font-weight: bold;')
            self.status = BypassStatus.INCOMPATIVEL
            self.btn_start.setEnabled(False)
            return
        if codename in DISPOSITIVOS_SUPORTADOS:
            self.device_config = DISPOSITIVOS_SUPORTADOS[codename]
            self.log('Ô£à Dispositivo compat├¡vel!')
            self.lbl_status.setText('Status: Compativel')
            self.lbl_status.setStyleSheet(f'color: {Cores.SUCESSO_VERDE}; font-size: 11px; font-weight: bold;')
            self.btn_start.setEnabled(True)
            self.status = BypassStatus.COMPATIVEL
            return
        self.log('ÔØî Requer AUTH - Dispositivo n├úo suportado neste m├®todo')
        self.lbl_status.setText('Status: Requer AUTH (servico pago)')
        self.lbl_status.setStyleSheet(f'color: {Cores.ERRO_VERMELHO}; font-size: 11px; font-weight: bold;')
        self.btn_start.setEnabled(False)
        self.status = BypassStatus.INCOMPATIVEL
    def start_operation(self):
        '''Inicia a opera├º├úo selecionada'''
        op_name = {OperationType.MI_BYPASS: 'Remover Mi Account/FRP', OperationType.FORMAT_DATA: 'Formatar Dispositivo', OperationType.FACTORY_RESET: 'Factory Reset', OperationType.WIPE_CACHE: 'Limpar Cache/Dalvik', OperationType.REBOOT_BOOTLOADER: 'Reiniciar ÔåÆ Bootloader', OperationType.REBOOT_RECOVERY: 'Reiniciar ÔåÆ Recovery'}.get(self.operation, 'Opera├º├úo')
        warning_msg = f'Voce esta prestes a executar:\n\n{op_name}\n\n'
        if self.operation == OperationType.MI_BYPASS:
            warning_msg += 'Esta operacao modifica particoes criticas.\nNAO desconecte o cabo USB!'
        elif self.operation == OperationType.FORMAT_DATA:
            warning_msg += 'TODOS os dados serao APAGADOS!\nFotos, apps, contas - tudo sera removido.'
        elif self.operation == OperationType.FACTORY_RESET:
            warning_msg += 'Metodo alternativo de reset.\nPode nao funcionar em alguns dispositivos.'
        elif self.operation == OperationType.WIPE_CACHE:
            warning_msg += 'Limpa arquivos temporarios.\nNao apaga dados pessoais.'
        elif self.operation == OperationType.REBOOT_BOOTLOADER:
            warning_msg += 'Reinicia em modo Fastboot.'
        elif self.operation == OperationType.REBOOT_RECOVERY:
            warning_msg += 'Reinicia em modo Recovery.'
        reply = QMessageBox.warning(self, 'Confirmar Operacao', warning_msg + '\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.log('')
        self.log('=======================================================')
        self.log(f'­ƒÜÇ INICIANDO: {op_name.upper()}')
        self.log('=======================================================')
        self.btn_start.setEnabled(False)
        self.btn_detect.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress.setValue(0)
        self.worker = SideloadWorker(self._sideload_dir, self.operation, self.device_config)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.log_signal.connect(self.log)
        self.worker.status_signal.connect(self._on_status_update)
        self.worker.finished_signal.connect(self._on_operation_finished)
        self.worker.start()
    def _on_status_update(self, status: str):
        '''Atualiza status'''
        self.lbl_status.setText(f'Status: {status}')
    def _on_operation_finished(self, success: bool, message: str):
        '''Callback quando opera├º├úo termina'''
        self.btn_detect.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        if success:
            self.lbl_status.setText('Status: Concluido')
            self.lbl_status.setStyleSheet(f'color: {Cores.SUCESSO_VERDE}; font-size: 11px; font-weight: bold;')
            QMessageBox.information(self, 'Sucesso', message)
            return
        self.log(f'ÔØî {message}')
        self.lbl_status.setText('Status: Falha')
        self.lbl_status.setStyleSheet(f'color: {Cores.ERRO_VERMELHO}; font-size: 11px; font-weight: bold;')
        self.btn_start.setEnabled(True)
        QMessageBox.critical(self, 'Erro', message)
    def cancel_operation(self):
        '''Cancela opera├º├úo'''
        if self.worker:
            if self.worker.isRunning():
                reply = QMessageBox.warning(self, 'Cancelar', 'Cancelar pode causar problemas!\n\nTem certeza?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.worker.cancel()
                    self.log('ÔÜá´©Å Opera├º├úo cancelada')
                    self.btn_cancel.setEnabled(False)
class XiaomiSideloadWindow(QMainWindow):
    '''Janela standalone'''
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Xiaomi Sideload Tools | TECH UNION SOLUTIONS')
        self.setMinimumSize(900, 650)
        central = XiaomiSideloadWidget()
        self.setCentralWidget(central)
        self.setStyleSheet(f'background-color: {Cores.FUNDO_BRANCO};')
MiBypassSideloadWidget = XiaomiSideloadWidget
MiBypassSideloadWindow = XiaomiSideloadWindow
def main():
    '''Fun├º├úo principal'''
    app = QApplication(sys.argv)
    window = XiaomiSideloadWindow()
    window.show()
    sys.exit(app.exec_())
if __name__ == '__main__':
    main()
# WARNING: Decompyle incomplete
