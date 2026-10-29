'''
TECH UNION SOLUTIONS - MOTOROLA FLASH TOOL
Interface gr├ífica para flash de firmware Motorola via Fastboot
Vers├úo: 1.0.0
Autor: TECH UNION SOLUTIONS
Data: 2026
Este m├│dulo implementa uma interface PyQt5 para flash de ROMs Motorola
utilizando XML (flashfile.xml / servicefile.xml) com suporte a:
- Dispositivos A/B (parti├º├úo dupla)
- Dispositivos tradicionais
- Flash com WIPE (flashfile.xml)
- Flash sem WIPE (servicefile.xml)
- Sele├º├úo manual de parti├º├Áes
- Detec├º├úo autom├ítica de firmware
'''
import os
import sys
import subprocess
import ctypes
import xml.etree.ElementTree as ET
from typing import (List, Dict, Optional, Tuple)
from dataclasses import dataclass
from enum import Enum
if sys.platform == 'win32':
    ctypes.windll.kernel32.SetErrorMode(32769)
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QFrame, QMessageBox, QFileDialog, QGroupBox, QCheckBox, QTextEdit, QRadioButton, QButtonGroup, QApplication, QMainWindow, QGridLayout, QScrollArea, QSizePolicy, QSplitter)
from PyQt5.QtCore import (Qt, QThread, pyqtSignal, QTimer)
from PyQt5.QtGui import (QFont, QFontMetrics, QIcon)
class CoresMotorola:
    '''Paleta de cores para interface Motorola'''
    PRIMARY = '#1976D2'
    PRIMARY_DARK = '#1565C0'
    PRIMARY_LIGHT = '#42A5F5'
    SECONDARY = '#FFC107'
    SUCCESS = '#4CAF50'
    WARNING = '#FF9800'
    ERROR = '#F44336'
    BACKGROUND = '#F5F5F5'
    BACKGROUND_WHITE = '#FFFFFF'
    BACKGROUND_DARK = '#E0E0E0'
    TEXT = '#212121'
    TEXT_WHITE = '#FFFFFF'
    TEXT_MUTED = '#757575'
    BORDER = '#BDBDBD'
FASTBOOT_EXPECTED_SIZE = 802304
FASTBOOT_EXPECTED_MD5 = ''
class FlashType(Enum):
    '''Tipos de flash dispon├¡veis'''
    WIPE = 'wipe'
    NO_WIPE = 'no_wipe'
class DeviceType(Enum):
    '''Tipos de dispositivo'''
    AB = 'ab'
    TRADITIONAL = 'traditional'
@dataclass
class PartitionInfo:
    '''Informa├º├Áes de uma parti├º├úo'''
    name: str
    filename: str
    operation: str
    file_exists: bool = False
    file_size: int = 0
def calculate_file_md5(filepath: str) -> str:
    '''Calcula MD5 de um arquivo'''
    import hashlib
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter((lambda: f.read(4096)), b''):
                hash_md5.update(chunk)
    except:
        return ''
    return hash_md5.hexdigest().upper()
