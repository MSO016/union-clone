'''
XIAOMI FLASH TOOL - TECH UNION SOLUTIONS
Flash de firmware Xiaomi via Fastboot
Parseia flash_all.bat / flash_all_except_data_storage.bat
Autor: TECH UNION SOLUTIONS
'''
import os
import re
import sys
import subprocess
import ctypes
import zipfile
import hashlib
from typing import (List, Dict, Optional, Tuple)
from dataclasses import dataclass
from enum import Enum
if sys.platform == 'win32':
    ctypes.windll.kernel32.SetErrorMode(32769)
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QProgressBar, QFileDialog, QMessageBox, QFrame, QScrollArea, QGridLayout, QCheckBox, QRadioButton, QButtonGroup, QGroupBox, QSplitter, QApplication, QSizePolicy)
from PyQt5.QtCore import (Qt, QThread, pyqtSignal, QSize)
from PyQt5.QtGui import (QFont, QFontMetrics, QIcon)
class CoresXiaomi:
    '''Paleta de cores Xiaomi'''
    PRIMARY = '#FF6900'
    PRIMARY_DARK = '#E55A00'
    PRIMARY_LIGHT = '#FF8533'
    BACKGROUND_DARK = '#1a1a1a'
    BACKGROUND_MEDIUM = '#2d2d2d'
    BACKGROUND_LIGHT = '#3d3d3d'
    BACKGROUND_WHITE = '#ffffff'
    SUCCESS = '#4CAF50'
    WARNING = '#FFC107'
    ERROR = '#f44336'
    INFO = '#2196F3'
    TEXT_WHITE = '#ffffff'
    TEXT_DARK = '#333333'
    TEXT_MUTED = '#888888'
class FlashType(Enum):
    '''Tipo de flash'''
    WIPE = 'wipe'
    NO_WIPE = 'no_wipe'
    LOCK = 'lock'
@dataclass
class PartitionInfo:
    '''Informa├º├Áes de uma parti├º├úo'''
    name: str
    filename: str
    operation: str
    file_exists: bool = False
    file_size: int = 0
    def size_formatted(self) -> str:
        '''Retorna tamanho formatado'''
        if self.file_size < 1024:
            return f'{self.file_size} B'
        if self.file_size < 1048576:
            return f'{self.file_size / 1024:.1f} KB'
        if self.file_size < 1073741824:
            return f'{self.file_size / 1048576:.1f} MB'
        return f'{self.file_size / 1073741824:.2f} GB'
class XiaomiFlashWorker(QThread):
    '''Worker thread para executar flash em background'''
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
            self.log_signal.emit('­ƒöÑ INICIANDO FLASH XIAOMI')
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
                        error_clean = self._clean_output(str(e))
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
            self.status_signal.emit('Flash parcialmente conclu├¡do')
            self.finished_signal.emit(True, f'Parcial: {success_count} OK, {error_count} erros')
            return
        self.log_signal.emit('\nÔØî Flash falhou')
        self.log_signal.emit('   ­ƒÆí Verifique o cabo USB e tente em outra porta.')
        self.status_signal.emit('Flash falhou')
        self.finished_signal.emit(False, f'Falhou: {error_count} erros')
    def _execute_fastboot(self, cmd: str) -> Dict:
        '''Executa um comando fastboot'''
        try:
            full_cmd = f'"{self.fastboot_path}" {cmd}'
            result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=300, cwd=self.firmware_folder, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            output = (result.stdout or '') + (result.stderr or '')
            if result.returncode == 0:
                return {'success': True, 'output': output.strip(), 'error': ''}
            return {'success': False, 'output': '', 'error': output.strip()}
        except subprocess.TimeoutExpired:
            return {'success': False, 'output': '', 'error': 'Timeout - parti├º├úo muito grande ou dispositivo travou'}
        except Exception as e:
            return {'success': False, 'output': '', 'error': str(e)}
    def _format_cmd_for_log(self, cmd: str) -> str:
        '''Formata comando para log sem expor caminhos'''
        cmd = re.sub('[A-Za-z]:\\\\[^\\s"]+\\\\', '', cmd)
        cmd = re.sub('%~dp0\\\\?images\\\\?', '', cmd)
        cmd = re.sub('%~dp0\\\\?', '', cmd)
        if cmd.startswith('flash '):
            parts = cmd.split()
            if len(parts) >= 3:
                partition = parts[1]
                filename = os.path.basename(parts[2].strip('"'))
                return f'­ƒôª flash {partition} ÔåÆ {filename}'
        if cmd.startswith('erase'):
            return '­ƒùæ´©Å Preparando ├írea de dados...'
        if cmd.startswith('getvar'):
            return f'­ƒöì {cmd}'
        if cmd == 'reboot':
            return '­ƒöä Reiniciando dispositivo...'
        if 'oem lock' in cmd:
            return '­ƒöÆ Bloqueando bootloader...'
        return cmd
    def _clean_output(self, text: str) -> str:
        '''Remove caminhos e informa├º├Áes sens├¡veis'''
        if not text:
            return ''
        text = re.sub('[A-Za-z]:\\\\[^\\s\\\'"]*', (lambda m: os.path.basename(m.group(0))), text)
        text = re.sub('%~dp0\\\\?images\\\\?', '', text)
        text = re.sub('\\n\\s*\\n', '\n', text)
        return text.strip()
    def _is_critical_error(self, command: str, error_msg: str) -> bool:
        '''Verifica se ├® erro cr├¡tico'''
        error_lower = error_msg.lower()
        critical_errors = ['no devices', 'device not found', 'remote: not allowed', 'anti-rollback', 'device is locked', 'oem unlock is required', 'current device antirollback']
        for critical in critical_errors:
            if critical in error_lower:
                return True
        return False
    def _is_retryable_error(self, error_msg: str) -> bool:
        '''Verifica se erro pode ser resolvido com retry'''
        error_lower = error_msg.lower()
        retryable_patterns = ['too many links', 'write to device failed', 'sendbuffer', 'usb', 'timeout']
        for pattern in retryable_patterns:
            if pattern in error_lower:
                return True
        return False
