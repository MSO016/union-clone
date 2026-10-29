'''
SAMSUNG FLASH TOOL - Interface PyQt5 para Odin4
=================================================
TECH UNION SOLUTIONS - Ferramenta de Flash Samsung
Vers├úo: 1.2.0
Baseado em: Odin4 v1.2.13
Funcionalidades:
- Flash de firmware Samsung (BL, AP, CP, CSC, UMS)
- Detec├º├úo autom├ítica de dispositivos
- Verifica├º├úo MD5 autom├ítica
- Op├º├Áes avan├ºadas (nand erase, reboot, etc.)
- Avisos de seguran├ºa robustos
- Verifica├º├úo de integridade do Odin4 com auto-reparo
IMPORTANTE - RISCOS:
- Hard brick poss├¡vel em dispositivos novos (S25 series)
- Knox counter incrementado irreversivelmente
- Perda de garantia
- N├âO interromper o processo ap├│s iniciado
O Odin4 descompacta automaticamente arquivos .tar.md5, .lz4, .gz
usando bibliotecas LZ4 e Crypto++ internas.
'''
import os
import sys
import subprocess
import hashlib
import zipfile
import shutil
from typing import (Optional, List, Dict)
from dataclasses import dataclass
from enum import Enum
def _mensagem_amigavel_usb_acesso_negado(mensagem_odin: str) -> Optional[str]:
    '''
    Trata apenas o erro t├¡pico do Odin4 quando a porta COM/USB n├úo abre no Windows
    (permiss├úo, driver ou outro programa usando a porta). Retorna texto para o usu├írio
    ou None se for outro tipo de falha.
    '''
    if not mensagem_odin:
        return
    m = mensagem_odin.lower()
    m_compact = m.replace(' ', '')
    if 'usbopenfail' not in m_compact and 'usb open fail' not in m:
        return
    if 'acesso negado' not in m and 'access denied' not in m:
        return
    return f'O Windows n├úo liberou o acesso ├á porta USB do aparelho (modo Download).\n\nSugest├Áes:\nÔÇó Feche Samsung Smart Switch, Odin, Z3X, Octoplus e ferramentas similares.\nÔÇó Desconecte o cabo, espere alguns segundos e conecte de novo (prefer├¬ncia: porta USB traseira do PC).\nÔÇó Se persistir, abra o TECH UNION como administrador.\nÔÇó No Gerenciador de dispositivos, confira o driver do aparelho Samsung.\n\nRefer├¬ncia: {mensagem_odin.strip()}'
ODIN4_EXPECTED_MD5 = '16C15504E09238D54B3DE2AD016DB5F2'
ODIN4_EXPECTED_SIZE = 685568
def calculate_file_md5(filepath: str) -> str:
    '''Calcula o MD5 de um arquivo'''
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter((lambda: f.read(4096)), b''):
                hash_md5.update(chunk)
    except Exception:
        return ''
    return hash_md5.hexdigest().upper()