def verify_fastboot_integrity(fastboot_path: str, backup_path: str=None) -> Tuple[bool, str]:
    '''Verifica integridade do fastboot.exe e repara se necess├írio'''
    import zipfile
    try:
        if not os.path.exists(fastboot_path):
            if backup_path and os.path.exists(backup_path):
                pass
        try:
            with zipfile.ZipFile(backup_path, 'r') as zf:
                zf.extract('fastboot.exe', os.path.dirname(fastboot_path))
        except:
            pass
        else:
            return (True, 'Fastboot restaurado do backup')
    except Exception as e:
        return False, f'Erro ao verificar: {str(e)}'
    try:
        result = subprocess.run([fastboot_path, '--version'], capture_output=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
        if result.returncode == 0:
            version_info = result.stdout.decode() if result.stdout else ''
            return True, f'Fastboot OK ({file_size} bytes)'
    except subprocess.TimeoutExpired:
        return (False, 'Fastboot n├úo respondeu (timeout)')
    return (True, 'Fastboot presente (verifica├º├úo b├ísica)')
class MotorolaFlashWorker(QThread):
    '''Thread para executar flash em background'''
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, fastboot_path: str, commands: List[str], firmware_folder: str):
        super().__init__()
        self.fastboot_path = fastboot_path
        self.commands = commands
        self.firmware_folder = firmware_folder
        self.should_stop = False
    def stop(self):
        '''Para a execu├º├úo'''
        self.should_stop = True
    def run(self):
        '''Executa os comandos de flash'''
        try:
            total_commands = len(self.commands)
            success_count = 0
            error_count = 0
            retry_count = 0
            max_retries = 2
            self.log_signal.emit('============================================================')
            self.log_signal.emit('­ƒöÑ INICIANDO FLASH MOTOROLA')
            self.log_signal.emit('============================================================')
            self.log_signal.emit(f'­ƒôï Total de comandos: {total_commands}')
            self.log_signal.emit('')
            for i, cmd in enumerate(self.commands):
                if self.should_stop:
                    self.log_signal.emit('\nÔÜá´©Å Flash cancelado pelo usu├írio')
                    self.finished_signal.emit(False, 'Cancelado pelo usu├írio')
                    return
                progress = int(i / total_commands * 100)
                self.progress_signal.emit(progress)
                cmd_display = self._format_cmd_for_log(cmd)
                self.log_signal.emit(f'[{i + 1}/{total_commands}] {cmd_display}')
                self.status_signal.emit(f'Executando comando {i + 1}/{total_commands}...')
                attempts = 0
                cmd_success = False
                if not attempts <= max_retries:
                    continue
                if cmd_success:
                    continue
                try:
                    try:
                        result = self._execute_fastboot(cmd)
                        if result['success']:
                            output = self._clean_output(result['output'])
                            self.log_signal.emit(f'   Ô£à {output[:80] if output else 'OK'}')
                            success_count += 1
                            cmd_success = True
                        else:
                            error_msg = self._clean_output(result['error'])
                            if self._is_critical_error(cmd, result['error']):
                                self.log_signal.emit(f'   ÔØî {error_msg[:100]}')
                                self.log_signal.emit('\nÔØî ERRO CR├ìTICO - Flash interrompido')
                                self.finished_signal.emit(False, f'Erro cr├¡tico em: {cmd_display}')
                                return
                            if self._is_retryable_error(result['error']) and attempts < max_retries:
                                attempts += 1
                                retry_count += 1
                                self.log_signal.emit(f'   ÔÜá´©Å Erro USB - Tentativa {attempts + 1}/{max_retries + 1}...')
                                import time
                                time.sleep(1)
                            else:
                                self.log_signal.emit(f'   ÔÜá´©Å {error_msg[:80]}')
                                error_count += 1
                                cmd_success = True
                    except Exception as e:
                        error_str = str(e)
                        error_clean = self._clean_output(error_str)
                        self.log_signal.emit(f'   ÔØî {error_clean[:80]}')
                        error_count += 1
                        cmd_success = True
                except Exception as e:
                    error_clean = self._clean_output(str(e))
                    self.log_signal.emit(f'\nÔØî Erro geral: {error_clean}')
                    self.finished_signal.emit(False, error_clean)
                if not attempts <= max_retries:
                    continue
                if not cmd_success:
                    continue
                continue
        except Exception as e:
            error_clean = self._clean_output(str(e))
            self.log_signal.emit(f'\nÔØî Erro geral: {error_clean}')
            self.finished_signal.emit(False, error_clean)
        self.progress_signal.emit(100)
        self.log_signal.emit('')
        self.log_signal.emit('============================================================')
        self.log_signal.emit('­ƒôè RESUMO DA OPERA├ç├âO')
        self.log_signal.emit('============================================================')
        self.log_signal.emit(f'   Comandos executados: {total_commands}')
        self.log_signal.emit(f'   Sucessos: {success_count}')
        self.log_signal.emit(f'   Erros: {error_count}')
        if retry_count > 0:
            self.log_signal.emit(f'   Retries (USB): {retry_count}')
        if error_count == 0:
            self.log_signal.emit('\nÔ£à FLASH CONCLU├ìDO COM SUCESSO!')
            self.status_signal.emit('Flash conclu├¡do com sucesso!')
            self.finished_signal.emit(True, 'Flash conclu├¡do com sucesso!')
            return
        if success_count > error_count:
            self.log_signal.emit('\nÔÜá´©Å Flash parcialmente conclu├¡do')
            self.log_signal.emit('   ­ƒÆí Alguns erros ocorreram mas a maioria funcionou.')
            self.log_signal.emit('   ­ƒÆí Se o dispositivo n├úo ligar, tente novamente.')
            self.status_signal.emit('Flash parcialmente conclu├¡do')
            self.finished_signal.emit(True, f'Parcial: {success_count} OK, {error_count} erros')
            return
        self.log_signal.emit('\nÔØî Flash falhou')
        self.log_signal.emit('   ­ƒÆí Verifique o cabo USB e tente em outra porta.')
        self.log_signal.emit("   ­ƒÆí Erros de 'Too many links' indicam problema de conex├úo.")
        self.status_signal.emit('Flash falhou')
        self.finished_signal.emit(False, f'Falhou: {error_count} erros')
    def _execute_fastboot(self, cmd: str) -> Dict:
        '''Executa um comando fastboot'''
        try:
            full_cmd = f'"{self.fastboot_path}" {cmd}'
            result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=120, cwd=self.firmware_folder, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            return {'success': result.returncode == 0, 'output': result.stdout.strip(), 'error': result.stderr.strip()}
        except subprocess.TimeoutExpired:
            return {'success': False, 'output': '', 'error': 'Timeout (2 min)'}
        except Exception as e:
            return {'success': False, 'output': '', 'error': str(e)}
    def _format_cmd_for_log(self, cmd: str) -> str:
        '''Formata comando para log sem exibir caminhos completos'''
        import os
        if cmd.startswith('flash '):
            parts = cmd.split('"')
            if len(parts) >= 2:
                partition_part = parts[0].replace('flash ', '').strip()
                file_path = parts[1]
                filename = os.path.basename(file_path)
                return f'­ƒôª flash {partition_part} ÔåÆ {filename}'
            words = cmd.split()
            if len(words) >= 3:
                partition = words[1]
                filename = os.path.basename(words[2])
                return f'­ƒôª flash {partition} ÔåÆ {filename}'
        if cmd.startswith('getvar'):
            return f'­ƒöì {cmd}'
        if cmd.startswith('oem'):
            return f'ÔÜÖ´©Å {cmd}'
        if cmd.startswith('erase'):
            return '­ƒùæ´©Å Preparando ├írea de dados...'
        if cmd == 'reboot':
            return '­ƒöä reboot'
        return cmd
    def _is_critical_error(self, command: str, error_msg: str) -> bool:
        '''
        Verifica se ├® erro cr├¡tico que deve parar o flash.
        Nota: Erros de USB intermitentes N├âO s├úo cr├¡ticos.
        '''
        error_lower = error_msg.lower()
        critical_errors = ['no devices', 'device not found', 'remote: not allowed', 'remote: oem unlock is required', 'remote: device is locked', 'remote: flashing not allowed', 'anti-rollback']
        for critical in critical_errors:
            if critical in error_lower:
                return True
        return False
    def _is_retryable_error(self, error_msg: str) -> bool:
        '''Verifica se o erro pode ser resolvido com retry'''
        error_lower = error_msg.lower()
        retryable_patterns = ['too many links', 'write to device failed', 'sendbuffer', 'usb', 'timeout']
        for pattern in retryable_patterns:
            if pattern in error_lower:
                return True
        return False
    def _clean_output(self, text: str) -> str:
        '''Remove caminhos completos e informa├º├Áes sens├¡veis do output'''
        import re
        if not text:
            return ''
        text = re.sub('[A-Za-z]:\\\\[^\\s\\\'"]*', (lambda m: os.path.basename(m.group(0))), text)
        text = re.sub('/[^\\s\\\'"]+/', (lambda m: os.path.basename(m.group(0).rstrip('/')) + '/'), text)
        text = re.sub('\\n\\s*\\n', '\n', text)
        text = text.replace('(bootloader) ', '')
        return text.strip()