class XiaomiPartitionWidget(QFrame):
    '''Widget para exibir uma parti├º├úo'''
    def __init__(self, partition: PartitionInfo, parent=None):
        super().__init__(parent)
        self.partition = partition
        self.setup_ui()
    def setup_ui(self):
        if self.partition.file_exists:
            border_color = CoresXiaomi.SUCCESS
            status_icon = '[OK]'
        else:
            border_color = CoresXiaomi.ERROR
            status_icon = '[X]'
        self.setStyleSheet(f'\n            XiaomiPartitionWidget {{\n                background-color: {CoresXiaomi.BACKGROUND_WHITE};\n                border: 1px solid {border_color};\n                border-left: 4px solid {border_color};\n                border-radius: 4px;\n                padding: 4px;\n                margin: 2px;\n            }}\n        ')
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.partition.file_exists)
        self.checkbox.setEnabled(self.partition.file_exists)
        layout.addWidget(self.checkbox)
        status_lbl = QLabel(status_icon)
        layout.addWidget(status_lbl)
        name_lbl = QLabel(self.partition.name)
        name_lbl.setStyleSheet(f'font-weight: bold; color: {CoresXiaomi.TEXT_DARK};')
        name_lbl.setMinimumWidth(120)
        layout.addWidget(name_lbl)
        file_lbl = QLabel(self.partition.filename)
        file_lbl.setStyleSheet(f'color: {CoresXiaomi.TEXT_MUTED};')
        layout.addWidget(file_lbl, 1)
        if self.partition.file_exists:
            size_lbl = QLabel(self.partition.size_formatted())
            size_lbl.setStyleSheet(f'color: {CoresXiaomi.PRIMARY};')
            layout.addWidget(size_lbl)
    def is_selected(self) -> bool:
        return self.checkbox.isChecked()