def verify_odin_integrity(odin_path: str, backup_zip_path: str) -> tuple:
    '''
Verifica a integridade do odin4.exe e repara se necess├írio.
Returns:
    (bool, str): (sucesso, mensagem)
'''
    if not os.path.exists(odin_path):
        if os.path.exists(backup_zip_path):
            try:
                with zipfile.ZipFile(backup_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(os.path.dirname(odin_path))
            except Exception as e:
                return False, f'Erro ao extrair backup: {e}'
            return verify_odin_integrity(odin_path, backup_zip_path)
        return (False, 'odin4.exe n├úo encontrado e backup n├úo dispon├¡vel')
    file_size = os.path.getsize(odin_path)
    if file_size != ODIN4_EXPECTED_SIZE:
        if os.path.exists(backup_zip_path):
            try:
                os.remove(odin_path)
                with zipfile.ZipFile(backup_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(os.path.dirname(odin_path))
            except Exception as e:
                return False, f'Erro ao reparar: {e}'
            return True, f'Arquivo reparado do backup (tamanho incorreto: {file_size})'
        return False, f'Arquivo corrompido (tamanho: {file_size}, esperado: {ODIN4_EXPECTED_SIZE})'
    file_md5 = calculate_file_md5(odin_path)
    if file_md5 != ODIN4_EXPECTED_MD5:
        if os.path.exists(backup_zip_path):
            try:
                os.remove(odin_path)
                with zipfile.ZipFile(backup_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(os.path.dirname(odin_path))
            except Exception as e:
                return False, f'Erro ao reparar: {e}'
            return (True, 'Arquivo reparado do backup (MD5 incorreto)')
        return False, f'MD5 incorreto: {file_md5}'
    return (True, 'Integridade verificada OK')
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QFrame, QMessageBox, QFileDialog, QGroupBox, QCheckBox, QTextEdit, QLineEdit, QComboBox, QApplication, QMainWindow, QGridLayout, QSplitter, QScrollArea, QSizePolicy)
from PyQt5.QtCore import (QThread, pyqtSignal, Qt, QTimer, QSize)
from PyQt5.QtGui import (QFont, QIcon, QColor, QPalette, QTextCursor)
RESPONSIVE_LAYOUT_FIX = True
class CoresUnion:
    '''Cores padr├úo do sistema TECH UNION SOLUTIONS - Tema Samsung'''
    BACKGROUND = '#f5f5f5'
    BACKGROUND_DARK = '#e8e8e8'
    BACKGROUND_WHITE = '#ffffff'
    BACKGROUND_CARD = '#ffffff'
    PRIMARY = '#1428A0'
    PRIMARY_HOVER = '#0D1B69'
    PRIMARY_LIGHT = '#4169E1'
    SUCCESS = '#27ae60'
    ERROR = '#e74c3c'
    WARNING = '#f39c12'
    INFO = '#3498db'
    TEXT = '#2c3e50'
    TEXT_MUTED = '#7f8c8d'
    TEXT_WHITE = '#ffffff'
    BORDER = '#bdc3c7'
    BORDER_DARK = '#95a5a6'
    SLOT_BL = '#1428A0'
    SLOT_AP = '#27ae60'
    SLOT_CP = '#9b59b6'
    SLOT_CSC = '#e67e22'
    SLOT_UMS = '#16a085'
class FlashMode(Enum):
    '''Modos de flash dispon├¡veis'''
    NORMAL = 'normal'
    REBOOT = 'reboot'
    NO_REBOOT = 'noreboot'
    REDOWNLOAD = 'redownload'
@dataclass
class FirmwareFiles:
    '''Estrutura para armazenar os arquivos de firmware'''
    bl: Optional[str] = None
    ap: Optional[str] = None
    cp: Optional[str] = None
    csc: Optional[str] = None
    ums: Optional[str] = None
    def has_any_file(self) -> bool:
        '''Verifica se h├í pelo menos um arquivo selecionado'''
        return any([self.bl, self.ap, self.cp, self.csc, self.ums])
    def get_file_list(self) -> Dict[str, str]:
        '''Retorna dicion├írio com arquivos n├úo nulos'''
        files = {}
        if self.bl:
            files['BL'] = self.bl
        if self.ap:
            files['AP'] = self.ap
        if self.cp:
            files['CP'] = self.cp
        if self.csc:
            files['CSC'] = self.csc
        if self.ums:
            files['UMS'] = self.ums
        return files
@dataclass
class FlashOptions:
    '''Op├º├Áes de flash'''
    nand_erase: bool = False
    ignore_md5: bool = False
    md5_only: bool = False
    reboot_mode: FlashMode = FlashMode.NORMAL
    home_validation: bool = False
    verbose: bool = False
class Odin4Worker(QThread):
    '''
    Thread para executar Odin4 flash.
    '''
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    device_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, odin_path: str, firmware: FirmwareFiles, options: FlashOptions, device_path: Optional[str]=None):
        super().__init__()
        self.odin_path = odin_path
        self.firmware = firmware
        self.options = options
        self.device_path = device_path
        self._cancelado = False
    def cancelar(self):
        '''Cancela a opera├º├úo'''
        self._cancelado = True
    def _log(self, msg: str):
        '''Envia log para a GUI'''
        print(msg, flush=True)
        self.log_signal.emit(msg)
    def _format_cmd_for_log(self, cmd: List[str]) -> str:
        '''Formata o comando para log, mostrando apenas nomes de arquivos'''
        formatted_parts = []
        skip_next = False
        for i, part in enumerate(cmd):
            if skip_next:
                skip_next = False
                continue
            if i == 0:
                formatted_parts.append('odin4')
                continue
            if part in ('-b', '-a', '-c', '-s', '-u') and i + 1 < len(cmd):
                filename = os.path.basename(cmd[i + 1])
                if len(filename) > 40:
                    filename = filename[:37] + '...'
                formatted_parts.append(f'{part} {filename}')
                skip_next = True
            else:
                formatted_parts.append(part)
        return ' '.join(formatted_parts)
    def _build_command(self) -> List[str]:
        '''Constr├│i o comando Odin4'''
        cmd = [self.odin_path]
        if self.firmware.bl:
            cmd.extend(['-b', self.firmware.bl])
        if self.firmware.ap:
            cmd.extend(['-a', self.firmware.ap])
        if self.firmware.cp:
            cmd.extend(['-c', self.firmware.cp])
        if self.firmware.csc:
            cmd.extend(['-s', self.firmware.csc])
        if self.firmware.ums:
            cmd.extend(['-u', self.firmware.ums])
        if self.options.nand_erase:
            cmd.append('-e')
        if self.options.ignore_md5:
            cmd.append('--ignore-md5')
        if self.options.md5_only:
            cmd.append('--md5sum-only')
        if self.options.verbose:
            cmd.append('--verbose')
        if self.options.reboot_mode == FlashMode.REBOOT:
            cmd.append('--reboot')
        elif self.options.reboot_mode == FlashMode.NO_REBOOT:
            cmd.append('--noreboot')
        elif self.options.reboot_mode == FlashMode.REDOWNLOAD:
            cmd.append('--redownload')
        if self.device_path:
            cmd.extend(['-d', self.device_path])
        return cmd
    def run(self):
        try:
            if not os.path.exists(self.odin_path):
                self._log('ÔØî ERRO: odin4.exe n├úo encontrado!')
                self.finished_signal.emit(False, 'odin4.exe n├úo encontrado')
                self.status_signal.emit('error')
                return
            if not self.firmware.has_any_file():
                self._log('ÔØî ERRO: Nenhum arquivo de firmware selecionado!')
                self.finished_signal.emit(False, 'Nenhum arquivo selecionado')
                self.status_signal.emit('error')
                return
            for slot, path in self.firmware.get_file_list().items():
                if os.path.exists(path):
                    continue
                self._log(f'ÔØî ERRO: Arquivo {slot} n├úo encontrado: {path}')
                self.finished_signal.emit(False, f'Arquivo {slot} n├úo encontrado')
                self.status_signal.emit('error')
                return
            self._log('============================================================')
            self._log('  TECH UNION SOLUTIONS - SAMSUNG FLASH TOOL')
            self._log('  Powered by Odin4 v1.2.13')
            self._log('============================================================')
            self._log('')
            self._log('­ƒôü ARQUIVOS SELECIONADOS:')
            for slot, path in self.firmware.get_file_list().items():
                filename = os.path.basename(path)
                size_mb = os.path.getsize(path) / 1048576
                self._log(f'   {slot}: {filename} ({size_mb:.1f} MB)')
            self._log('')
            self._log('ÔÜÖ´©Å  OP├ç├òES:')
            self._log(f'   NAND Erase: {'Sim' if self.options.nand_erase else 'N├úo'}')
            self._log(f'   Ignorar MD5: {'Sim' if self.options.ignore_md5 else 'N├úo'}')
            self._log(f'   Modo: {self.options.reboot_mode.value}')
            self._log('')
            self._log('­ƒô▒ Aguardando dispositivo Samsung em modo Download...')
            self._log('   1. Desligue o aparelho')
            self._log('   2. Segure Volume - + Power')
            self._log('   3. Confirme com Volume +')
            self._log('   4. Conecte o cabo USB')
            self._log('')
            self._log('------------------------------------------------------------')
            self.status_signal.emit('waiting')
            self.progress_signal.emit(10)
            cmd = self._build_command()
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            processo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.path.dirname(self.odin_path), creationflags=creationflags)
            flashing = False
            progress = 10
            flash_started = False
            upload_started = False
            files_uploaded = []
            pit_received = False
            connection_closed = False
            current_phase = 'init'
            last_percent = 0
            if self._cancelado:
                processo.kill()
                self._log('\nÔÜá´©Å Opera├º├úo cancelada pelo usu├írio!')
                self.finished_signal.emit(False, 'Cancelado')
                self.status_signal.emit('error')
                return
            linha = processo.stdout.readline()
            if not linha:
                if processo.poll() is not None:
                    pass
            else:
                linha = linha.strip()
                if not linha:
                    pass
                linha_lower = linha.lower()
                linha_upper = linha.upper()
                if '%' in linha and '(' in linha:
                    pass
            try:
                import re
                match = re.search('\\((\\d+)%\\)', linha)
                if match:
                    pct = int(match.group(1))
                    if pct in (25, 50, 75, 100) and pct != last_percent:
                        last_percent = pct
                        if current_phase != 'md5':
                            self._log(f'   ÔûôÔûôÔûô {pct}% conclu├¡do')
                    if upload_started:
                        self.progress_signal.emit(30 + int(pct * 0.65))
            except:
                pass
            else:
                if 'check file' in linha_lower:
                    current_phase = 'md5'
                    filename = linha.split('/')[-1] if '/' in linha else linha.split('\\')[-1]
                    if '.tar' in filename:
                        slot = filename.split('_')[0]
                        self._log(f'\n­ƒôï Verificando {slot}: {filename[:50]}...')
                if 'reboot into' in linha_lower:
                    self._log(f'\n­ƒöä Modo: {linha}')
                if 'com' in linha_lower and 'port' in linha_lower:
                    self._log(f'\n­ƒô▒ Dispositivo detectado: {linha}')
                if linha_lower.startswith('com') and len(linha) < 10:
                    pass
                if 'setup connection' in linha_lower:
                    current_phase = 'connecting'
                    self._log('\n­ƒöî Conectando ao dispositivo...')
                    self.status_signal.emit('flashing')
                if 'initializeconnection' in linha_lower:
                    self._log('   Ô£ô Conex├úo inicializada')
                if 'set partition' in linha_lower:
                    self._log('   Ô£ô Parti├º├úo configurada')
                if 'receive pit' in linha_lower:
                    self._log('   Ô£ô Recebendo tabela de parti├º├Áes...')
                if 'success getpit' in linha_lower or 'getpit' in linha_lower:
                    pit_received = True
                    self._log('   Ô£ô PIT recebido com sucesso')
                    progress = 25
                    self.progress_signal.emit(progress)
                if 'upload binaries' in linha_lower:
                    current_phase = 'uploading'
                    upload_started = True
                    flash_started = True
                    self.status_signal.emit('flashing')
                    self._log('\n==================================================')
                    self._log('­ƒôñ INICIANDO UPLOAD DOS BIN├üRIOS')
                    self._log('==================================================')
                    progress = 30
                    self.progress_signal.emit(progress)
                if upload_started:
                    if '.lz4' not in linha_lower:
                        if '.bin' in linha_lower or '.img' in linha_lower:
                            files_uploaded.append(linha)
                            self._log(f'   ­ƒôü {linha}')
                if 'close connection' in linha_lower:
                    connection_closed = True
                    current_phase = 'closing'
                    self._log('\n­ƒöÆ Fechando conex├úo...')
                if 'PASS!' in linha_upper:
                    self.progress_signal.emit(100)
                    self._log('\n==================================================')
                    self._log('Ô£à FLASH CONCLU├ìDO COM SUCESSO!')
                    self._log(f'   Arquivos enviados: {len(files_uploaded)}')
                    self._log('==================================================')
                    self.finished_signal.emit(True, 'Flash conclu├¡do com sucesso')
                    self.status_signal.emit('success')
                    return
                if 'FAIL' in linha_upper:
                    self._log('\n==================================================')
                    self._log('ÔØî ERRO DURANTE O FLASH!')
                    self._log(f'   Mensagem: {linha}')
                    self._log('==================================================')
                    self.finished_signal.emit(False, linha)
                    self.status_signal.emit('error')
                    return
                exit_code = processo.returncode
                self._log('\n--------------------------------------------------')
                self._log('­ƒôè RESUMO DA OPERA├ç├âO')
                self._log('--------------------------------------------------')
                self._log(f'   C├│digo de sa├¡da: {exit_code}')
                self._log(f'   PIT recebido: {'Ô£ô Sim' if pit_received else 'Ô£ù N├úo'}')
                self._log(f'   Upload iniciado: {'Ô£ô Sim' if upload_started else 'Ô£ù N├úo'}')
                self._log(f'   Arquivos enviados: {len(files_uploaded)}')
                self._log(f'   Conex├úo fechada: {'Ô£ô Sim' if connection_closed else 'Ô£ù N├úo'}')
                if exit_code == 0 and upload_started and len(files_uploaded) > 0 and connection_closed:
                    self.progress_signal.emit(100)
                    self._log('\n==================================================')
                    self._log('Ô£à FLASH CONCLU├ìDO COM SUCESSO!')
                    self._log('==================================================')
                    self._log('\n­ƒÆí O dispositivo deve reiniciar automaticamente.')
                    self.finished_signal.emit(True, f'Flash conclu├¡do - {len(files_uploaded)} arquivos enviados')
                    self.status_signal.emit('success')
                    return
                if exit_code == 0 and pit_received and not upload_started:
                    self._log('\nÔÜá´©Å ATEN├ç├âO: Dispositivo detectado, mas upload n├úo iniciou!')
                    self.finished_signal.emit(False, 'Upload n├úo iniciado')
                    self.status_signal.emit('error')
                    return
                if exit_code == 0 and upload_started and not connection_closed:
                    self._log('\nÔÜá´©Å ATEN├ç├âO: Upload iniciou, mas conex├úo n├úo foi fechada!')
                    self._log('   O processo pode ter sido interrompido.')
                    self.finished_signal.emit(False, 'Processo interrompido')
                    self.status_signal.emit('error')
                    return
                if exit_code == 0:
                    self._log('\nÔÜá´©Å Resultado inconclusivo. Verifique o dispositivo.')
                    self.finished_signal.emit(False, 'Resultado inconclusivo')
                    self.status_signal.emit('error')
                    return
                self._log(f'\nÔØî Processo falhou (c├│digo: {exit_code})')
                self.finished_signal.emit(False, f'C├│digo de sa├¡da: {exit_code}')
                self.status_signal.emit('error')
        except Exception as e:
            self._log(f'\nÔØî EXCE├ç├âO: {str(e)}')
            self.finished_signal.emit(False, str(e))
            self.status_signal.emit('error')