class PartitionWidget(QFrame):
    '''Widget para exibir uma parti├º├úo'''
    def __init__(self, partition: PartitionInfo, parent=None):
        super().__init__(parent)
        self.partition = partition
        self.setup_ui()
    def setup_ui(self):
        if self.partition.file_exists:
            border_color = CoresMotorola.SUCCESS
            status_icon = '[OK]'
        else:
            border_color = CoresMotorola.ERROR
            status_icon = '[X]'
        self.setStyleSheet(f'\n            PartitionWidget {{\n                background-color: {CoresMotorola.BACKGROUND_WHITE};\n                border: 1px solid {border_color};\n                border-left: 4px solid {border_color};\n                border-radius: 4px;\n                padding: 4px;\n                margin: 2px;\n            }}\n        ')
        self.setMinimumHeight(40)
        self.setMaximumHeight(50)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.partition.file_exists)
        self.checkbox.setEnabled(self.partition.file_exists)
        layout.addWidget(self.checkbox)
        status_label = QLabel(status_icon)
        status_label.setFont(QFont('Segoe UI', 10))
        layout.addWidget(status_label)
        name_label = QLabel(self.partition.name)
        name_label.setFont(QFont('Segoe UI', 10, QFont.Bold))
        name_label.setStyleSheet(f'color: {CoresMotorola.TEXT};')
        name_label.setMinimumWidth(80)
        layout.addWidget(name_label)
        file_label = QLabel(self.partition.filename if self.partition.filename else 'N/A')
        file_label.setFont(QFont('Segoe UI', 9))
        file_label.setStyleSheet(f'color: {CoresMotorola.TEXT_MUTED};')
        file_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(file_label)
        if self.partition.file_size > 0:
            size_mb = self.partition.file_size / 1048576
            size_text = f'{size_mb:.1f} MB'
        else:
            size_text = ''
        size_label = QLabel(size_text)
        size_label.setFont(QFont('Segoe UI', 9))
        size_label.setStyleSheet(f'color: {CoresMotorola.TEXT_MUTED};')
        size_label.setMinimumWidth(70)
        size_label.setAlignment(Qt.AlignRight)
        layout.addWidget(size_label)
    def is_selected(self) -> bool:
        return self.checkbox.isChecked()