class XiaomiFlashToolWidget(QWidget):
    '''Widget principal do Xiaomi Flash Tool'''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.tools_path = self._resolve_tools_dir()
        self.fastboot_path = self._resolve_fastboot()
        self.fastboot_backup_path = os.path.join(self.tools_path, 'tools_backup.zip')
        self.fastboot_ok = False
        self.bat_path = None
        self.firmware_folder = None
        self.partitions = []
        self.partition_widgets = []
        self.flash_type = FlashType.WIPE
        self.device_codename = None
        self.worker = None
        self.setup_ui()
        self.verify_fastboot_integrity()
    def _resolve_tools_dir(self) -> str:
        try:
            from app.utils.path_manager import PathManager
            tools = PathManager.get_unlock_tools_dir()
            if tools:
                p = os.path.normpath(os.path.join(os.path.dirname(tools), 'flash', 'xiaomi', 'tools'))
                if os.path.isdir(p):
                    return p
        except Exception:
            pass
        return os.path.join(self.base_path, 'tools')
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
        return os.path.join(self.tools_path, 'fastboot.exe')
    def setup_ui(self):
        '''Configura a interface'''
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self._create_header())
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet('QSplitter::handle { background: #ddd; }')
        left_panel = self._create_config_panel()
        splitter.addWidget(left_panel)
        right_panel = self._create_log_panel()
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 500])
        main_layout.addWidget(splitter, 1)
        main_layout.addWidget(self._create_action_bar())
    def _create_header(self) -> QFrame:
        '''Cria o header com informa├º├Áes'''
        header = QFrame()
        header.setStyleSheet(f'\n            QFrame {{\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n                    stop:0 {CoresXiaomi.PRIMARY},\n                    stop:1 {CoresXiaomi.PRIMARY_DARK});\n                border: none;\n            }}\n        ')
        header.setMinimumHeight(50)
        header.setMaximumHeight(60)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(15, 8, 15, 8)
        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)
        title = QLabel('XIAOMI FLASH TOOL')
        title.setStyleSheet(f'\n            font-size: 16px;\n            font-weight: bold;\n            color: {CoresXiaomi.TEXT_WHITE};\n        ')
        title_layout.addWidget(title)
        subtitle = QLabel('Flash via Fastboot | TECH UNION SOLUTIONS')
        subtitle.setStyleSheet('font-size: 10px; color: rgba(255,255,255,0.8);')
        title_layout.addWidget(subtitle)
        layout.addLayout(title_layout)
        layout.addStretch()
        status_frame = QFrame()
        status_frame.setMinimumWidth(180)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)
        self.fastboot_status = QLabel('Verificando...')
        self.fastboot_status.setStyleSheet(f'color: {CoresXiaomi.TEXT_WHITE}; font-size: 11px;')
        status_layout.addWidget(self.fastboot_status)
        self.verify_btn = QPushButton('Verificar')
        self.verify_btn.setStyleSheet('\n            QPushButton {\n                background: rgba(255,255,255,0.2);\n                color: white;\n                border: 1px solid rgba(255,255,255,0.3);\n                border-radius: 3px;\n                padding: 3px 8px;\n                font-size: 10px;\n            }\n            QPushButton:hover {\n                background: rgba(255,255,255,0.3);\n            }\n        ')
        self.verify_btn.setMinimumSize(60, 20)
        self.verify_btn.setMaximumSize(75, 24)
        self.verify_btn.clicked.connect(self.verify_fastboot_integrity)
        status_layout.addWidget(self.verify_btn)
        status_layout.addStretch()
        layout.addWidget(status_frame, 0, Qt.AlignRight | Qt.AlignVCenter)
        return header
    def _create_config_panel(self) -> QFrame:
        '''Cria o painel de configura├º├Áes'''
        panel = QFrame()
        panel.setStyleSheet(f'\n            QFrame {{\n                background: {CoresXiaomi.BACKGROUND_WHITE};\n                border: none;\n            }}\n        ')
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        config_title = QLabel('CONFIGURACOES')
        config_title.setStyleSheet(f'\n            font-size: 13px;\n            font-weight: bold;\n            color: {CoresXiaomi.PRIMARY};\n            padding: 5px;\n            background: {CoresXiaomi.BACKGROUND_LIGHT};\n            border-radius: 4px;\n        ')
        layout.addWidget(config_title)
        type_group = QGroupBox('Tipo de Flash')
        type_group.setStyleSheet(f'\n            QGroupBox {{\n                font-weight: bold;\n                border: 1px solid #ddd;\n                border-radius: 4px;\n                margin-top: 8px;\n                padding-top: 8px;\n            }}\n            QGroupBox::title {{\n                color: {CoresXiaomi.PRIMARY};\n            }}\n        ')
        type_layout = QVBoxLayout(type_group)
        self.flash_type_group = QButtonGroup(self)
        self.wipe_radio = QRadioButton('Flash com WIPE (apaga dados)')
        self.wipe_radio.setChecked(True)
        self.wipe_radio.setStyleSheet('color: #d32f2f;')
        self.flash_type_group.addButton(self.wipe_radio, 0)
        type_layout.addWidget(self.wipe_radio)
        self.no_wipe_radio = QRadioButton('Flash sem WIPE (preserva dados)')
        self.no_wipe_radio.setStyleSheet('color: #388e3c;')
        self.flash_type_group.addButton(self.no_wipe_radio, 1)
        type_layout.addWidget(self.no_wipe_radio)
        self.lock_radio = QRadioButton('Flash + LOCK (bloqueia bootloader)')
        self.lock_radio.setStyleSheet('color: #1565c0;')
        self.flash_type_group.addButton(self.lock_radio, 2)
        type_layout.addWidget(self.lock_radio)
        self.bootloader_warning = QLabel('')
        self.bootloader_warning.setWordWrap(True)
        self.bootloader_warning.setStyleSheet('\n            QLabel {\n                padding: 8px;\n                border-radius: 4px;\n                font-size: 10px;\n            }\n        ')
        type_layout.addWidget(self.bootloader_warning)
        self._update_bootloader_warning()
        self.flash_type_group.buttonClicked.connect(self._on_flash_type_changed)
        layout.addWidget(type_group)
        firmware_group = QGroupBox('Arquivo de Firmware')
        firmware_group.setStyleSheet(f'\n            QGroupBox {{\n                font-weight: bold;\n                border: 1px solid #ddd;\n                border-radius: 4px;\n                margin-top: 8px;\n                padding-top: 8px;\n            }}\n            QGroupBox::title {{\n                color: {CoresXiaomi.PRIMARY};\n            }}\n        ')
        firmware_layout = QVBoxLayout(firmware_group)
        self.select_btn = QPushButton('Selecionar Pasta do Firmware')
        self.select_btn.setStyleSheet(f'\n            QPushButton {{\n                background: {CoresXiaomi.PRIMARY};\n                color: white;\n                border: none;\n                border-radius: 4px;\n                padding: 10px;\n                font-weight: bold;\n            }}\n            QPushButton:hover {{\n                background: {CoresXiaomi.PRIMARY_DARK};\n            }}\n        ')
        self.select_btn.clicked.connect(self.select_firmware)
        firmware_layout.addWidget(self.select_btn)
        self.firmware_info = QLabel('Nenhum firmware selecionado')
        self.firmware_info.setStyleSheet(f'color: {CoresXiaomi.TEXT_MUTED}; padding: 5px;')
        self.firmware_info.setWordWrap(True)
        firmware_layout.addWidget(self.firmware_info)
        layout.addWidget(firmware_group)
        partitions_group = QGroupBox('Parti├º├Áes Detectadas')
        partitions_group.setStyleSheet(f'\n            QGroupBox {{\n                font-weight: bold;\n                border: 1px solid #ddd;\n                border-radius: 4px;\n                margin-top: 8px;\n                padding-top: 8px;\n            }}\n            QGroupBox::title {{\n                color: {CoresXiaomi.PRIMARY};\n            }}\n        ')
        partitions_layout = QVBoxLayout(partitions_group)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('border: none;')
        self.partitions_container = QWidget()
        self.partitions_layout = QVBoxLayout(self.partitions_container)
        self.partitions_layout.setContentsMargins(0, 0, 0, 0)
        self.partitions_layout.setSpacing(4)
        self.partitions_layout.addStretch()
        scroll.setWidget(self.partitions_container)
        partitions_layout.addWidget(scroll)
        layout.addWidget(partitions_group, 1)
        return panel
    def _create_log_panel(self) -> QFrame:
        '''Cria o painel de log'''
        panel = QFrame()
        panel.setStyleSheet(f'background: {CoresXiaomi.BACKGROUND_WHITE};')
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        log_title = QLabel('LOG DE EXECUCAO')
        log_title.setStyleSheet(f'\n            font-size: 13px;\n            font-weight: bold;\n            color: {CoresXiaomi.PRIMARY};\n            padding: 5px;\n            background: {CoresXiaomi.BACKGROUND_LIGHT};\n            border-radius: 4px;\n        ')
        layout.addWidget(log_title)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(f"\n            QTextEdit {{\n                background: {CoresXiaomi.BACKGROUND_DARK};\n                color: {CoresXiaomi.TEXT_WHITE};\n                border: 1px solid {CoresXiaomi.PRIMARY};\n                border-radius: 4px;\n                font-family: 'Consolas', 'Courier New', monospace;\n                font-size: 11px;\n                padding: 8px;\n            }}\n        ")
        layout.addWidget(self.log_text, 1)
        return panel
    def _create_action_bar(self) -> QFrame:
        '''Cria a barra de a├º├úo inferior'''
        bar = QFrame()
        bar.setStyleSheet(f'\n            QFrame {{\n                background: {CoresXiaomi.BACKGROUND_LIGHT};\n                border-top: 2px solid {CoresXiaomi.PRIMARY};\n            }}\n        ')
        bar.setMinimumHeight(60)
        bar.setMaximumHeight(70)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f'\n            QProgressBar {{\n                border: 1px solid #ccc;\n                border-radius: 4px;\n                text-align: center;\n                background: white;\n                height: 20px;\n            }}\n            QProgressBar::chunk {{\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n                    stop:0 {CoresXiaomi.PRIMARY},\n                    stop:1 {CoresXiaomi.PRIMARY_LIGHT});\n                border-radius: 3px;\n            }}\n        ')
        layout.addWidget(self.progress_bar, 1)
        self.btn_detect = QPushButton('Detectar Dispositivo')
        self.btn_detect.setStyleSheet(f'\n            QPushButton {{\n                background: {CoresXiaomi.INFO};\n                color: white;\n                border: none;\n                border-radius: 4px;\n                padding: 10px 15px;\n                font-weight: bold;\n            }}\n            QPushButton:hover {{\n                background: #1976D2;\n            }}\n        ')
        self.btn_detect.clicked.connect(self.detect_device)
        layout.addWidget(self.btn_detect)
        self.btn_cancel = QPushButton('Cancelar')
        self.btn_cancel.setStyleSheet(f'\n            QPushButton {{\n                background: {CoresXiaomi.ERROR};\n                color: white;\n                border: none;\n                border-radius: 4px;\n                padding: 10px 15px;\n                font-weight: bold;\n            }}\n            QPushButton:hover {{\n                background: #d32f2f;\n            }}\n            QPushButton:disabled {{\n                background: #ccc;\n            }}\n        ')
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_flash)
        layout.addWidget(self.btn_cancel)
        self.btn_flash = QPushButton('INICIAR FLASH')
        self.btn_flash.setStyleSheet(f'\n            QPushButton {{\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 {CoresXiaomi.PRIMARY_LIGHT},\n                    stop:1 {CoresXiaomi.PRIMARY});\n                color: white;\n                border: none;\n                border-radius: 4px;\n                padding: 10px 25px;\n                font-weight: bold;\n                font-size: 13px;\n            }}\n            QPushButton:hover {{\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 {CoresXiaomi.PRIMARY},\n                    stop:1 {CoresXiaomi.PRIMARY_DARK});\n            }}\n            QPushButton:disabled {{\n                background: #ccc;\n            }}\n        ')
        self.btn_flash.setEnabled(False)
        self.btn_flash.clicked.connect(self.start_flash)
        layout.addWidget(self.btn_flash)
        return bar
    def _log(self, message: str):
        '''Adiciona mensagem ao log'''
        self.log_text.append(message)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    def _sanitize_tools_dir(self):
        '''Remove DLLs n├úo autorizadas da pasta tools (preven├º├úo contra malware dropper)'''
        allowed_dlls = {'adbwinapi.dll', 'adbwinusbapi.dll'}
        cleaned = False
        try:
            for f in os.listdir(self.tools_path):
                if not f.lower().endswith('.dll'):
                    continue
                if f.lower() not in allowed_dlls:
                    try:
                        try:
                            os.remove(os.path.join(self.tools_path, f))
                            cleaned = True
                        except Exception:
                            continue
                    except Exception:
                        break
        except Exception:
            pass
        if cleaned:
            self._log('­ƒøí´©Å Verifica├º├úo de seguran├ºa conclu├¡da - sistema pronto para uso')
    def verify_fastboot_integrity(self):
        '''Verifica integridade do fastboot'''
        self._sanitize_tools_dir()
        self._log('\n­ƒöì Verificando integridade do Fastboot...')
        try:
            if not os.path.exists(self.fastboot_path):
                self._log('   ÔÜá´©Å Fastboot n├úo encontrado, tentando restaurar...')
                if self._restore_fastboot():
                    self._log('   Ô£à Fastboot restaurado com sucesso!')
                else:
                    self._log('   ÔØî Falha ao restaurar fastboot')
                    self.fastboot_ok = False
                    self.fastboot_status.setText('Fastboot indisponivel')
                    return
            result = subprocess.run([self.fastboot_path, '--version'], capture_output=True, text=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0] if result.stdout else 'OK'
                self._log(f'   Ô£à Fastboot OK: {version}')
                self.fastboot_ok = True
                self.fastboot_status.setText('Fastboot OK')
                return
            raise Exception('Falha na execu├º├úo')
        except subprocess.TimeoutExpired:
            self._log('   ÔÜá´©Å Fastboot timeout, tentando restaurar...')
            if self._restore_fastboot():
                self.verify_fastboot_integrity()
        except Exception as e:
            self._log(f'   ÔØî Erro: {str(e)}')
            self.fastboot_ok = False
            self.fastboot_status.setText('Fastboot erro')
    def _restore_fastboot(self) -> bool:
        '''Restaura fastboot do backup'''
        try:
            if os.path.exists(self.fastboot_backup_path):
                with zipfile.ZipFile(self.fastboot_backup_path, 'r') as zf:
                    zf.extractall(self.tools_path)
                return os.path.exists(self.fastboot_path)
        except:
            pass
        return False
    def _on_flash_type_changed(self, button):
        '''Callback quando muda tipo de flash'''
        if button == self.wipe_radio:
            self.flash_type = FlashType.WIPE
        elif button == self.no_wipe_radio:
            self.flash_type = FlashType.NO_WIPE
        elif button == self.lock_radio:
            self.flash_type = FlashType.LOCK
        self._update_bootloader_warning()
        if self.firmware_folder:
            self._load_bat_file()
    def select_firmware(self):
        '''Seleciona pasta do firmware'''
        default_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        folder = QFileDialog.getExistingDirectory(self, 'Selecionar Pasta do Firmware Xiaomi', default_path, QFileDialog.ShowDirsOnly)
        if folder:
            self.firmware_folder = folder
            self._load_bat_file()
    def _update_bootloader_warning(self):
        '''Atualiza o aviso sobre requisitos de bootloader'''
        if self.flash_type == FlashType.LOCK:
            self.bootloader_warning.setText('<b>Flash + Lock:</b> Flasha o firmware e BLOQUEIA o bootloader no final. Recomendado para assistencias autorizadas ou ROM de engenharia. Se falhar, o dispositivo pode ficar inutilizavel!')
            self.bootloader_warning.setStyleSheet('\n                QLabel {\n                    background: #e3f2fd;\n                    color: #1565c0;\n                    padding: 8px;\n                    border: 1px solid #1565c0;\n                    border-radius: 4px;\n                    font-size: 10px;\n                }\n            ')
            return
        self.bootloader_warning.setText("<b>REQUISITO:</b> O bootloader DEVE estar <b>DESBLOQUEADO</b> para usar esta opcao. Caso contrario, o erro 'Not allowed in locked state' sera exibido.")
        self.bootloader_warning.setStyleSheet('\n                QLabel {\n                    background: #fff3e0;\n                    color: #e65100;\n                    padding: 8px;\n                    border: 1px solid #e65100;\n                    border-radius: 4px;\n                    font-size: 10px;\n                }\n            ')
    def _load_bat_file(self):
        '''Carrega e parseia o arquivo .bat'''
        if not self.firmware_folder:
            return
        for widget in self.partition_widgets:
            widget.deleteLater()
        self.partition_widgets.clear()
        self.partitions.clear()
        if self.flash_type == FlashType.WIPE:
            bat_name = 'flash_all.bat'
        elif self.flash_type == FlashType.NO_WIPE:
            bat_name = 'flash_all_except_data_storage.bat'
        else:
            bat_name = 'flash_all_lock.bat'
        bat_path = os.path.join(self.firmware_folder, bat_name)
        if not os.path.exists(bat_path):
            self._log(f'ÔÜá´©Å Arquivo {bat_name} n├úo encontrado')
            self.firmware_info.setText(f'{bat_name} nao encontrado na pasta')
            return
        self.bat_path = bat_path
        self._log(f'\n­ƒôé Carregando: {bat_name}')
        self._log(f'   Pasta: {os.path.basename(self.firmware_folder)}')
        self._parse_bat_file(bat_path)
        if self.device_codename:
            self._log(f'   Dispositivo: {self.device_codename}')
        if self.flash_type == FlashType.WIPE:
            self._log('   ÔÜá´©Å Este firmware ir├í APAGAR os dados do dispositivo')
        elif self.flash_type == FlashType.NO_WIPE:
            self._log('   ­ƒÆ¥ Dados do usu├írio ser├úo preservados')
        else:
            self._log('   ­ƒöÆ Este firmware ir├í APAGAR dados e BLOQUEAR o bootloader')
        self._log(f'   Parti├º├Áes encontradas: {len(self.partitions)}')
        valid_count = 0
        for partition in self.partitions:
            widget = XiaomiPartitionWidget(partition)
            self.partition_widgets.append(widget)
            self.partitions_layout.insertWidget(self.partitions_layout.count() - 1, widget)
            if partition.file_exists:
                valid_count += 1
        self._log(f'Ô£à {valid_count} parti├º├Áes prontas para flash')
        self.firmware_info.setText(f'{os.path.basename(self.firmware_folder)}\n{len(self.partitions)} particoes ({valid_count} validas)')
        self.btn_flash.setEnabled(valid_count > 0)
    def _parse_bat_file(self, bat_path: str):
        '''Parseia o arquivo .bat e extrai parti├º├Áes'''
        try:
            with open(bat_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            codename_match = re.search('product: \\*(\\w+)', content)
            if codename_match:
                self.device_codename = codename_match.group(1)
            images_folder = os.path.join(self.firmware_folder, 'images')
            if not os.path.exists(images_folder):
                images_folder = self.firmware_folder
            flash_pattern = re.compile('fastboot\\s+%\\*\\s+(flash|erase)\\s+(\\S+)(?:\\s+%~dp0\\\\?(?:images\\\\?)?(\\S+))?', re.IGNORECASE)
            for match in flash_pattern.finditer(content):
                operation = match.group(1).lower()
                partition = match.group(2)
                filename = match.group(3) if match.group(3) else ''
                filename = filename.strip('"').strip("'").replace('\\', '/')
                if filename.startswith('images/'):
                    filename = filename[7:]
                if partition in ('boot',) and operation == 'erase':
                    continue
                if operation != 'flash':
                    continue
                if not filename:
                    continue
                file_path = os.path.join(images_folder, filename)
                file_exists = os.path.exists(file_path)
                file_size = os.path.getsize(file_path) if file_exists else 0
                info = PartitionInfo(name=partition, filename=filename, operation=operation, file_exists=file_exists, file_size=file_size)
                self.partitions.append(info)
                continue
        except Exception as e:
            self._log(f'ÔØî Erro ao parsear .bat: {str(e)}')
    def detect_device(self):
        '''Detecta dispositivo conectado'''
        self._log('\n==================================================')
        self._log('­ƒô▒ DETECTANDO DISPOSITIVO')
        self._log('==================================================')
        if not self.fastboot_ok:
            self._log('ÔØî Fastboot n├úo dispon├¡vel')
            return
        try:
            result = subprocess.run([self.fastboot_path, 'devices'], capture_output=True, text=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
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
        except Exception as e:
            error_clean = re.sub('[\\\'\\"]?[A-Za-z]:\\\\[^\\s\\\'\\"\\]]+[\\\'\\"]?', '', str(e))
            self._log(f'ÔÜá´©Å {error_clean.strip()}')
        try:
            try:
                result = subprocess.run([self.fastboot_path, 'getvar', 'all'], capture_output=True, text=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                all_vars = (result.stdout or '') + '\n' + (result.stderr or '')
                device_info = self._parse_device_info(all_vars)
                self._log('­ƒôï INFORMA├ç├òES DO DISPOSITIVO')
                self._log('----------------------------------------')
                priority_fields = [('product', '­ƒô▒ Modelo'), ('serialno', '­ƒöó Serial'), ('ro.product.model', '­ƒÅÀ´©Å Nome'), ('version-bootloader', '­ƒöº Bootloader'), ('version-baseband', '­ƒôí Baseband'), ('unlocked', '­ƒöô Desbloqueado'), ('secure', '­ƒöÆ Secure Boot'), ('current-slot', '­ƒôª Slot Atual'), ('slot-count', '­ƒôª Qtd Slots'), ('anti', '­ƒøí´©Å Anti-rollback')]
                for key, label in priority_fields:
                    if key in device_info:
                        value = device_info[key]
                        if key == 'unlocked':
                            value = 'Ô£à Sim' if value.lower() == 'yes' else 'ÔØî N├úo'
                        elif key == 'secure':
                            value = '­ƒöÆ Ativo' if value.lower() == 'yes' else '­ƒöô Inativo'
                        self._log(f'   {label}: {value}')
                self._log('----------------------------------------')
                return
            except subprocess.TimeoutExpired:
                self._log('ÔÜá´©Å Timeout ao obter informa├º├Áes')
        except Exception as e:
            error_clean = re.sub('[\\\'\\"]?[A-Za-z]:\\\\[^\\s\\\'\\"\\]]+[\\\'\\"]?', '', str(e))
            self._log(f'ÔÜá´©Å {error_clean.strip()}')
    def _parse_device_info(self, raw_output: str) -> Dict[str, str]:
        '''Parseia sa├¡da do getvar all'''
        info = {}
        for line in raw_output.split('\n'):
            line = line.strip()
            if not line or 'Finished' in line:
                continue
            if '(bootloader)' in line:
                line = line.replace('(bootloader)', '').strip()
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    key = re.sub('\\[\\d+\\]', '', key)
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
        if not self.bat_path:
            QMessageBox.warning(self, 'Aviso', 'Selecione uma pasta de firmware primeiro!')
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
        if self.flash_type == FlashType.LOCK:
            warning_text = '<h3>FLASH + LOCK - ATENCAO ESPECIAL</h3>\n            \n<p><b>Este modo ira BLOQUEAR o bootloader apos o flash!</b></p>\n\n<p><b>Antes de continuar, verifique:</b></p>\n<ul>\n<li>A ROM e <b>EXATAMENTE</b> a mesma versao do dispositivo?</li>\n<li>Voce esta usando <b>ROM de engenharia</b> ou e assistencia autorizada?</li>\n<li>O cabo USB e <b>ORIGINAL</b> ou de boa qualidade?</li>\n<li>A bateria esta com <b>MAIS DE 50%</b>?</li>\n</ul>\n\n<p style="color: #1565c0;"><b>INFORMACAO:</b></p>\n<ul>\n<li>Apos o flash, o bootloader sera <b>BLOQUEADO</b></li>\n<li>Ideal para assistencias ou quando a versao e a mesma</li>\n</ul>\n\n<p style="color: #d32f2f;"><b>RISCOS:</b></p>\n<ul>\n<li>Se falhar, o dispositivo pode ficar <b>INUTILIZAVEL</b></li>\n<li>Nao sera possivel desbloquear sem conta Mi autorizada</li>\n<li>Anti-rollback pode impedir qualquer recuperacao</li>\n</ul>\n'
        else:
            bootloader_req = "<b style='color:#d32f2f;'>BOOTLOADER DEVE ESTAR DESBLOQUEADO!</b>"
            warning_text = f'<h3>ATENCAO - PROCEDIMENTO DE RISCO</h3>\n            \n<p>{bootloader_req}</p>\n<p>Se o bootloader estiver bloqueado, o erro "Not allowed in locked state" sera exibido.</p>\n\n<p><b>Antes de continuar, verifique:</b></p>\n<ul>\n<li>A ROM e <b>COMPATIVEL</b> com este modelo exato (codename)?</li>\n<li>O <b>BOOTLOADER</b> esta <b>DESBLOQUEADO</b>?</li>\n<li>O cabo USB e <b>ORIGINAL</b> ou de boa qualidade?</li>\n<li>A bateria esta com <b>MAIS DE 50%</b>?</li>\n<li>O dispositivo esta em modo <b>FASTBOOT</b>?</li>\n</ul>\n\n<p style="color: #d32f2f;"><b>RISCOS:</b></p>\n<ul>\n<li>Flash de ROM incompativel pode BRICKAR o dispositivo</li>\n<li>Erro de Anti-rollback pode inutilizar o aparelho</li>\n<li>Desconexao durante o processo pode danificar o aparelho</li>\n</ul>\n'
        risk_msg.setTextFormat(Qt.RichText)
        risk_msg.setText(warning_text)
        risk_msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        risk_msg.setDefaultButton(QMessageBox.No)
        risk_msg.button(QMessageBox.Yes).setText('Entendi os riscos, CONTINUAR')
        risk_msg.button(QMessageBox.No).setText('Cancelar')
        if risk_msg.exec_() != QMessageBox.Yes:
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
        self.select_btn.setEnabled(False)
        images_folder = os.path.join(self.firmware_folder, 'images')
        if not os.path.exists(images_folder):
            images_folder = self.firmware_folder
        self.worker = XiaomiFlashWorker(self.fastboot_path, commands, images_folder)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.log_signal.connect(self._log)
        self.worker.status_signal.connect((lambda s: None))
        self.worker.finished_signal.connect(self._on_flash_finished)
        self.worker.start()
    def _generate_commands(self, partitions: List[PartitionInfo]) -> List[str]:
        '''Gera lista de comandos fastboot'''
        commands = []
        images_folder = os.path.join(self.firmware_folder, 'images')
        if not os.path.exists(images_folder):
            images_folder = self.firmware_folder
        for partition in partitions:
            if partition.operation != 'flash':
                continue
            if partition.file_exists:
                file_path = os.path.join(images_folder, partition.filename)
                commands.append(f'flash {partition.name} "{file_path}"')
        if self.flash_type == FlashType.LOCK:
            commands.append('oem lock')
        commands.append('reboot')
        return commands
    def cancel_flash(self):
        '''Cancela o flash em andamento'''
        if self.worker:
            if self.worker.isRunning():
                self.worker.stop()
                self._log('\nÔÜá´©Å Cancelamento solicitado...')
    def _on_flash_finished(self, success: bool, message: str):
        '''Callback quando flash termina'''
        self.btn_flash.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.select_btn.setEnabled(True)
        if success:
            QMessageBox.information(self, 'Sucesso', message)
            return
        QMessageBox.warning(self, 'Aten├º├úo', message)
class XiaomiFlashWindow(QWidget):
    '''Janela standalone para teste'''
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Xiaomi Flash Tool - TECH UNION SOLUTIONS')
        self.setMinimumSize(1000, 700)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.flash_widget = XiaomiFlashToolWidget()
        layout.addWidget(self.flash_widget)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = XiaomiFlashWindow()
    window.show()
    sys.exit(app.exec_())