class FileSlotWidget(QFrame):
    '''Widget para um slot de arquivo (BL, AP, CP, CSC, UMS)'''
    file_changed = pyqtSignal(str, str)
    def __init__(self, slot_name: str, slot_color: str, description: str, parent=None):
        super().__init__(parent)
        self.slot_name = slot_name
        self.slot_color = slot_color
        self.file_path = ''
        self.setup_ui(description)
    def setup_ui(self, description: str):
        self.setStyleSheet(f'\n            FileSlotWidget {{\n                background-color: {CoresUnion.BACKGROUND_WHITE};\n                border: 2px solid {CoresUnion.BORDER};\n                border-radius: 8px;\n            }}\n            FileSlotWidget:hover {{\n                border-color: {self.slot_color};\n            }}\n        ')
        if RESPONSIVE_LAYOUT_FIX:
            self.setMinimumHeight(72)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        else:
            self.setMinimumHeight(70)
            self.setMaximumHeight(90)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        indicator = QFrame()
        if RESPONSIVE_LAYOUT_FIX:
            indicator.setFixedWidth(8)
            indicator.setMinimumHeight(48)
            indicator.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        else:
            indicator.setFixedSize(8, 60)
        indicator.setStyleSheet(f'\n            background-color: {self.slot_color};\n            border-radius: 4px;\n        ')
        layout.addWidget(indicator)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        self.title_label = QLabel(self.slot_name)
        self.title_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        self.title_label.setStyleSheet(f'color: {self.slot_color};')
        title_layout.addWidget(self.title_label)
        self.desc_label = QLabel(f'({description})')
        self.desc_label.setFont(QFont('Segoe UI', 9))
        self.desc_label.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        title_layout.addWidget(self.desc_label)
        title_layout.addStretch()
        info_layout.addLayout(title_layout)
        self.file_label = QLabel('Nenhum arquivo selecionado')
        self.file_label.setFont(QFont('Segoe UI', 9))
        self.file_label.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        self.file_label.setWordWrap(False)
        self.file_label.setMinimumWidth(100)
        self.file_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        info_layout.addWidget(self.file_label)
        self.size_label = QLabel('')
        self.size_label.setFont(QFont('Segoe UI', 9))
        self.size_label.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        self.size_label.hide()
        info_layout.addWidget(self.size_label)
        layout.addLayout(info_layout, 1)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)
        btn_layout.setAlignment(Qt.AlignVCenter)
        self.select_btn = QPushButton('Selecionar')
        self.select_btn.setMinimumSize(78, 30)
        self.select_btn.setMaximumSize(110, 34)
        self.select_btn.setCursor(Qt.PointingHandCursor)
        self.select_btn.setStyleSheet(f'\n            QPushButton {{\n                background-color: {self.slot_color};\n                color: white;\n                border: none;\n                border-radius: 4px;\n                padding: 0 10px;\n                font-size: 10px;\n                font-weight: bold;\n            }}\n            QPushButton:hover {{\n                background-color: {CoresUnion.PRIMARY_HOVER};\n            }}\n        ')
        self.select_btn.clicked.connect(self.select_file)
        btn_layout.addWidget(self.select_btn)
        self.clear_btn = QPushButton('Limpar')
        self.clear_btn.setMinimumSize(62, 30)
        self.clear_btn.setMaximumSize(80, 34)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setStyleSheet(f'\n            QPushButton {{\n                background-color: transparent;\n                color: {CoresUnion.TEXT_MUTED};\n                border: 1px solid {CoresUnion.BORDER};\n                border-radius: 4px;\n                padding: 0 8px;\n                font-size: 9px;\n            }}\n            QPushButton:hover {{\n                background-color: {CoresUnion.ERROR};\n                color: white;\n                border-color: {CoresUnion.ERROR};\n            }}\n        ')
        self.clear_btn.clicked.connect(self.clear_file)
        self.clear_btn.setEnabled(False)
        btn_layout.addWidget(self.clear_btn)
        layout.addLayout(btn_layout)
    def select_file(self):
        '''Abre di├ílogo para selecionar arquivo'''
        import os
        default_dir = ''
        try:
            owner = self.window()
            candidate = getattr(owner, '_last_flash_dir', '') if owner is not None else ''
            if candidate and os.path.isdir(candidate):
                default_dir = candidate
        except Exception:
            default_dir = ''
        if not default_dir:
            default_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
            if not os.path.exists(default_dir):
                default_dir = os.path.expanduser('~')
        file_path, _ = QFileDialog.getOpenFileName(self, f'Selecionar arquivo {self.slot_name}', default_dir, 'Samsung Firmware (*.tar.md5 *.tar *.zip *.bin);;Todos os arquivos (*.*)')
        if file_path:
            self.set_file(file_path)
    def set_file(self, file_path: str):
        '''Define o arquivo selecionado'''
        self.file_path = file_path
        filename = os.path.basename(file_path)
        size_mb = os.path.getsize(file_path) / 1048576
        self._full_filename = filename
        self._file_size_text = f'({size_mb:.1f} MB)'
        self._update_file_label_text()
        self.file_label.setStyleSheet(f'color: {CoresUnion.TEXT};')
        self.file_label.setToolTip(f'{filename}\n{self._file_size_text}')
        self.clear_btn.setEnabled(True)
        self.setStyleSheet(f'\n            FileSlotWidget {{\n                background-color: {CoresUnion.BACKGROUND_WHITE};\n                border: 2px solid {self.slot_color};\n                border-radius: 8px;\n            }}\n        ')
        try:
            owner = self.window()
            if owner is not None and hasattr(owner, '_last_flash_dir'):
                owner._last_flash_dir = os.path.dirname(file_path)
        except Exception:
            pass
        self.file_changed.emit(self.slot_name, file_path)
    def _update_file_label_text(self):
        '''Atualiza o texto do label com elide baseado na largura dispon├¡vel'''
        if not hasattr(self, '_full_filename') or not self._full_filename:
            return
        from PyQt5.QtGui import QFontMetrics
        from PyQt5.QtCore import Qt
        fm = QFontMetrics(self.file_label.font())
        available_width = self.file_label.width() - 10
        if available_width < 50:
            available_width = 200
        elided_name = fm.elidedText(self._full_filename, Qt.ElideMiddle, available_width)
        self.file_label.setText(elided_name)
        self.size_label.setText(self._file_size_text)
        self.size_label.show()
    def resizeEvent(self, event):
        '''Atualiza elide quando o widget ├® redimensionado'''
        super().resizeEvent(event)
        if hasattr(self, '_full_filename'):
            if self._full_filename:
                self._update_file_label_text()
    def clear_file(self):
        '''Limpa o arquivo selecionado'''
        self.file_path = ''
        self._full_filename = ''
        self._file_size_text = ''
        self.file_label.setText('Nenhum arquivo selecionado')
        self.file_label.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        self.file_label.setToolTip('')
        self.size_label.setText('')
        self.size_label.hide()
        self.clear_btn.setEnabled(False)
        self.setStyleSheet(f'\n            FileSlotWidget {{\n                background-color: {CoresUnion.BACKGROUND_WHITE};\n                border: 2px solid {CoresUnion.BORDER};\n                border-radius: 8px;\n            }}\n            FileSlotWidget:hover {{\n                border-color: {self.slot_color};\n            }}\n        ')
        self.file_changed.emit(self.slot_name, '')
    def get_file(self) -> str:
        '''Retorna o caminho do arquivo'''
        return self.file_path