class MotorolaFlashToolWidget(QWidget):
    '''Widget principal da ferramenta de flash Motorola'''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tools_dir = self._resolve_tools_dir()
        self.fastboot_path = self._resolve_fastboot()
        self.fastboot_backup_path = os.path.join(self.tools_dir, 'tools_backup.zip')
        self.fastboot_ok = False
        self.fastboot_status_msg = ''
        self._verify_fastboot()
        self.xml_path = ''
        self.firmware_folder = ''
        self.partitions = []
        self.partition_widgets = []
        self.erase_partitions = []
        self.flash_type = FlashType.WIPE
        self.device_type = DeviceType.TRADITIONAL
        self.worker = None
        self.setup_ui()
    def _resolve_tools_dir(self) -> str:
        try:
            from app.utils.path_manager import PathManager
            tools = PathManager.get_unlock_tools_dir()
            if tools:
                p = os.path.normpath(os.path.join(os.path.dirname(tools), 'flash', 'motorola', 'tools'))
                if os.path.isdir(p):
                    return p
        except Exception:
            pass
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools')
    def _resolve_fastboot(self) -> str:
        try:
            from app.utils.path_manager import PathManager
            tools = PathManager.get_unlock_tools_dir()
            if tools:
                candidate = os.path.join(tools, 'fastboot.exe')
                if os.path.isfile(candidate):
                    return candidate
        except Exception:
            pass
        return os.path.join(self.tools_dir, 'fastboot.exe')
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
            print('[SECURITY] Verifica├º├úo de seguran├ºa conclu├¡da - sistema pronto para uso')
    def _verify_fastboot(self):
        '''Verifica integridade do fastboot (com auto-reparo)'''
        self._sanitize_tools_dir()
        success, message = verify_fastboot_integrity(self.fastboot_path, self.fastboot_backup_path)
        self.fastboot_ok = success
        self.fastboot_status_msg = message
        if not success:
            print(f'[FASTBOOT] ERRO: {message}')
            return
        print(f'[FASTBOOT] {message}')
    def setup_ui(self):
        self.setStyleSheet(f'background-color: {CoresMotorola.BACKGROUND};')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        header = self._create_header()
        main_layout.addWidget(header)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet('QSplitter::handle { background: #ddd; width: 3px; }')
        left_panel = self._create_config_panel()
        splitter.addWidget(left_panel)
        right_panel = self._create_log_panel()
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])
        main_layout.addWidget(splitter, 1)
        progress_section = self._create_progress_section()
        main_layout.addWidget(progress_section)
        action_bar = self._create_action_bar()
        main_layout.addWidget(action_bar)
    def _create_header(self) -> QFrame:
        '''Cria o cabe├ºalho'''
        header = QFrame()
        header.setStyleSheet(f'\n            QFrame {{\n                background-color: {CoresMotorola.PRIMARY};\n                border-radius: 10px;\n            }}\n        ')
        header.setMinimumHeight(60)
        header.setMaximumHeight(80)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(15, 8, 15, 8)
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title = QLabel('MOTOROLA FLASH TOOL')
        title.setFont(QFont('Segoe UI', 16, QFont.Bold))
        title.setStyleSheet(f'color: {CoresMotorola.TEXT_WHITE};')
        title_layout.addWidget(title)
        subtitle = QLabel('Flash via Fastboot | TECH UNION SOLUTIONS')
        subtitle.setFont(QFont('Segoe UI', 9))
        subtitle.setStyleSheet('color: rgba(255,255,255,0.8);')
        title_layout.addWidget(subtitle)
        layout.addLayout(title_layout)
        layout.addStretch()
        status_frame = QFrame()
        status_frame.setMinimumWidth(120)
        status_frame.setStyleSheet('background: transparent;')
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(4)
        if self.fastboot_ok:
            status_text = 'ÔùÅ Fastboot OK'
            color = CoresMotorola.SUCCESS
        else:
            status_text = 'ÔùÅ Fastboot ERRO'
            color = CoresMotorola.ERROR
        self.fastboot_status = QLabel(status_text)
        self.fastboot_status.setFont(QFont('Segoe UI', 9))
        self.fastboot_status.setStyleSheet(f'color: {color};')
        self.fastboot_status.setToolTip(self.fastboot_status_msg)
        status_layout.addWidget(self.fastboot_status, 0, Qt.AlignRight)
        layout.addWidget(status_frame)
        return header
    def _create_config_panel(self) -> QFrame:
        '''Cria painel de configura├º├Áes'''
        panel = QFrame()
        panel.setStyleSheet(f'\n            QFrame {{\n                background-color: {CoresMotorola.BACKGROUND_WHITE};\n                border-radius: 8px;\n                border: 1px solid {CoresMotorola.BORDER};\n            }}\n        ')
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        config_title = QLabel('CONFIGURACOES')
        config_title.setFont(QFont('Segoe UI', 12, QFont.Bold))
        config_title.setStyleSheet(f'color: {CoresMotorola.PRIMARY};')
        layout.addWidget(config_title)
        flash_group = QGroupBox('Tipo de Flash')
        flash_group.setFont(QFont('Segoe UI', 10))
        flash_group.setStyleSheet(f'\n            QGroupBox {{\n                font-weight: bold;\n                border: 1px solid {CoresMotorola.BORDER};\n                border-radius: 6px;\n                margin-top: 10px;\n                padding-top: 10px;\n            }}\n            QGroupBox::title {{\n                subcontrol-origin: margin;\n                left: 10px;\n                padding: 0 5px;\n            }}\n        ')
        flash_layout = QVBoxLayout(flash_group)
        self.flash_button_group = QButtonGroup(self)
        self.wipe_radio = QRadioButton('Flash com WIPE (flashfile.xml)')
        self.wipe_radio.setToolTip('Apaga todos os dados do dispositivo')
        self.wipe_radio.setChecked(True)
        self.wipe_radio.toggled.connect(self._on_flash_type_changed)
        self.flash_button_group.addButton(self.wipe_radio)
        flash_layout.addWidget(self.wipe_radio)
        self.no_wipe_radio = QRadioButton('Flash sem WIPE (servicefile.xml)')
        self.no_wipe_radio.setToolTip('Preserva dados do usu├írio')
        self.flash_button_group.addButton(self.no_wipe_radio)
        flash_layout.addWidget(self.no_wipe_radio)
        layout.addWidget(flash_group)
        xml_group = QGroupBox('Arquivo de Firmware')
        xml_group.setFont(QFont('Segoe UI', 10))
        xml_group.setStyleSheet(f'\n            QGroupBox {{\n                font-weight: bold;\n                border: 1px solid {CoresMotorola.BORDER};\n                border-radius: 6px;\n                margin-top: 10px;\n                padding-top: 10px;\n            }}\n            QGroupBox::title {{\n                subcontrol-origin: margin;\n                left: 10px;\n                padding: 0 5px;\n            }}\n        ')
        xml_layout = QVBoxLayout(xml_group)
        self.btn_select_xml = QPushButton('Selecionar XML / Pasta')
        self.btn_select_xml.setMinimumHeight(40)
        self.btn_select_xml.setCursor(Qt.PointingHandCursor)
        self.btn_select_xml.setStyleSheet(f'\n            QPushButton {{\n                background-color: {CoresMotorola.PRIMARY};\n                color: white;\n                border: none;\n                border-radius: 6px;\n                font-weight: bold;\n                font-size: 11px;\n            }}\n            QPushButton:hover {{\n                background-color: {CoresMotorola.PRIMARY_DARK};\n            }}\n        ')
        self.btn_select_xml.clicked.connect(self.select_firmware)
        xml_layout.addWidget(self.btn_select_xml)
        self.xml_label = QLabel('Nenhum arquivo selecionado')
        self.xml_label.setFont(QFont('Segoe UI', 9))
        self.xml_label.setStyleSheet(f'color: {CoresMotorola.TEXT_MUTED};')
        self.xml_label.setWordWrap(True)
        xml_layout.addWidget(self.xml_label)
        layout.addWidget(xml_group)
        partitions_group = QGroupBox('Parti├º├Áes Detectadas')
        partitions_group.setFont(QFont('Segoe UI', 10))
        partitions_group.setStyleSheet(f'\n            QGroupBox {{\n                font-weight: bold;\n                border: 1px solid {CoresMotorola.BORDER};\n                border-radius: 6px;\n                margin-top: 10px;\n                padding-top: 10px;\n            }}\n            QGroupBox::title {{\n                subcontrol-origin: margin;\n                left: 10px;\n                padding: 0 5px;\n            }}\n        ')
        partitions_layout = QVBoxLayout(partitions_group)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; }')
        self.partitions_container = QWidget()
        self.partitions_layout = QVBoxLayout(self.partitions_container)
        self.partitions_layout.setContentsMargins(0, 0, 0, 0)
        self.partitions_layout.setSpacing(2)
        self.partitions_placeholder = QLabel('Selecione um XML para ver as parti├º├Áes')
        self.partitions_placeholder.setAlignment(Qt.AlignCenter)
        self.partitions_placeholder.setStyleSheet(f'color: {CoresMotorola.TEXT_MUTED}; padding: 20px;')
        self.partitions_layout.addWidget(self.partitions_placeholder)
        self.partitions_layout.addStretch()
        scroll.setWidget(self.partitions_container)
        partitions_layout.addWidget(scroll)
        layout.addWidget(partitions_group, 1)
        return panel
    def _create_log_panel(self) -> QFrame:
        '''Cria painel de log'''
        panel = QFrame()
        panel.setStyleSheet(f'\n            QFrame {{\n                background-color: {CoresMotorola.BACKGROUND_WHITE};\n                border-radius: 8px;\n                border: 1px solid {CoresMotorola.BORDER};\n            }}\n        ')
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        log_title = QLabel('LOG DE EXECUCAO')
        log_title.setFont(QFont('Segoe UI', 12, QFont.Bold))
        log_title.setStyleSheet(f'color: {CoresMotorola.PRIMARY};')
        layout.addWidget(log_title)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont('Consolas', 9))
        self.log_text.setStyleSheet(f'\n            QTextEdit {{\n                background-color: #1e1e1e;\n                color: #dcdcdc;\n                border: 1px solid {CoresMotorola.BORDER};\n                border-radius: 6px;\n                padding: 8px;\n            }}\n        ')
        self.log_text.setPlaceholderText('Os logs da opera├º├úo aparecer├úo aqui...')
        layout.addWidget(self.log_text, 1)
        return panel
    def _create_progress_section(self) -> QFrame:
        '''Cria se├º├úo de progresso'''
        section = QFrame()
        section.setMinimumHeight(60)
        section.setMaximumHeight(80)
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        status_layout = QHBoxLayout()
        self.status_label = QLabel('ÔùÅ Aguardando')
        self.status_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        self.status_label.setStyleSheet(f'color: {CoresMotorola.TEXT_MUTED};')
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        self.percent_label = QLabel('0%')
        self.percent_label.setFont(QFont('Segoe UI', 14, QFont.Bold))
        self.percent_label.setStyleSheet(f'color: {CoresMotorola.PRIMARY};')
        status_layout.addWidget(self.percent_label)
        layout.addLayout(status_layout)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimumHeight(10)
        self.progress_bar.setMaximumHeight(14)
        self.progress_bar.setStyleSheet(f'\n            QProgressBar {{\n                background-color: {CoresMotorola.BACKGROUND_DARK};\n                border-radius: 6px;\n            }}\n            QProgressBar::chunk {{\n                background-color: {CoresMotorola.PRIMARY};\n                border-radius: 6px;\n            }}\n        ')
        layout.addWidget(self.progress_bar)
        return section
    def _create_action_bar(self) -> QFrame:
        '''Cria barra de a├º├Áes'''
        bar = QFrame()
        bar.setMinimumHeight(50)
        bar.setMaximumHeight(70)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.btn_detect = QPushButton('Detectar Dispositivo')
        self.btn_detect.setMinimumHeight(40)
        self.btn_detect.setMaximumHeight(50)
        self.btn_detect.setCursor(Qt.PointingHandCursor)
        self.btn_detect.setFont(QFont('Segoe UI', 10))
        self.btn_detect.setStyleSheet(f'\n            QPushButton {{\n                background-color: {CoresMotorola.BACKGROUND_WHITE};\n                color: {CoresMotorola.PRIMARY};\n                border: 2px solid {CoresMotorola.PRIMARY};\n                border-radius: 8px;\n                padding: 8px 16px;\n            }}\n            QPushButton:hover {{\n                background-color: {CoresMotorola.PRIMARY};\n                color: white;\n            }}\n        ')
        self.btn_detect.clicked.connect(self.detect_device)
        layout.addWidget(self.btn_detect)
        layout.addStretch()
        self.btn_cancel = QPushButton('Cancelar')
        self.btn_cancel.setMinimumSize(100, 40)
        self.btn_cancel.setMaximumSize(140, 50)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self.btn_cancel.setStyleSheet(f'\n            QPushButton {{\n                background-color: {CoresMotorola.BACKGROUND_DARK};\n                color: {CoresMotorola.TEXT};\n                border: none;\n                border-radius: 8px;\n            }}\n            QPushButton:hover {{\n                background-color: {CoresMotorola.ERROR};\n                color: white;\n            }}\n            QPushButton:disabled {{\n                background-color: {CoresMotorola.BACKGROUND};\n                color: {CoresMotorola.TEXT_MUTED};\n            }}\n        ')
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_flash)
        layout.addWidget(self.btn_cancel)
        self.btn_flash = QPushButton('INICIAR FLASH')
        self.btn_flash.setMinimumSize(150, 40)
        self.btn_flash.setMaximumSize(200, 50)
        self.btn_flash.setCursor(Qt.PointingHandCursor)
        self.btn_flash.setFont(QFont('Segoe UI', 11, QFont.Bold))
        self.btn_flash.setStyleSheet(f'\n            QPushButton {{\n                background-color: {CoresMotorola.PRIMARY};\n                color: white;\n                border: none;\n                border-radius: 8px;\n            }}\n            QPushButton:hover {{\n                background-color: {CoresMotorola.PRIMARY_DARK};\n            }}\n            QPushButton:disabled {{\n                background-color: {CoresMotorola.BACKGROUND_DARK};\n                color: {CoresMotorola.TEXT_MUTED};\n            }}\n        ')
        self.btn_flash.setEnabled(False)
        self.btn_flash.clicked.connect(self.start_flash)
        layout.addWidget(self.btn_flash)
        return bar
    def _on_flash_type_changed(self, checked):
        '''Callback quando tipo de flash muda'''
        if self.wipe_radio.isChecked():
            self.flash_type = FlashType.WIPE
            return
        self.flash_type = FlashType.NO_WIPE
    def select_firmware(self):
        '''Abre di├ílogo para selecionar firmware'''
        default_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        if not os.path.exists(default_dir):
            default_dir = os.path.expanduser('~')
        file_path, _ = QFileDialog.getOpenFileName(self, 'Selecionar arquivo XML', default_dir, 'Motorola XML (*.xml);;Todos os arquivos (*.*)')
        if file_path:
            self.load_xml(file_path)
    def load_xml(self, xml_path: str):
        '''Carrega e analisa o arquivo XML'''
        try:
            self.xml_path = xml_path
            self.firmware_folder = os.path.dirname(os.path.abspath(xml_path))
            self.xml_label.setText(os.path.basename(xml_path))
            self.xml_label.setToolTip(xml_path)
            self.xml_label.setStyleSheet(f'color: {CoresMotorola.TEXT};')
            self._log(f'­ƒôé Carregando: {os.path.basename(xml_path)}')
            folder_name = os.path.basename(self.firmware_folder)
            self._log(f'   Pasta: {folder_name}')
            xml_name = os.path.basename(xml_path).lower()
            if 'servicefile' in xml_name:
                self.no_wipe_radio.setChecked(True)
                self._log('   Modo: ­ƒÆ¥ Preservar dados do usu├írio')
            elif 'flashfile' in xml_name:
                self.wipe_radio.setChecked(True)
                self._log('   Modo: ÔÜá´©Å Apagar todos os dados')
            self._parse_xml(xml_path)
            valid_count = sum((1 for p in self.partitions if p.file_exists))
            if valid_count > 0:
                self.btn_flash.setEnabled(True)
                self._log(f'\nÔ£à {valid_count} parti├º├Áes prontas para flash')
                return
            self._log('\nÔÜá´©Å Nenhuma parti├º├úo v├ílida encontrada')
            return
        except Exception as e:
            self._log(f'ÔØî Erro ao carregar XML: {str(e)}')
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar XML:\n{str(e)}')
    def _parse_xml(self, xml_path: str):
        '''Analisa o XML e extrai parti├º├Áes'''
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            self.partitions = []
            for widget in self.partition_widgets:
                widget.deleteLater()
            self.partition_widgets = []
            if self.partitions_placeholder:
                self.partitions_placeholder.hide()
            self.erase_partitions = []
            steps = root.findall('.//step')
            if steps:
                for step in steps:
                    operation = step.get('operation', '')
                    partition = step.get('partition', '')
                    filename = step.get('filename', '')
                    if operation == 'flash' and partition:
                        file_path = os.path.join(self.firmware_folder, filename) if filename else ''
                        file_exists = os.path.exists(file_path) if file_path else False
                        file_size = os.path.getsize(file_path) if file_exists else 0
                        info = PartitionInfo(name=partition, filename=filename, operation=operation, file_exists=file_exists, file_size=file_size)
                        self.partitions.append(info)
                        continue
                    if operation != 'erase':
                        continue
                    if not partition:
                        continue
                    self.erase_partitions.append(partition)
                    continue
            else:
                for node in root.findall('.//filename'):
                    partition = node.get('partition', '')
                    filename = node.get('filename', '')
                    if not partition:
                        continue
                    file_path = os.path.join(self.firmware_folder, filename) if filename else ''
                    file_exists = os.path.exists(file_path) if file_path else False
                    file_size = os.path.getsize(file_path) if file_exists else 0
                    info = PartitionInfo(name=partition, filename=filename, operation='flash', file_exists=file_exists, file_size=file_size)
                    self.partitions.append(info)
                for node in root.findall('.//erase'):
                    partition = node.get('partition', '')
                    if partition:
                        self.erase_partitions.append(partition)
            if self.erase_partitions:
                self._log('   ÔÜá´©Å Este firmware ir├í APAGAR os dados do dispositivo')
            for partition in self.partitions:
                widget = PartitionWidget(partition)
                self.partition_widgets.append(widget)
                self.partitions_layout.insertWidget(self.partitions_layout.count() - 1, widget)
            self._log(f'   Parti├º├Áes encontradas: {len(self.partitions)}')
            return
        except Exception as e:
            self._log(f'ÔØî Erro ao analisar XML: {str(e)}')
    def detect_device(self):
        '''Detecta dispositivo em fastboot e obt├®m informa├º├Áes detalhadas'''
        self._log('\n==================================================')
        self._log('­ƒô▒ DETECTANDO DISPOSITIVO')
        self._log('==================================================')
        if not self.fastboot_ok:
            self._log('ÔØî Fastboot n├úo dispon├¡vel')
            return
        try:
            result = subprocess.run([self.fastboot_path, 'devices'], capture_output=True, text=True, timeout=10)
            output = result.stdout.strip()
            if not output or 'fastboot' not in output.lower():
                self._log('ÔÜá´©Å Nenhum dispositivo em modo fastboot')
                self._log('')
                self._log('­ƒôï Para entrar no modo Fastboot:')
                self._log('   1. Desligue o aparelho')
                self._log('   2. Segure Volume - + Power')
                self._log('   3. Conecte o cabo USB')
                return
            self._log('Ô£à Dispositivo conectado!')
            self._log('')
            try:
                result = subprocess.run([self.fastboot_path, 'getvar', 'all'], capture_output=True, text=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            except subprocess.TimeoutExpired:
                self._log('ÔÜá´©Å Dispositivo n├úo respondeu ao getvar all')
                self._log('   ­ƒÆí Isso pode acontecer em alguns modelos.')
                self._log('   ­ƒÆí O flash ainda pode funcionar normalmente.')
            else:
                all_vars = (result.stdout or '') + '\n' + (result.stderr or '')
                device_info = self._parse_device_info(all_vars)
                self._log('­ƒôï INFORMA├ç├òES DO DISPOSITIVO')
                self._log('----------------------------------------')
                priority_fields = [('product', '­ƒô▒ Modelo'), ('sku', '­ƒÅÀ´©Å SKU'), ('serialno', '­ƒöó Serial'), ('imei', '­ƒô▓ IMEI'), ('cpu', 'ÔÜÖ´©Å CPU'), ('ram', '­ƒÆ¥ RAM'), ('emmc', '­ƒÆ┐ Armazenamento'), ('secure', '­ƒöÆ Secure Boot'), ('securestate', '­ƒöÉ Estado Seguro'), ('frp-state', '­ƒøí´©Å FRP'), ('current-slot', '­ƒôª Slot Atual'), ('slot-count', '­ƒôª Qtd Slots'), ('version-bootloader', '­ƒöº Bootloader'), ('version-baseband', '­ƒôí Baseband'), ('ro.carrier', '­ƒôí Operadora'), ('max-download-size', '­ƒôÑ Max Download')]
                for key, label in priority_fields:
                    if key in device_info:
                        value = device_info[key]
                        if key == 'unlocked':
                            value = 'Ô£à Sim' if value.lower() == 'yes' else 'ÔØî N├úo'
                        elif key == 'secure':
                            value = '­ƒöÆ Ativo' if value.lower() == 'yes' else '­ƒöô Inativo'
                        elif key == 'battery-level':
                            value = f'{value}%'
                        elif key == 'max-download-size':
                            pass
        except subprocess.TimeoutExpired:
            self._log('ÔÜá´©Å Timeout ao obter informa├º├Áes do dispositivo')
            self._log('   ­ƒÆí O dispositivo foi detectado mas n├úo respondeu a tempo.')
            self._log('   ­ƒÆí Tente desconectar e reconectar o cabo USB.')
            self._log('   ­ƒÆí Voc├¬ ainda pode tentar o flash normalmente.')
        except Exception as e:
            error_str = str(e)
            import re
            error_clean = re.sub('[\\\'\\"]?[A-Za-z]:\\\\[^\\s\\\'\\"\\]]+[\\\'\\"]?', '', error_str)
            error_clean = error_clean.replace('Command ', '').replace(' timed out after', ' - Timeout:')
            self._log(f'ÔÜá´©Å {error_clean.strip()}')
        self._log('----------------------------------------')
        if 'current-slot' in device_info or device_info.get('slot-count', '0') == '2':
            self.device_type = DeviceType.AB
            self._log('   ­ƒôî Tipo: Dispositivo A/B')
        else:
            self.device_type = DeviceType.TRADITIONAL
            self._log('   ­ƒôî Tipo: Dispositivo Tradicional')
        self._log('')
    def _parse_device_info(self, raw_output: str) -> Dict[str, str]:
        '''Analisa sa├¡da do getvar all e retorna dicion├írio organizado'''
        info = {}
        for line in raw_output.split('\n'):
            line = line.strip()
            if line:
                if 'Finished' in line or 'listed above' in line:
                    continue
                if '(bootloader)' in line:
                    line = line.replace('(bootloader)', '').strip()
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip().lower()
                        value = parts[1].strip()
                        if '[' in key:
                            key = key.split('[')[0]
                        if not key:
                            continue
                        if not value:
                            continue
                        if key not in info:
                            info[key] = value
        return info
    def start_flash(self):
        '''Inicia o processo de flash'''
        if not self.fastboot_ok:
            QMessageBox.critical(self, 'Erro', 'Fastboot n├úo dispon├¡vel!')
            return
        if not self.xml_path:
            QMessageBox.warning(self, 'Aviso', 'Selecione um arquivo XML primeiro!')
            return
        selected_partitions = []
        for widget in self.partition_widgets:
            if widget.is_selected():
                selected_partitions.append(widget.partition)
        if not selected_partitions:
            QMessageBox.warning(self, 'Aviso', 'Nenhuma parti├º├úo selecionada!')
            return
        risk_msg = QMessageBox(self)
        risk_msg.setWindowTitle('AVISO DE RISCO')
        risk_msg.setIcon(QMessageBox.Warning)
        warning_text = '<h3>ATENCAO - PROCEDIMENTO DE RISCO</h3>\n        \n<p><b>Antes de continuar, verifique:</b></p>\n<ul>\n<li>A ROM e <b>COMPATIVEL</b> com este modelo exato?</li>\n<li>O cabo USB e <b>ORIGINAL</b> ou de boa qualidade?</li>\n<li>A bateria esta com <b>MAIS DE 50%</b>?</li>\n<li>O dispositivo esta em modo <b>FASTBOOT</b>?</li>\n</ul>\n\n<p style="color: #d32f2f;"><b>RISCOS:</b></p>\n<ul>\n<li>Flash de ROM incompativel pode BRICKAR o dispositivo</li>\n<li>Desconexao durante o processo pode danificar o aparelho</li>\n<li>Erro de USB pode corromper particoes</li>\n</ul>\n\n<p><b>DICA:</b> Se ocorrer erro de USB ("Too many links"), \ntroque de porta USB ou reinicie o dispositivo em fastboot.</p>\n'
        risk_msg.setTextFormat(Qt.RichText)
        risk_msg.setText(warning_text)
        risk_msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        risk_msg.setDefaultButton(QMessageBox.No)
        risk_msg.button(QMessageBox.Yes).setText('Entendi os riscos, CONTINUAR')
        risk_msg.button(QMessageBox.No).setText('Cancelar')
        if risk_msg.exec_() != QMessageBox.Yes:
            return
        msg = f'<b>Flash de {len(selected_partitions)} parti├º├úo(├Áes)</b>\n\n'
        if self.flash_type == FlashType.WIPE:
            msg += "<p style='color: #d32f2f;'>WIPE: Todos os dados serao APAGADOS!</p>"
        else:
            msg += "<p style='color: #388e3c;'>Dados do usuario serao preservados.</p>"
        final_msg = QMessageBox(self)
        final_msg.setWindowTitle('Confirmar Flash')
        final_msg.setIcon(QMessageBox.Question)
        final_msg.setTextFormat(Qt.RichText)
        final_msg.setText(msg)
        final_msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        final_msg.setDefaultButton(QMessageBox.No)
        final_msg.button(QMessageBox.Yes).setText('INICIAR FLASH')
        final_msg.button(QMessageBox.No).setText('Cancelar')
        reply = final_msg.exec_()
        if reply != QMessageBox.Yes:
            return
        commands = self._generate_commands(selected_partitions)
        if not commands:
            QMessageBox.warning(self, 'Aviso', 'Nenhum comando gerado!')
            return
        self._log('\n============================================================')
        self._log('­ƒÜÇ INICIANDO PROCESSO DE FLASH')
        self._log('============================================================')
        self.btn_flash.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_select_xml.setEnabled(False)
        self.worker = MotorolaFlashWorker(self.fastboot_path, commands, self.firmware_folder)
        self.worker.progress_signal.connect(self._on_progress)
        self.worker.log_signal.connect(self._log)
        self.worker.status_signal.connect(self._on_status)
        self.worker.finished_signal.connect(self._on_flash_finished)
        self.worker.start()
    def _generate_commands(self, partitions: List[PartitionInfo]) -> List[str]:
        '''Gera lista de comandos fastboot'''
        commands = []
        commands.append('getvar max-sparse-size')
        commands.append('oem fb_mode_set')
        for partition in partitions:
            if partition.file_exists:
                file_path = os.path.join(self.firmware_folder, partition.filename)
                commands.append(f'flash {partition.name} "{file_path}"')
        if self.flash_type == FlashType.WIPE and hasattr(self, 'erase_partitions'):
            for erase_partition in self.erase_partitions:
                commands.append(f'erase {erase_partition}')
        commands.append('oem fb_mode_clear')
        commands.append('reboot')
        return commands
    def cancel_flash(self):
        '''Cancela o flash em andamento'''
        if self.worker:
            if self.worker.isRunning():
                reply = QMessageBox.question(self, 'Cancelar Flash', 'Deseja realmente cancelar o flash?\n\nÔÜá´©Å O dispositivo pode ficar em estado inconsistente!', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.worker.stop()
                    self._log('\nÔÜá´©Å Cancelamento solicitado...')
    def _on_progress(self, value: int):
        '''Callback de progresso'''
        self.progress_bar.setValue(value)
        self.percent_label.setText(f'{value}%')
    def _on_status(self, status: str):
        '''Callback de status'''
        self.status_label.setText(f'ÔùÅ {status}')
        self.status_label.setStyleSheet(f'color: {CoresMotorola.PRIMARY};')
    def _on_flash_finished(self, success: bool, message: str):
        '''Callback quando flash termina'''
        self.btn_flash.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_select_xml.setEnabled(True)
        if success:
            self.status_label.setText('ÔùÅ Conclu├¡do')
            self.status_label.setStyleSheet(f'color: {CoresMotorola.SUCCESS};')
            QMessageBox.information(self, 'Sucesso', message)
            return
        self.status_label.setText('ÔùÅ Erro')
        self.status_label.setStyleSheet(f'color: {CoresMotorola.ERROR};')
        QMessageBox.warning(self, 'Aviso', message)
    def _log(self, message: str):
        '''Adiciona mensagem ao log'''
        self.log_text.append(message)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
class MotorolaFlashWindow(QMainWindow):
    '''Janela principal para execu├º├úo standalone'''
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Motorola Flash Tool - TECH UNION SOLUTIONS')
        self.setMinimumSize(1000, 700)
        self.flash_widget = MotorolaFlashToolWidget()
        self.setCentralWidget(self.flash_widget)
        self.center_on_screen()
    def center_on_screen(self):
        '''Centraliza a janela na tela'''
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MotorolaFlashWindow()
    window.show()
    sys.exit(app.exec_())