class SamsungFlashToolWidget(QWidget):
    '''Widget principal da ferramenta de flash Samsung'''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tools_dir = self._resolve_tools_dir()
        self.odin_path = self._resolve_odin()
        self.odin_backup_path = os.path.join(self.tools_dir, 'odin4_backup.zip')
        self.odin_ok = False
        self.odin_status_msg = ''
        self._verify_odin()
        self.worker = None
        self._last_flash_dir = ''
        self.setup_ui()
    def _resolve_tools_dir(self) -> str:
        try:
            from app.utils.path_manager import PathManager
            tools = PathManager.get_unlock_tools_dir()
            if tools:
                p = os.path.normpath(os.path.join(os.path.dirname(tools), 'flash', 'samsung', 'tools'))
                if os.path.isdir(p):
                    return p
        except Exception:
            pass
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools')
    def _resolve_odin(self) -> str:
        try:
            from app.utils.path_manager import PathManager
            tools = PathManager.get_unlock_tools_dir()
            if tools:
                candidate = os.path.join(tools, 'odin4.exe')
                if os.path.isfile(candidate):
                    return candidate
        except Exception:
            pass
        return os.path.join(self.tools_dir, 'odin4.exe')
    def _verify_odin(self):
        '''Verifica e repara o Odin4 se necess├írio'''
        success, message = verify_odin_integrity(self.odin_path, self.odin_backup_path)
        self.odin_ok = success
        self.odin_status_msg = message
        if not success:
            print(f'[ODIN4] ERRO: {message}')
            return
        print(f'[ODIN4] {message}')
    def setup_ui(self):
        self.setStyleSheet(f'background-color: {CoresUnion.BACKGROUND};')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        header = self._create_header()
        main_layout.addWidget(header)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        left_panel = self._create_file_slots_panel()
        splitter.addWidget(left_panel)
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 500])
        if RESPONSIVE_LAYOUT_FIX:
            splitter.setChildrenCollapsible(False)
            splitter.setStretchFactor(0, 3)
            splitter.setStretchFactor(1, 4)
        main_layout.addWidget(splitter, 1)
        progress_section = self._create_progress_section()
        main_layout.addWidget(progress_section)
        action_bar = self._create_action_bar()
        main_layout.addWidget(action_bar)
    def _create_header(self) -> QFrame:
        '''Cria o cabe├ºalho'''
        header = QFrame()
        header.setStyleSheet(f'\n            QFrame {{\n                background-color: {CoresUnion.PRIMARY};\n                border-radius: 10px;\n            }}\n        ')
        header.setMinimumHeight(60)
        header.setMaximumHeight(80)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(15, 8, 15, 8)
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title = QLabel('SAMSUNG FLASH TOOL')
        title.setFont(QFont('Segoe UI', 18, QFont.Bold))
        title.setStyleSheet(f'color: {CoresUnion.TEXT_WHITE};')
        title_layout.addWidget(title)
        subtitle = QLabel('Powered by Odin4 v1.2.13 | TECH UNION SOLUTIONS')
        subtitle.setFont(QFont('Segoe UI', 9))
        subtitle.setStyleSheet('color: rgba(255,255,255,0.8);')
        title_layout.addWidget(subtitle)
        layout.addLayout(title_layout)
        layout.addStretch()
        status_frame = QFrame()
        status_frame.setMinimumWidth(100)
        status_frame.setStyleSheet('background: transparent;')
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(4)
        status_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if self.odin_ok:
            status_text = 'ÔùÅ Odin4 Pronto'
            color = CoresUnion.SUCCESS
        else:
            status_text = 'ÔùÅ Odin4 ERRO'
            color = CoresUnion.ERROR
        self.odin_status = QLabel(status_text)
        self.odin_status.setFont(QFont('Segoe UI', 9))
        self.odin_status.setStyleSheet(f'color: {color};')
        self.odin_status.setToolTip(self.odin_status_msg)
        status_layout.addWidget(self.odin_status, 0, Qt.AlignRight)
        verify_btn = QPushButton('Verificar')
        verify_btn.setFixedSize(70, 22)
        verify_btn.setFont(QFont('Segoe UI', 8))
        verify_btn.setCursor(Qt.PointingHandCursor)
        verify_btn.setStyleSheet('\n            QPushButton {\n                background-color: rgba(255,255,255,0.2);\n                color: white;\n                border: 1px solid rgba(255,255,255,0.3);\n                border-radius: 4px;\n                padding: 2px 8px;\n            }\n            QPushButton:hover {\n                background-color: rgba(255,255,255,0.3);\n            }\n        ')
        verify_btn.clicked.connect(self._on_verify_odin_clicked)
        status_layout.addWidget(verify_btn, 0, Qt.AlignRight)
        layout.addWidget(status_frame)
        return header
    def _create_file_slots_panel(self) -> QFrame:
        '''Cria o painel de slots de arquivo (com o bloco de op├º├Áes no topo).'''
        panel = QFrame()
        panel.setStyleSheet(f'\n            QFrame {{\n                background-color: {CoresUnion.BACKGROUND_WHITE};\n                border-radius: 10px;\n                border: 1px solid {CoresUnion.BORDER};\n            }}\n        ')
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        options_group = self._create_options_group()
        layout.addWidget(options_group)
        title = QLabel('ARQUIVOS DE FIRMWARE')
        title.setFont(QFont('Segoe UI', 12, QFont.Bold))
        title.setStyleSheet(f'color: {CoresUnion.TEXT};')
        layout.addWidget(title)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('border: none;')
        slots_widget = QWidget()
        slots_layout = QVBoxLayout(slots_widget)
        slots_layout.setSpacing(8)
        self.slot_bl = FileSlotWidget('BL', CoresUnion.SLOT_BL, 'Bootloader')
        self.slot_ap = FileSlotWidget('AP', CoresUnion.SLOT_AP, 'Sistema Android')
        self.slot_cp = FileSlotWidget('CP', CoresUnion.SLOT_CP, 'Modem/Baseband')
        self.slot_csc = FileSlotWidget('CSC', CoresUnion.SLOT_CSC, 'Country Specific')
        self.slot_ums = FileSlotWidget('HOME_CSC', CoresUnion.SLOT_UMS, 'CSC sem Reset')
        slots_layout.addWidget(self.slot_bl)
        slots_layout.addWidget(self.slot_ap)
        slots_layout.addWidget(self.slot_cp)
        slots_layout.addWidget(self.slot_csc)
        slots_layout.addWidget(self.slot_ums)
        slots_layout.addStretch()
        scroll.setWidget(slots_widget)
        layout.addWidget(scroll, 1)
        return panel
    def _create_options_group(self) -> QGroupBox:
        '''Cria o QGroupBox de OP├ç├òES (checkboxes + combo de reboot).
        Extra├¡do do painel direito para o esquerdo: o painel de log passa a
        ocupar toda a altura dispon├¡vel, evitando o encolhimento do terminal
        em zoom 125%/150%. Os atributos self.chk_* e self.combo_reboot s├úo
        preservados exatamente como antes ÔÇö start_flash() l├¬ por atributo.
        '''
        options_group = QGroupBox('OP├ç├òES')
        options_group.setFont(QFont('Segoe UI', 11, QFont.Bold))
        options_group.setStyleSheet(f'\n            QGroupBox {{\n                color: {CoresUnion.TEXT};\n                border: 1px solid {CoresUnion.BORDER};\n                border-radius: 8px;\n                margin-top: 10px;\n                padding-top: 10px;\n            }}\n            QGroupBox::title {{\n                subcontrol-origin: margin;\n                left: 10px;\n                padding: 0 5px;\n            }}\n        ')
        options_layout = QGridLayout(options_group)
        options_layout.setSpacing(10)
        self.chk_nand_erase = QCheckBox('NAND Erase (Limpar dados)')
        self.chk_nand_erase.setFont(QFont('Segoe UI', 10))
        self.chk_nand_erase.setToolTip('Apaga todos os dados do dispositivo antes do flash')
        options_layout.addWidget(self.chk_nand_erase, 0, 0)
        self.chk_ignore_md5 = QCheckBox('Ignorar MD5')
        self.chk_ignore_md5.setFont(QFont('Segoe UI', 10))
        self.chk_ignore_md5.setToolTip('N├úo verifica a integridade dos arquivos')
        options_layout.addWidget(self.chk_ignore_md5, 0, 1)
        self.chk_md5_only = QCheckBox('Apenas verificar MD5')
        self.chk_md5_only.setFont(QFont('Segoe UI', 10))
        self.chk_md5_only.setToolTip('Apenas verifica os arquivos, n├úo faz flash')
        options_layout.addWidget(self.chk_md5_only, 1, 0)
        self.chk_verbose = QCheckBox('Modo detalhado')
        self.chk_verbose.setFont(QFont('Segoe UI', 10))
        self.chk_verbose.setToolTip('Mostra informa├º├Áes detalhadas no log')
        options_layout.addWidget(self.chk_verbose, 1, 1)
        reboot_layout = QHBoxLayout()
        reboot_label = QLabel('Ap├│s flash:')
        reboot_label.setFont(QFont('Segoe UI', 10))
        reboot_layout.addWidget(reboot_label)
        self.combo_reboot = QComboBox()
        self.combo_reboot.addItems(['Reiniciar normalmente', 'N├úo reiniciar', 'Reiniciar em Download Mode'])
        self.combo_reboot.setFont(QFont('Segoe UI', 10))
        _arrow_rule = ''
        try:
            from app.utils.path_manager import PathManager
            _svg_path = PathManager.get_resource_path(os.path.join('icons_svg', 'seta_down.svg'))
            if _svg_path and os.path.isfile(_svg_path):
                _svg_url = str(_svg_path).replace('\\', '/')
                _arrow_rule = f'QComboBox::down-arrow {{ image: url("{_svg_url}"); width: 12px; height: 12px; }}'
        except Exception:
            _arrow_rule = ''
        self.combo_reboot.setStyleSheet(f'\n            QComboBox {{\n                padding: 5px 28px 5px 10px;\n                border: 1px solid {CoresUnion.BORDER};\n                border-radius: 4px;\n                background-color: {CoresUnion.BACKGROUND_WHITE};\n                color: {CoresUnion.TEXT};\n                min-width: 180px;\n            }}\n            QComboBox:hover {{\n                border-color: {CoresUnion.PRIMARY};\n            }}\n            QComboBox::drop-down {{\n                subcontrol-origin: padding;\n                subcontrol-position: center right;\n                width: 24px;\n                border: none;\n                border-left: 1px solid {CoresUnion.BORDER};\n                background: {CoresUnion.BACKGROUND};\n            }}\n            {_arrow_rule}\n            QComboBox QAbstractItemView {{\n                background-color: {CoresUnion.BACKGROUND_WHITE};\n                color: {CoresUnion.TEXT};\n                selection-background-color: {CoresUnion.PRIMARY};\n                selection-color: {CoresUnion.TEXT_WHITE};\n                border: 1px solid {CoresUnion.BORDER};\n                padding: 5px;\n            }}\n            QComboBox QAbstractItemView::item {{\n                padding: 8px 10px;\n                min-height: 25px;\n            }}\n            QComboBox QAbstractItemView::item:hover {{\n                background-color: {CoresUnion.PRIMARY_LIGHT};\n                color: {CoresUnion.TEXT_WHITE};\n            }}\n        ')
        reboot_layout.addWidget(self.combo_reboot, 1)
        options_layout.addLayout(reboot_layout, 2, 0, 1, 2)
        options_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        return options_group
    def _create_right_panel(self) -> QFrame:
        '''Cria o painel direito com o log (op├º├Áes migraram para o painel esquerdo).'''
        panel = QFrame()
        panel.setStyleSheet(f'\n            QFrame {{\n                background-color: {CoresUnion.BACKGROUND_WHITE};\n                border-radius: 10px;\n                border: 1px solid {CoresUnion.BORDER};\n            }}\n        ')
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        log_label = QLabel('LOG DE EXECU├ç├âO')
        log_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        log_label.setStyleSheet(f'color: {CoresUnion.TEXT};')
        layout.addWidget(log_label)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont('Consolas', 9))
        self.log_text.setStyleSheet(f'\n            QTextEdit {{\n                background-color: #1e1e1e;\n                color: #d4d4d4;\n                border: 1px solid {CoresUnion.BORDER};\n                border-radius: 8px;\n                padding: 10px;\n            }}\n        ')
        self.log_text.setPlaceholderText('Os logs da opera├º├úo aparecer├úo aqui...')
        if RESPONSIVE_LAYOUT_FIX:
            self.log_text.setMinimumHeight(80)
            self.log_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.log_text.setLineWrapMode(QTextEdit.WidgetWidth)
        layout.addWidget(self.log_text, 1)
        return panel
    def _create_progress_section(self) -> QFrame:
        '''Cria a se├º├úo de progresso'''
        section = QFrame()
        section.setStyleSheet(f'\n            QFrame {{\n                background-color: {CoresUnion.BACKGROUND_WHITE};\n                border-radius: 10px;\n                border: 1px solid {CoresUnion.BORDER};\n            }}\n        ')
        section.setMinimumHeight(70)
        section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)
        status_layout = QHBoxLayout()
        self.status_label = QLabel('ÔùÅ Aguardando')
        self.status_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        self.status_label.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        self.percent_label = QLabel('0%')
        self.percent_label.setFont(QFont('Segoe UI', 14, QFont.Bold))
        self.percent_label.setStyleSheet(f'color: {CoresUnion.PRIMARY};')
        status_layout.addWidget(self.percent_label)
        layout.addLayout(status_layout)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setStyleSheet(f'\n            QProgressBar {{\n                background-color: {CoresUnion.BACKGROUND_DARK};\n                border-radius: 6px;\n            }}\n            QProgressBar::chunk {{\n                background-color: {CoresUnion.PRIMARY};\n                border-radius: 6px;\n            }}\n        ')
        layout.addWidget(self.progress_bar)
        return section
    def _create_action_bar(self) -> QFrame:
        '''Cria a barra de a├º├Áes'''
        bar = QFrame()
        bar.setMinimumHeight(50)
        bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.btn_detect_device = QPushButton('Detectar Dispositivo')
        self.btn_detect_device.setMinimumHeight(40)
        self.btn_detect_device.setMaximumHeight(50)
        self.btn_detect_device.setCursor(Qt.PointingHandCursor)
        self.btn_detect_device.setFont(QFont('Segoe UI', 10))
        self.btn_detect_device.setStyleSheet(f'\n            QPushButton {{\n                background-color: {CoresUnion.BACKGROUND_WHITE};\n                color: {CoresUnion.TEXT};\n                border: 2px solid {CoresUnion.PRIMARY};\n                border-radius: 8px;\n                padding: 0 20px;\n            }}\n            QPushButton:hover {{\n                background-color: {CoresUnion.PRIMARY};\n                color: {CoresUnion.TEXT_WHITE};\n            }}\n        ')
        self.btn_detect_device.clicked.connect(self.detect_samsung_device)
        layout.addWidget(self.btn_detect_device)
        layout.addStretch()
        self.btn_cancel = QPushButton('Cancelar')
        self.btn_cancel.setMinimumSize(100, 40)
        self.btn_cancel.setMaximumSize(140, 50)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setStyleSheet(f'\n            QPushButton {{\n                background-color: {CoresUnion.ERROR};\n                color: white;\n                border: none;\n                border-radius: 8px;\n            }}\n            QPushButton:hover {{\n                background-color: #c0392b;\n            }}\n            QPushButton:disabled {{\n                background-color: {CoresUnion.BORDER};\n            }}\n        ')
        self.btn_cancel.clicked.connect(self.cancel_flash)
        layout.addWidget(self.btn_cancel)
        self.btn_flash = QPushButton('INICIAR FLASH')
        self.btn_flash.setMinimumSize(150, 40)
        self.btn_flash.setMaximumSize(200, 50)
        self.btn_flash.setCursor(Qt.PointingHandCursor)
        self.btn_flash.setFont(QFont('Segoe UI', 11, QFont.Bold))
        self.btn_flash.setStyleSheet(f'\n            QPushButton {{\n                background-color: {CoresUnion.PRIMARY};\n                color: white;\n                border: none;\n                border-radius: 8px;\n            }}\n            QPushButton:hover {{\n                background-color: {CoresUnion.PRIMARY_HOVER};\n            }}\n            QPushButton:disabled {{\n                background-color: {CoresUnion.BORDER};\n            }}\n        ')
        self.btn_flash.clicked.connect(self.start_flash)
        layout.addWidget(self.btn_flash)
        return bar
    def detect_samsung_device(self):
        '''
        Detecta dispositivo Samsung e obt├®m informa├º├Áes detalhadas.
        Usa comunica├º├úo serial com comando AT DVIF.
        '''
        self.log_text.clear()
        self.append_log('=======================================================')
        self.append_log('  DETECTANDO DISPOSITIVO SAMSUNG')
        self.append_log('=======================================================')
        self.append_log('')
        try:
            import serial
            import serial.tools.list_ports
            import re
            SAMSUNG_VID = 1256
            self.append_log('Buscando portas Samsung...')
            samsung_ports = []
            for port in serial.tools.list_ports.comports():
                vid = getattr(port, 'vid', None)
                desc = str(getattr(port, 'description', '')).lower()
                if vid != SAMSUNG_VID:
                    if not any((k in desc for k in ('samsung', 'mobile', 'modem'))):
                        continue
                port_type = 'MODEM' if getattr(port, 'pid', 0) == 26717 or 'modem' in desc else 'Samsung'
                samsung_ports.append({'port': port.device, 'desc': port.description, 'type': port_type})
            if not samsung_ports:
                self.append_log('[!] Nenhuma porta Samsung encontrada.')
                self._show_download_mode_instructions()
                return
            self.append_log(f'[OK] {len(samsung_ports)} porta(s) encontrada(s):')
            for p in samsung_ports:
                self.append_log(f'   - {p['port']} ({p['type']})')
            self.append_log('')
            self.append_log('Obtendo informacoes do dispositivo...')
            target_port = samsung_ports[0]['port']
        except ImportError:
            self.append_log('[!] Modulo de comunicacao serial nao disponivel.')
            self.append_log('   Usando metodo basico (Odin4)...')
            self.append_log('')
            self._detect_with_odin()
        except Exception:
            self.append_log('[!] Falha ao detectar dispositivo.')
            self._show_download_mode_instructions()
        try:
            ser = serial.Serial(port=target_port, baudrate=115200, timeout=2.0, write_timeout=3.0, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
            import time
            time.sleep(1.0)
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            for cmd in ('AT', 'ATZ', 'ATE0'):
                ser.write(f'{cmd}\r\n'.encode('ascii'))
                time.sleep(0.3)
                if ser.in_waiting > 0:
                    ser.read(ser.in_waiting)
            self.append_log('   Comunicando com dispositivo...')
            dvif_formats = ['DVIF\r\n', 'DVIF\r', 'AT+DVIF\r\n']
            response = ''
            for cmd_format in dvif_formats:
                ser.reset_input_buffer()
                ser.write(cmd_format.encode('ascii'))
                start_time = time.time()
                buffer = ''
                while time.time() - start_time < 3.0:
                    if ser.in_waiting > 0:
                        chunk = ser.read(ser.in_waiting)
                        buffer += chunk.decode('ascii', errors='ignore')
                        if '@#' in buffer:
                            time.sleep(0.5)
                            if ser.in_waiting > 0:
                                buffer += ser.read(ser.in_waiting).decode('ascii', errors='ignore')
                            response = buffer
                            break
                    time.sleep(0.01)
                if response:
                    break
                time.sleep(0.3)
                continue
            ser.close()
            if response and '@#' in response:
                self.append_log('   [OK] Resposta recebida!')
                self.append_log('')
                blocks = re.findall('@#(.*?)@#', response)
                parsed_data = {}
                for block in blocks:
                    pairs = block.split(';')
                    for pair in pairs:
                        if '=' in pair:
                            key, value = pair.split('=', 1)
                            parsed_data[key.strip().lower()] = value.strip()
                if parsed_data:
                    self.append_log('=======================================================')
                    self.append_log('  INFORMACOES DO DISPOSITIVO')
                    self.append_log('=======================================================')
                    field_map = {'model': ('Modelo', ''), 'vendor': ('Fabricante', ''), 'capa': ('Capacidade', 'GB'), 'sales': ('Regiao/CSC', ''), 'ver': ('Versao Firmware', ''), 'un': ('Numero Unico', ''), 'fwver': ('Versao FW', ''), 'product': ('Codigo Produto', ''), 'did': ('Device ID', ''), 'tmu_temp': ('Temperatura', 'C'), 'imei': ('IMEI', ''), 'sn': ('Serial', '')}
                    shown_fields = 0
                    for key, (label, suffix) in field_map.items():
                        if key in parsed_data:
                            value = parsed_data[key]
                            self.append_log(f'   {label}: {value}{suffix}')
                            shown_fields += 1
                    for key, value in parsed_data.items():
                        if key in field_map:
                            continue
                        if not value:
                            continue
                        if len(value) < 50:
                            self.append_log(f'   {key}: {value}')
                            shown_fields += 1
                    self.append_log('')
                    self.append_log('=======================================================')
                    self.append_log(f'   Total: {shown_fields} informacoes obtidas')
                    self.append_log('=======================================================')
                    return
                self.append_log('[!] Resposta recebida mas sem dados parseaveis.')
                return
            self.append_log('[!] Nao foi possivel obter informacoes.')
            self.append_log('')
            self.append_log('Possiveis causas:')
            self.append_log('   - Dispositivo nao esta em modo correto')
            self.append_log('   - Modelo nao suporta este comando')
            self.append_log('   - Porta serial ocupada')
            self.append_log('')
            self._detect_with_odin()
            return
        except serial.SerialException as e:
            err_str = str(e).lower()
            if 'acesso negado' in err_str or 'access denied' in err_str or 'permissionerror' in err_str:
                self.append_log(f'[!] A porta {target_port} esta sendo usada por outro programa.')
                self.append_log('')
                self.append_log('Resolucao rapida:')
                self.append_log('   - Feche Smart Switch, Odin, Z3X ou similares')
                self.append_log('   - Desconecte o cabo e reconecte')
                self.append_log('   - Tente executar como Administrador')
            elif 'filenotfounderror' in err_str or 'not found' in err_str:
                self.append_log(f'[!] Porta {target_port} nao disponivel.')
                self.append_log('   Verifique se o dispositivo esta conectado.')
            else:
                self.append_log('[!] Nao foi possivel comunicar com a porta serial.')
                self.append_log('   Verifique conexao e drivers do dispositivo.')
            self.append_log('')
            self._detect_with_odin()
        e = None
        del e
        if PermissionError, OSError:
            self.append_log(f'[!] Acesso negado a porta {target_port}.')
            self.append_log('   Feche outros programas que usam a porta e tente novamente.')
            self.append_log('')
            self._detect_with_odin()
    def _detect_with_odin(self):
        '''Detecta dispositivo usando apenas Odin4'''
        try:
            result = subprocess.run([self.odin_path, '--list'], capture_output=True, text=True, cwd=os.path.dirname(self.odin_path), creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            output = result.stdout + result.stderr
            if output.strip():
                self.append_log('Dispositivos encontrados (modo Download):')
                for line in output.strip().split('\n'):
                    if line.strip():
                        self.append_log(f'   {line}')
                return
            self.append_log('[!] Nenhum dispositivo em modo Download.')
            self._show_download_mode_instructions()
            return
        except Exception:
            self.append_log('[!] Falha ao consultar Odin4.')
    def _show_download_mode_instructions(self):
        '''Mostra instrucoes para entrar no modo Download'''
        self.append_log('')
        self.append_log('Para detectar o dispositivo:')
        self.append_log('   1. Desligue o aparelho')
        self.append_log('   2. Segure Volume - + Power')
        self.append_log('   3. Confirme com Volume +')
        self.append_log('   4. Conecte o cabo USB')
        self.append_log('')
        self.append_log('Certifique-se que os drivers Samsung estao instalados.')
    def _on_verify_odin_clicked(self):
        '''Verifica e repara o Odin4'''
        self.append_log('\n==================================================')
        self.append_log('­ƒöì VERIFICANDO INTEGRIDADE DO ODIN4...')
        self.append_log('==================================================')
        self._verify_odin()
        if self.odin_ok:
            self.odin_status.setText('ÔùÅ Odin4 Pronto')
            self.odin_status.setStyleSheet(f'color: {CoresUnion.SUCCESS};')
            self.append_log(f'Ô£à {self.odin_status_msg}')
            file_size = os.path.getsize(self.odin_path)
            file_md5 = calculate_file_md5(self.odin_path)
            self.append_log(f'   Tamanho: {file_size} bytes')
            self.append_log(f'   MD5: {file_md5}')
            QMessageBox.information(self, 'Odin4 OK', f'Verifica├º├úo conclu├¡da com sucesso!\n\nTamanho: {file_size} bytes\nMD5: {file_md5}')
        else:
            self.odin_status.setText('ÔùÅ Odin4 ERRO')
            self.odin_status.setStyleSheet(f'color: {CoresUnion.ERROR};')
            self.append_log(f'ÔØî {self.odin_status_msg}')
            QMessageBox.critical(self, 'Erro no Odin4', f"N├úo foi poss├¡vel verificar/reparar o Odin4!\n\nErro: {self.odin_status_msg}\n\nCertifique-se que o arquivo 'odin4_backup.zip' existe na pasta 'tools'.")
        self.odin_status.setToolTip(self.odin_status_msg)
    def start_flash(self):
        '''Inicia o processo de flash'''
        self._verify_odin()
        if not self.odin_ok:
            QMessageBox.critical(self, 'Odin4 Corrompido', f"O Odin4 est├í corrompido ou ausente!\n\nErro: {self.odin_status_msg}\n\nClique em 'Verificar' no cabe├ºalho para tentar reparar.")
            return
        firmware = FirmwareFiles(bl=self.slot_bl.get_file() or None, ap=self.slot_ap.get_file() or None, cp=self.slot_cp.get_file() or None, csc=self.slot_csc.get_file() or None, ums=self.slot_ums.get_file() or None)
        if not firmware.has_any_file():
            QMessageBox.warning(self, 'Nenhum arquivo', 'Selecione pelo menos um arquivo de firmware para continuar.')
            return
        warning_msg = QMessageBox(self)
        warning_msg.setIcon(QMessageBox.Warning)
        warning_msg.setWindowTitle('AVISO DE SEGURANCA')
        warning_msg.setText("<b>ATEN├ç├âO: Opera├º├úo de ALTO RISCO!</b><br><br>O flash de firmware Samsung pode resultar em:<br><br>ÔÇó <b>HARD BRICK</b> - Dispositivo inutilizado permanentemente<br>ÔÇó <b>SOFT BRICK</b> - Bootloop, n├úo inicializa<br>ÔÇó <b>PERDA TOTAL DE DADOS</b><br>ÔÇó <b>KNOX INCREMENTADO</b> - Irrevers├¡vel, perde garantia<br>ÔÇó <b>PERDA DE GARANTIA</b><br><br><span style='color:red;'><b>N├âO DESLIGUE O APARELHO OU DESCONECTE O CABO DURANTE O PROCESSO!</b></span>")
        warning_msg.setInformativeText('Voc├¬ entende os riscos e deseja continuar?')
        warning_msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        warning_msg.setDefaultButton(QMessageBox.No)
        if warning_msg.exec_() != QMessageBox.Yes:
            return
        if (firmware.ap or firmware.cp or firmware.csc) and not firmware.bl:
            reply = QMessageBox.warning(self, 'Bootloader n├úo selecionado', 'Voc├¬ N├âO selecionou um arquivo de Bootloader (BL).\n\nFlash sem BL pode causar problemas se a vers├úo do bootloader\natual for incompat├¡vel com o firmware.\n\nRecomenda├º├úo: Incluir BL para flash mais seguro.\n\nDeseja continuar mesmo assim?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        files_str = '\n'.join([f'  ÔÇó {k}: {os.path.basename(v)}' for k, v in firmware.get_file_list().items()])
        nand_warning = ''
        if self.chk_nand_erase.isChecked():
            nand_warning = '\n\nÔÜá´©Å NAND ERASE ATIVADO!\nTODOS OS DADOS SER├âO APAGADOS PERMANENTEMENTE!'
        final_msg = QMessageBox(self)
        final_msg.setIcon(QMessageBox.Question)
        final_msg.setWindowTitle('Confirmar Flash')
        final_msg.setText(f"<b>Arquivos a serem flashados:</b><br><br><pre>{files_str}</pre><span style='color:red;'>{nand_warning}</span>")
        final_msg.setInformativeText('├ÜLTIMA CONFIRMA├ç├âO:\n\nÔÇó Bateria est├í acima de 60%?\nÔÇó Cabo USB ├® de boa qualidade?\nÔÇó Firmware ├® do modelo CORRETO?\n\nIniciar o flash?')
        final_msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        final_msg.setDefaultButton(QMessageBox.No)
        if final_msg.exec_() != QMessageBox.Yes:
            return
        reboot_modes = [FlashMode.REBOOT, FlashMode.NO_REBOOT, FlashMode.REDOWNLOAD]
        options = FlashOptions(nand_erase=self.chk_nand_erase.isChecked(), ignore_md5=self.chk_ignore_md5.isChecked(), md5_only=self.chk_md5_only.isChecked(), verbose=self.chk_verbose.isChecked(), reboot_mode=reboot_modes[self.combo_reboot.currentIndex()])
        self.log_text.clear()
        self.progress_bar.setValue(0)
        self.percent_label.setText('0%')
        self.update_status('waiting', 'Aguardando dispositivo...')
        self.btn_flash.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.worker = Odin4Worker(self.odin_path, firmware, options)
        self.worker.log_signal.connect(self.append_log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.status_signal.connect(self.on_status_change)
        self.worker.finished_signal.connect(self.on_flash_finished)
        self.worker.start()
    def cancel_flash(self):
        '''Cancela o flash em andamento'''
        if self.worker:
            if self.worker.isRunning():
                reply = QMessageBox.question(self, 'Cancelar', 'Tem certeza que deseja cancelar o flash?\n\nÔÜá´©Å Isso pode deixar o dispositivo em estado inconsistente!', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.worker.cancelar()
    def append_log(self, msg: str):
        '''Adiciona mensagem ao log'''
        self.log_text.append(msg)
        self.log_text.moveCursor(QTextCursor.End)
    def update_progress(self, value: int):
        '''Atualiza a barra de progresso'''
        self.progress_bar.setValue(value)
        self.percent_label.setText(f'{value}%')
    def update_status(self, status: str, text: str):
        '''Atualiza o status'''
        colors = {'waiting': CoresUnion.WARNING, 'flashing': CoresUnion.INFO, 'success': CoresUnion.SUCCESS, 'error': CoresUnion.ERROR}
        color = colors.get(status, CoresUnion.TEXT_MUTED)
        self.status_label.setText(f'ÔùÅ {text}')
        self.status_label.setStyleSheet(f'color: {color};')
    def on_status_change(self, status: str):
        '''Callback de mudan├ºa de status'''
        texts = {'waiting': 'Aguardando dispositivo...', 'flashing': 'Fazendo flash...', 'success': 'Conclu├¡do com sucesso!', 'error': 'Erro durante o processo'}
        self.update_status(status, texts.get(status, status))
        if status == 'success':
            self.progress_bar.setStyleSheet(f'\n                QProgressBar {{\n                    background-color: {CoresUnion.BACKGROUND_DARK};\n                    border-radius: 6px;\n                }}\n                QProgressBar::chunk {{\n                    background-color: {CoresUnion.SUCCESS};\n                    border-radius: 6px;\n                }}\n            ')
            return
        if status == 'error':
            self.progress_bar.setStyleSheet(f'\n                QProgressBar {{\n                    background-color: {CoresUnion.BACKGROUND_DARK};\n                    border-radius: 6px;\n                }}\n                QProgressBar::chunk {{\n                    background-color: {CoresUnion.ERROR};\n                    border-radius: 6px;\n                }}\n            ')
    def on_flash_finished(self, success: bool, message: str):
        '''Callback quando o flash termina'''
        self.btn_flash.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        if success:
            QMessageBox.information(self, 'Sucesso', f'Flash conclu├¡do com sucesso!\n\n{message}')
            return
        amigavel = _mensagem_amigavel_usb_acesso_negado(message)
        if amigavel:
            QMessageBox.critical(self, 'USB ÔÇö acesso negado', amigavel)
            return
        QMessageBox.critical(self, 'Erro', f'Erro durante o flash:\n\n{message}')
class SamsungFlashWindow(QMainWindow):
    '''Janela principal para teste standalone'''
    def __init__(self):
        super().__init__()
        self.setWindowTitle('TECH UNION - Samsung Flash Tool')
        self.setMinimumSize(1000, 700)
        self.resize(1100, 750)
        self.setCentralWidget(SamsungFlashToolWidget())
        self.setStyleSheet(f'background-color: {CoresUnion.BACKGROUND};')
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = SamsungFlashWindow()
    window.show()
    sys.exit(app.exec_())
# WARNING: Decompyle incomplete
