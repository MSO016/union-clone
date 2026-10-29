from __future__ import annotations
import ctypes
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import (Dict, List, Optional, Tuple)
from PyQt5.QtCore import (Qt, QThread, pyqtSignal)
from PyQt5.QtWidgets import (QApplication, QDialog, QFrame, QHBoxLayout, QLabel, QMessageBox, QProgressBar, QPushButton, QTextEdit, QVBoxLayout)
_CREATE_NO_WINDOW = 134217728
_USBDK_FALLBACK_URL = 'https://github.com/daynix/UsbDk/releases/download/v1.00-22/UsbDk_1.0.22_x64.msi'
_WINFSP_FALLBACK_URL = 'https://github.com/winfsp/winfsp/releases/download/v2.1/winfsp-2.1.25156.msi'
_TIMEOUT_INSTALL = 1200
_TIMEOUT_DOWNLOAD = 600
_TIMEOUT_QUERY = 10
def _is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False
def _program_files() -> Path:
    return Path(os.environ.get('ProgramFiles', 'C:\\Program Files'))
def _program_files_x86() -> Path:
    return Path(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'))
def _which_winget() -> Optional[str]:
    return shutil.which('winget')
def _run_silent(cmd: List[str], timeout: int=_TIMEOUT_QUERY) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout, creationflags=_CREATE_NO_WINDOW)
        return proc.returncode, proc.stdout or '', proc.stderr or ''
    except subprocess.TimeoutExpired:
        return (-1, '', 'timeout')
    except FileNotFoundError:
        return (-2, '', 'not_found')
    except PermissionError:
        return (-3, '', 'permission_denied')
    except Exception:
        return (-4, '', 'unknown_error')
def find_usbdk_controller() -> Optional[Path]:
    pf = _program_files()
    for candidate in pf / 'UsbDk Runtime Library' / 'UsbDkController.exe', pf / 'UsbDk' / 'UsbDkController.exe':
        try:
            if candidate.exists():
                return candidate
        except Exception:
            continue
def is_usbdk_installed() -> bool:
    return find_usbdk_controller() is not None
def is_winfsp_installed() -> bool:
    pf = _program_files()
    pf86 = _program_files_x86()
    for path in pf / 'WinFsp', pf86 / 'WinFsp':
        try:
            if path.exists():
                return True
        except Exception:
            continue
    return False
def status_dependencias() -> dict:
    return {'usbdk': is_usbdk_installed(), 'winfsp': is_winfsp_installed(), 'winget': _which_winget() is not None, 'admin': _is_admin()}
_DRIVERS_CFG = {'mediatek': {'nome': 'MediaTek USB VCOM', 'tipo': 'r2_file', 'arquivo_r2': 'drivers/MTK.exe', 'inf_provider': 'MediaTek', 'registry_hints': ['SYSTEM\\CurrentControlSet\\Services\\mdmcpq']}, 'qualcomm': {'nome': 'Qualcomm QDLoader 9008', 'tipo': 'r2_file', 'arquivo_r2': 'drivers/QDLoader HS-USB Driver_64bit_Setup.exe', 'inf_provider': 'Qualcomm', 'registry_hints': ['SYSTEM\\CurrentControlSet\\Services\\qcusbser', 'SYSTEM\\CurrentControlSet\\Services\\QCUSB_BULK']}, 'spd': {'nome': 'SPD / Unisoc USB', 'tipo': 'r2_folder', 'prefixo_r2': 'drivers/SPDPK2/', 'executavel': '64install.exe', 'inf_provider': 'Spreadtrum', 'registry_hints': ['SYSTEM\\CurrentControlSet\\Services\\sprdvcom', 'SYSTEM\\CurrentControlSet\\Services\\sprdadb']}, 'vcredist': {'nome': 'Visual C++ Redist', 'tipo': 'http_silent', 'urls': [('vc_redist.x64.exe', 'https://aka.ms/vc14/vc_redist.x64.exe'), ('vc_redist.x86.exe', 'https://aka.ms/vc14/vc_redist.x86.exe')], 'args_silent': ['/install', '/quiet', '/norestart'], 'registry_hints': ['SOFTWARE\\Microsoft\\VisualStudio\\14.0\\VC\\Runtimes\\x64'], 'inf_provider': None}, 'dotnet8': {'nome': '.NET 8.0 Desktop Runtime', 'tipo': 'http_interactive', 'urls': [('windowsdesktop-runtime-8.0.28-win-x64.exe', 'https://builds.dotnet.microsoft.com/dotnet/WindowsDesktop/8.0.28/windowsdesktop-runtime-8.0.28-win-x64.exe')], 'registry_hints': ['SOFTWARE\\dotnet\\Setup\\InstalledVersions\\x64\\sharedfx\\Microsoft.WindowsDesktop.App'], 'inf_provider': None}}
def _check_registry_key(hints: List[str]) -> bool:
    import winreg
    for path in hints:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
            winreg.CloseKey(key)
        except (FileNotFoundError, OSError):
            continue
        return True
    return False
def _check_pnputil_provider(provider: str) -> bool:
    if not provider:
        return False
    try:
        rc, out, _err = _run_silent(['pnputil.exe', '/enum-drivers'], timeout=15)
        if rc == 0:
            return provider.lower() in out.lower()
    except Exception:
        pass
    return False
def _check_dotnet8_runtime() -> bool:
    try:
        rc, out, _err = _run_silent(['dotnet', '--list-runtimes'], timeout=10)
        if rc == 0:
            return 'Microsoft.WindowsDesktop.App 8.' in out
    except Exception:
        pass
    return False
def is_driver_installed(key: str) -> bool:
    cfg = _DRIVERS_CFG.get(key)
    if not cfg:
        return False
    if _check_registry_key(cfg.get('registry_hints', [])):
        return True
    if cfg.get('inf_provider') and _check_pnputil_provider(cfg['inf_provider']):
        return True
    if key == 'dotnet8':
        return _check_dotnet8_runtime()
    return False
class _InstallerWorker(QThread):
    progresso = pyqtSignal(int, str)
    concluido = pyqtSignal(bool, str)
    def __init__(self, alvos: List[str], parent=None):
        super().__init__(parent)
        self._alvos = [a for a in alvos if a in ('usbdk', 'winfsp')]
        self._needs_reboot = False
        self._cancelado = False
    def cancelar(self) -> None:
        self._cancelado = True
    def run(self) -> None:
        try:
            if not self._alvos:
                self.concluido.emit(True, 'Nenhuma instalacao necessaria.')
                return
            total = len(self._alvos)
            for idx, alvo in enumerate(self._alvos):
                if self._cancelado:
                    self.concluido.emit(False, 'Operacao cancelada.')
                    return
                base_pct = int(idx * 100 / total)
                self.progresso.emit(base_pct, f'Instalando {self._nome_amigavel(alvo)}...')
                ok = self._instalar(alvo)
                if not ok:
                    self.concluido.emit(False, f'Nao foi possivel instalar {self._nome_amigavel(alvo)}.')
                    return
                self.progresso.emit(int((idx + 1) * 100 / total), f'{self._nome_amigavel(alvo)} pronto.')
            msg = 'Dependencias instaladas com sucesso.'
            if self._needs_reboot:
                msg += ' (recomendado reiniciar o Windows)'
            self.concluido.emit(True, msg)
            return
        except Exception:
            self.concluido.emit(False, 'Nao foi possivel concluir.')
    @staticmethod
    def _nome_amigavel(alvo: str) -> str:
        return {'usbdk': 'UsbDk', 'winfsp': 'WinFsp'}.get(alvo, alvo)
    def _instalar(self, alvo: str) -> bool:
        if alvo == 'usbdk':
            if is_usbdk_installed():
                return True
            if self._instalar_via_winget('daynix.UsbDk'):
                return True
            return self._instalar_via_msi(_USBDK_FALLBACK_URL, 'usbdk')
        if alvo == 'winfsp':
            if is_winfsp_installed():
                return True
            if self._instalar_via_winget('WinFsp.WinFsp'):
                return True
            return self._instalar_via_msi(_WINFSP_FALLBACK_URL, 'winfsp')
        return False
    def _instalar_via_winget(self, pkg_id: str) -> bool:
        if not _which_winget():
            return False
        rc, _out, _err = _run_silent(['winget', 'install', '--id', pkg_id, '--source', 'winget', '-e', '--accept-package-agreements', '--accept-source-agreements', '--disable-interactivity'], timeout=_TIMEOUT_INSTALL)
        if rc == 3010:
            self._needs_reboot = True
            return True
        return rc == 0
    def _instalar_via_msi(self, url: str, tag: str) -> bool:
        try:
            tmp = Path(tempfile.gettempdir()) / f'_tus_dep_{tag}.msi'
            self.progresso.emit(40, 'Baixando instalador oficial...')
            req = urllib.request.Request(url, headers={'User-Agent': 'TUS-Installer/1.0'})
            with urllib.request.urlopen(req, timeout=_TIMEOUT_DOWNLOAD) as resp:
                status = getattr(resp, 'status', 200) or 200
                if status >= 400:
                    return False
                with open(tmp, 'wb') as fh:
                    shutil.copyfileobj(resp, fh)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError):
            return False
        except Exception:
            return False
        self.progresso.emit(70, 'Executando instalador oficial...')
        rc, _out, _err = _run_silent(['msiexec', '/i', str(tmp), '/qb', '/norestart'], timeout=_TIMEOUT_INSTALL)
        try:
            tmp.unlink()
        except Exception:
            pass
        if rc == 3010:
            self._needs_reboot = True
            return True
        return rc == 0
class _DriverWorker(QThread):
    '''Worker para download e instalacao de drivers de chipset e runtimes.'''
    progresso = pyqtSignal(int, str)
    concluido = pyqtSignal(bool, str)
    def __init__(self, driver_key: str, parent=None):
        super().__init__(parent)
        self._key = driver_key
        self._cancelado = False
    def cancelar(self) -> None:
        self._cancelado = True
    def run(self) -> None:
        cfg = _DRIVERS_CFG.get(self._key)
        if not cfg:
            self.concluido.emit(False, 'Driver desconhecido.')
            return
        try:
            tipo = cfg['tipo']
            if tipo == 'r2_file':
                self._install_r2_file(cfg)
                return
            if tipo == 'r2_folder':
                self._install_r2_folder(cfg)
                return
            if tipo == 'http_silent':
                self._install_http_silent(cfg)
                return
            if tipo == 'http_interactive':
                self._install_http_interactive(cfg)
                return
            self.concluido.emit(False, 'Tipo desconhecido.')
            return
        except Exception:
            self.concluido.emit(False, 'Falha na instalacao.')
    def _get_s3(self):
        import boto3
        from botocore.config import Config as BotoConfig
        from app.utils._app_cfg import REFS
        return boto3.client('s3', endpoint_url=REFS.R2_EP, aws_access_key_id=REFS.R2_AK, aws_secret_access_key=REFS.R2_SK, region_name='auto', config=BotoConfig(signature_version='s3v4', connect_timeout=15, read_timeout=300, retries=dict(max_attempts=3, mode='adaptive'), request_checksum_calculation='WHEN_REQUIRED', response_checksum_validation='WHEN_REQUIRED')), REFS.R2_BK
    def _install_r2_file(self, cfg: dict) -> None:
        nome = cfg['nome']
        self.progresso.emit(5, f'Baixando {nome}...')
        s3, bucket = self._get_s3()
        total = 0
        try:
            head = s3.head_object(Bucket=bucket, Key=cfg['arquivo_r2'])
            total = int(head.get('ContentLength') or 0)
        except Exception:
            pass
        tmp_dir = Path(tempfile.gettempdir()) / '_tus_drivers'
        tmp_dir.mkdir(exist_ok=True)
        destino = str(tmp_dir / os.path.basename(cfg['arquivo_r2']))
        transferido = {'n': 0}
        def _cb(amount):
            transferido['n'] += int(amount or 0)
            if total > 0:
                pct = min(90, int(transferido['n'] / total * 85) + 5)
                try:
                    self.progresso.emit(pct, f'Baixando {nome}...')
                    return
                except Exception:
                    pass
        s3.download_file(bucket, cfg['arquivo_r2'], destino, Callback=_cb)
        if not os.path.isfile(destino) or os.path.getsize(destino) == 0:
            self.concluido.emit(False, 'Download falhou.')
            return
        self.progresso.emit(95, 'Abrindo instalador...')
        os.startfile(destino)
        self.progresso.emit(100, 'Instalador aberto.')
        self.concluido.emit(True, f"{nome}: instalador aberto.\n\nSiga os passos na tela (Next > Next > Finish).\nApos concluir, clique em 'Verificar' para confirmar.")
    def _install_r2_folder(self, cfg: dict) -> None:
        nome = cfg['nome']
        self.progresso.emit(5, f'Baixando {nome}...')
        s3, bucket = self._get_s3()
        prefix = cfg['prefixo_r2']
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        objetos = [o for o in resp.get('Contents', []) if not o['Key'].endswith('/')]
        if not objetos:
            self.concluido.emit(False, 'Pasta vazia no servidor.')
            return
        tmp_dir = Path(tempfile.gettempdir()) / '_tus_drivers' / 'SPDPK2'
        tmp_dir.mkdir(parents=True, exist_ok=True)
        total_files = len(objetos)
        for idx, obj in enumerate(objetos):
            if self._cancelado:
                self.concluido.emit(False, 'Cancelado.')
                return
            key = obj['Key']
            rel_path = key[len(prefix):]
            local_path = tmp_dir / rel_path.replace('/', os.sep)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            pct = int(5 + idx / total_files * 80)
            self.progresso.emit(pct, f'Baixando {rel_path}...')
            s3.download_file(bucket, key, str(local_path))
        exe_path = str(tmp_dir / cfg['executavel'])
        if not os.path.isfile(exe_path):
            self.concluido.emit(False, 'Executavel nao encontrado.')
            return
        self.progresso.emit(95, 'Abrindo instalador SPD...')
        os.startfile(exe_path)
        self.progresso.emit(100, 'Instalador aberto.')
        self.concluido.emit(True, f"{nome}: instalador aberto.\n\nSiga os passos na tela (Next > Next > Finish).\nApos concluir, clique em 'Verificar' para confirmar.")
    def _install_http_interactive(self, cfg: dict) -> None:
        nome = cfg['nome']
        urls = cfg['urls']
        if not urls:
            self.concluido.emit(False, 'URL nao configurada.')
            return
        filename, url = urls[0]
        tmp_dir = Path(tempfile.gettempdir()) / '_tus_drivers'
        tmp_dir.mkdir(exist_ok=True)
        destino = str(tmp_dir / filename)
        self.progresso.emit(10, f'Baixando {nome}...')
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'TUS/1.0'})
            with urllib.request.urlopen(req, timeout=120) as resp:
                with open(destino, 'wb') as fh:
                    shutil.copyfileobj(resp, fh)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError):
            self.concluido.emit(False, 'Download falhou.')
        if not os.path.isfile(destino) or os.path.getsize(destino) == 0:
            self.concluido.emit(False, 'Download falhou.')
            return
        self.progresso.emit(95, 'Abrindo instalador...')
        os.startfile(destino)
        self.progresso.emit(100, 'Instalador aberto.')
        self.concluido.emit(True, f"{nome}: instalador aberto.\n\nSiga os passos na tela (Next > Next > Finish).\nApos concluir, clique em 'Verificar' para confirmar.")
    def _install_http_silent(self, cfg: dict) -> None:
        nome = cfg['nome']
        urls = cfg['urls']
        args_silent = cfg.get('args_silent', [])
        tmp_dir = Path(tempfile.gettempdir()) / '_tus_drivers'
        tmp_dir.mkdir(exist_ok=True)
        total_urls = len(urls)
        for idx, (filename, url) in enumerate(urls):
            if self._cancelado:
                self.concluido.emit(False, 'Cancelado.')
                return
            base_pct = int(idx / total_urls * 80)
            self.progresso.emit(base_pct + 5, f'Baixando {filename}...')
            destino = str(tmp_dir / filename)
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'TUS/1.0'})
                with urllib.request.urlopen(req, timeout=120) as resp:
                    with open(destino, 'wb') as fh:
                        shutil.copyfileobj(resp, fh)
            except (urllib.error.URLError, urllib.error.HTTPError, OSError):
                self.concluido.emit(False, f'Falha ao baixar {filename}.')
                return
            if not os.path.isfile(destino) or os.path.getsize(destino) == 0:
                self.concluido.emit(False, f'Download vazio: {filename}')
                return
            pct_install = base_pct + 40
            self.progresso.emit(min(90, pct_install), f'Instalando {filename}...')
            try:
                _run_silent([destino] + args_silent, timeout=_TIMEOUT_INSTALL)
            except Exception:
                pass
            try:
                os.remove(destino)
            except Exception:
                pass
            continue
        self._verificar(cfg)
    def _verificar(self, cfg: dict) -> None:
        import time
        self.progresso.emit(98, 'Verificando...')
        time.sleep(1)
        if is_driver_installed(self._key):
            self.progresso.emit(100, 'Instalado!')
            self.concluido.emit(True, f'{cfg['nome']} instalado com sucesso!')
            return
        self.progresso.emit(100, 'Concluido.')
        self.concluido.emit(True, 'Instalador encerrado. Conecte o dispositivo para confirmar.')
def listar_dispositivos_usbdk(timeout: int=_TIMEOUT_QUERY) -> Tuple[bool, List[str]]:
    ctrl = find_usbdk_controller()
    if not ctrl:
        return False, []
    rc, out, _err = _run_silent([str(ctrl), '-n'], timeout=timeout)
    if rc != 0:
        return False, []
    linhas = []
    for raw in out.splitlines():
        linha = raw.strip()
        if linha:
            linhas.append(linha)
    return True, linhas
_CAT_FLASH = 'flash'
_CAT_SMARTPHONE = 'smartphone'
_CAT_SERIAL = 'serial'
_CAT_SYSTEM = 'system'
_CAT_UNKNOWN = 'unknown'
_DEVICE_MAP: 'Dict[str, Tuple[str, str, str]]' = {'0e8d:0003': (_CAT_FLASH, 'MediaTek', 'BROM (pronto para flash)'), '0e8d:2000': (_CAT_FLASH, 'MediaTek', 'Preloader'), '0e8d:2001': (_CAT_FLASH, 'MediaTek', 'Preloader / Download Agent'), '0e8d:201c': (_CAT_FLASH, 'MediaTek', 'BROM (variante)'), '0e8d:20ff': (_CAT_FLASH, 'MediaTek', 'Preloader'), '0e8d:3000': (_CAT_FLASH, 'MediaTek', 'Preloader'), '0e8d:6000': (_CAT_FLASH, 'MediaTek', 'Preloader'), '0e8d:200a': (_CAT_SMARTPHONE, 'MediaTek', 'Conectado (modo modem)'), '0e8d:200c': (_CAT_SMARTPHONE, 'MediaTek', 'Conectado (modo modem)'), '0e8d:200e': (_CAT_SMARTPHONE, 'MediaTek', 'Conectado (porta serial)'), '1004:6000': (_CAT_FLASH, 'LG', 'Preloader MTK'), '22d9:0006': (_CAT_FLASH, 'Oppo', 'Preloader MTK'), '0fce:f200': (_CAT_FLASH, 'Sony', 'BROM'), '0fce:d1e9': (_CAT_FLASH, 'Sony', 'BROM XA1'), '0fce:d1e2': (_CAT_FLASH, 'Sony', 'BROM'), '0fce:d1ec': (_CAT_FLASH, 'Sony', 'BROM L1'), '0fce:d1dd': (_CAT_FLASH, 'Sony', 'BROM F3111'), '0fce:b00b': (_CAT_FLASH, 'Sony', 'Flash'), '05c6:9008': (_CAT_FLASH, 'Qualcomm', 'EDL ÔÇö HS-USB QDLoader 9008'), '05c6:900e': (_CAT_FLASH, 'Qualcomm', 'EDL ÔÇö QDLoader (variante)'), '05c6:9025': (_CAT_FLASH, 'Qualcomm', 'HS-USB QDLoader'), '05c6:9006': (_CAT_SMARTPHONE, 'Qualcomm', 'Conectado (diagn├│stico)'), '05c6:f000': (_CAT_FLASH, 'Qualcomm', 'Streaming Download'), '05c6:9091': (_CAT_SMARTPHONE, 'Qualcomm', 'Conectado (modem)'), '05c6:90db': (_CAT_SMARTPHONE, 'Qualcomm', 'Conectado (modem)'), '05c6:676c': (_CAT_SMARTPHONE, 'Qualcomm', 'Conectado (diagn├│stico)'), '04e8:685d': (_CAT_FLASH, 'Samsung', 'Download (Odin)'), '04e8:6860': (_CAT_SMARTPHONE, 'Samsung', 'Conectado (modo arquivos)'), '04e8:6863': (_CAT_SMARTPHONE, 'Samsung', 'Fastboot'), '2717:ff48': (_CAT_FLASH, 'Xiaomi', 'EDL'), '2717:ff40': (_CAT_SMARTPHONE, 'Xiaomi', 'Recovery'), '2717:ff60': (_CAT_SMARTPHONE, 'Xiaomi', 'Conectado (modo arquivos)'), '2717:ff68': (_CAT_SMARTPHONE, 'Xiaomi', 'Fastboot'), '1782:4d00': (_CAT_SMARTPHONE, 'Spreadtrum / Unisoc', 'Conectado (diagn├│stico)'), '1782:4d04': (_CAT_FLASH, 'Spreadtrum / Unisoc', 'Download'), '12d1:1052': (_CAT_SMARTPHONE, 'Huawei', 'Conectado (porta serial)'), '12d1:107e': (_CAT_SMARTPHONE, 'Huawei', 'HiSuite'), '12d1:1031': (_CAT_SMARTPHONE, 'Huawei', 'Conectado (depura├º├úo)'), '12d1:1038': (_CAT_SMARTPHONE, 'Huawei', 'Conectado (modo arquivos)'), '18d1:4ee0': (_CAT_SMARTPHONE, 'Android', 'Conectado (modo arquivos)'), '18d1:4ee1': (_CAT_SMARTPHONE, 'Android', 'Conectado (modo arquivos)'), '18d1:4ee2': (_CAT_SMARTPHONE, 'Android', 'Conectado (depura├º├úo)'), '18d1:4ee7': (_CAT_SMARTPHONE, 'Android', 'Conectado (depura├º├úo)'), '18d1:d00d': (_CAT_FLASH, 'Android', 'Fastboot'), '22b8:2e76': (_CAT_SMARTPHONE, 'Motorola', 'Conectado (modo arquivos)'), '22b8:2e80': (_CAT_FLASH, 'Motorola', 'Fastboot'), '0403:6001': (_CAT_SERIAL, 'FTDI', 'USB-Serial FT232'), '0403:6010': (_CAT_SERIAL, 'FTDI', 'USB-Serial FT2232'), '0403:6014': (_CAT_SERIAL, 'FTDI', 'USB-Serial FT232H'), '0403:6015': (_CAT_SERIAL, 'FTDI', 'USB-Serial FT231X'), '1a86:7523': (_CAT_SERIAL, 'CH340', 'USB-Serial CH340C'), '1a86:55d3': (_CAT_SERIAL, 'CH343', 'USB-Serial CH343G'), '1a86:5523': (_CAT_SERIAL, 'CH341', 'USB-Serial'), '1a86:5512': (_CAT_SERIAL, 'CH341A', 'USB-Serial'), '4348:5523': (_CAT_SERIAL, 'WCH', 'USB-Serial CH340'), '10c4:ea60': (_CAT_SERIAL, 'Silicon Labs', 'USB-Serial CP2102'), '10c4:ea70': (_CAT_SERIAL, 'Silicon Labs', 'USB-Serial CP2105'), '067b:2303': (_CAT_SERIAL, 'Prolific', 'USB-Serial PL2303')}
_KNOWN_VENDOR_LABEL: 'Dict[str, str]' = {'0e8d': 'MediaTek', '1004': 'LG', '05c6': 'Qualcomm', '04e8': 'Samsung', '2717': 'Xiaomi', '1782': 'Spreadtrum / Unisoc', '0fce': 'Sony', '12d1': 'Huawei', '18d1': 'Android', '22b8': 'Motorola', '2a70': 'OnePlus', '22d9': 'Oppo', '2a45': 'Meizu', '1ebf': 'ZTE', '0bb4': 'HTC', '0403': 'FTDI', '1a86': 'QinHeng', '4348': 'WCH', '10c4': 'Silicon Labs', '11ca': 'Silicon Labs', '067b': 'Prolific'}
_SYSTEM_VENDORS = {'046d', '0480', '05e3', '0bda', '0db0', '1462', '1d6b', '214b', '258a', '8086', '8087'}
_SMARTPHONE_VENDOR_PREFIXES = {'04e8', '05c6', '0bb4', '0e8d', '0fce', '1004', '12d1', '1782', '18d1', '1ebf', '22b8', '22d9', '2717', '2a45', '2a70'}
_VID_PID_RE = re.compile('ID\\s*:\\s*([0-9a-fA-F]{4})\\s*:\\s*([0-9a-fA-F]{4})')
def _classify_device(vid: str, pid: str) -> Tuple[str, str, str]:
    key = f'{vid}:{pid}'
    if key in _DEVICE_MAP:
        return _DEVICE_MAP[key]
    vendor_lbl = _KNOWN_VENDOR_LABEL.get(vid, '')
    if vid in _SMARTPHONE_VENDOR_PREFIXES:
        return _CAT_SMARTPHONE, vendor_lbl or 'Smartphone', 'Conectado'
    if vid in _SYSTEM_VENDORS:
        return _CAT_SYSTEM, vendor_lbl or 'Sistema', 'Dispositivo do computador'
    if vendor_lbl:
        return _CAT_UNKNOWN, vendor_lbl, 'Conectado'
    return _CAT_UNKNOWN, '', 'Dispositivo USB gen├®rico'
def _parse_usbdk_output(linhas: List[str]) -> List[Dict[str, str]]:
    devices = []
    for linha in linhas or []:
        m = _VID_PID_RE.search(linha)
        if m:
            vid = m.group(1).lower()
            pid = m.group(2).lower()
            category, vendor, mode = _classify_device(vid, pid)
            devices.append({'vid': vid, 'pid': pid, 'key': f'{vid}:{pid}', 'category': category, 'vendor': vendor, 'mode': mode})
    return devices
def analisar_dispositivos_usbdk(timeout: int=_TIMEOUT_QUERY) -> Dict[str, object]:
    ok, linhas = listar_dispositivos_usbdk(timeout=timeout)
    if not ok:
        return {'ok': False, 'total': 0, 'devices': [], 'flash_devices': [], 'smartphone_devices': [], 'serial_devices': [], 'system_count': 0}
    parsed = _parse_usbdk_output(linhas)
    flash_seen = set()
    flash_devices = []
    smartphone_seen = set()
    smartphone_devices = []
    serial_seen = set()
    serial_devices = []
    system_count = 0
    for d in parsed:
        cat = d['category']
        vendor = d['vendor']
        mode = d['mode']
        label = f'{vendor} ÔÇö {mode}' if vendor else mode
        if cat == _CAT_FLASH:
            if label not in flash_seen:
                flash_seen.add(label)
                flash_devices.append(label)
        elif cat == _CAT_SMARTPHONE:
            if label not in smartphone_seen:
                smartphone_seen.add(label)
                smartphone_devices.append(label)
        elif cat == _CAT_SERIAL:
            if label not in serial_seen:
                serial_seen.add(label)
                serial_devices.append(label)
        elif cat == _CAT_SYSTEM:
            system_count += 1
    return {'ok': True, 'total': len(parsed), 'devices': parsed, 'flash_devices': flash_devices, 'smartphone_devices': smartphone_devices, 'serial_devices': serial_devices, 'system_count': system_count}
def abrir_gerenciador_dispositivos() -> bool:
    try:
        subprocess.Popen(['cmd', '/c', 'start', '', 'devmgmt.msc'], creationflags=_CREATE_NO_WINDOW, shell=False)
        return True
    except Exception:
        pass
class UsbRequirementsDialog(QDialog):
    _STYLE = '\n        QDialog {\n            background-color: #ffffff;\n        }\n        QLabel#title {\n            font-size: 16px;\n            font-weight: 700;\n            color: #0D47A1;\n        }\n        QLabel#subtitle {\n            color: #455a64;\n        }\n        QFrame#status_card {\n            background-color: #f5f7fb;\n            border: 1px solid #e0e7f1;\n            border-radius: 8px;\n            padding: 12px;\n        }\n        QLabel.status_line {\n            font-size: 13px;\n            padding: 3px 0px;\n            min-height: 18px;\n        }\n        QPushButton {\n            padding: 8px 14px;\n            border-radius: 6px;\n            font-weight: 600;\n        }\n        QPushButton#primary {\n            background-color: #0D47A1;\n            color: white;\n            border: 1px solid #0D47A1;\n        }\n        QPushButton#primary:disabled {\n            background-color: #90a4ae;\n            border: 1px solid #90a4ae;\n            color: #eceff1;\n        }\n        QPushButton#secondary {\n            background-color: #ffffff;\n            color: #0D47A1;\n            border: 1px solid #0D47A1;\n        }\n        QPushButton#danger {\n            background-color: #ffffff;\n            color: #455a64;\n            border: 1px solid #cfd8dc;\n        }\n        QProgressBar {\n            border: 1px solid #cfd8dc;\n            border-radius: 6px;\n            text-align: center;\n            background-color: #eceff1;\n            color: #263238;\n            font-weight: 600;\n            min-height: 18px;\n        }\n        QProgressBar::chunk {\n            background-color: #0D47A1;\n            border-radius: 6px;\n        }\n        QTextEdit#log {\n            background-color: #fafbfc;\n            color: #263238;\n            border: 1px solid #e0e7f1;\n            border-radius: 6px;\n            font-family: Consolas, monospace;\n            font-size: 12px;\n        }\n    '
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Conex├úo USB ÔÇö Depend├¬ncias')
        self.setMinimumSize(680, 560)
        self.setStyleSheet(self._STYLE)
        self._worker = None
        self._drv_worker = None
        self._build_ui()
        self._refresh_status()
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        title = QLabel('Depend├¬ncias para Conex├úo USB Est├ível')
        title.setObjectName('title')
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        subtitle = QLabel('Estas bibliotecas s├úo necess├írias para comunica├º├úo USB com dispositivos em modos avan├ºados de manuten├º├úo e diagn├│stico.')
        subtitle.setObjectName('subtitle')
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        card = QFrame()
        card.setObjectName('status_card')
        card_l = QVBoxLayout(card)
        card_l.setSpacing(6)
        self.lbl_usbdk = QLabel('UsbDk: ...')
        self.lbl_usbdk.setProperty('class', 'status_line')
        self.lbl_winfsp = QLabel('WinFsp: ...')
        self.lbl_winfsp.setProperty('class', 'status_line')
        self.lbl_mtk = QLabel('MediaTek: ...')
        self.lbl_mtk.setProperty('class', 'status_line')
        self.lbl_qcom = QLabel('Qualcomm: ...')
        self.lbl_qcom.setProperty('class', 'status_line')
        self.lbl_spd = QLabel('SPD: ...')
        self.lbl_spd.setProperty('class', 'status_line')
        self.lbl_vcredist = QLabel('VC++ Redist: ...')
        self.lbl_vcredist.setProperty('class', 'status_line')
        self.lbl_dotnet = QLabel('.NET 8.0: ...')
        self.lbl_dotnet.setProperty('class', 'status_line')
        self.lbl_extra = QLabel('')
        self.lbl_extra.setProperty('class', 'status_line')
        self.lbl_extra.setWordWrap(True)
        for lbl in self.lbl_usbdk, self.lbl_winfsp, self.lbl_mtk, self.lbl_qcom, self.lbl_spd, self.lbl_vcredist, self.lbl_dotnet, self.lbl_extra:
            lbl.setWordWrap(True)
            lbl.setTextFormat(Qt.RichText)
            lbl.setMinimumWidth(200)
            card_l.addWidget(lbl)
        layout.addWidget(card)
        self.progresso = QProgressBar()
        self.progresso.setRange(0, 100)
        self.progresso.setValue(0)
        self.progresso.setVisible(False)
        layout.addWidget(self.progresso)
        self.log = QTextEdit()
        self.log.setObjectName('log')
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(120)
        self.log.setVisible(False)
        layout.addWidget(self.log)
        row1 = QHBoxLayout()
        self.btn_install_missing = QPushButton('Instalar Faltantes')
        self.btn_install_missing.setObjectName('primary')
        self.btn_reinstall = QPushButton('Reinstalar Todas')
        self.btn_reinstall.setObjectName('secondary')
        row1.addWidget(self.btn_install_missing)
        row1.addWidget(self.btn_reinstall)
        layout.addLayout(row1)
        row_drv = QHBoxLayout()
        row_drv.setSpacing(6)
        self.btn_mtk = QPushButton('MTK')
        self.btn_mtk.setObjectName('secondary')
        self.btn_mtk.setToolTip('Instalar driver MediaTek USB VCOM')
        self.btn_qcom = QPushButton('QCOM')
        self.btn_qcom.setObjectName('secondary')
        self.btn_qcom.setToolTip('Instalar driver Qualcomm QDLoader 9008')
        self.btn_spd = QPushButton('SPD')
        self.btn_spd.setObjectName('secondary')
        self.btn_spd.setToolTip('Instalar driver SPD / Unisoc')
        self.btn_vcredist = QPushButton('VC++')
        self.btn_vcredist.setObjectName('secondary')
        self.btn_vcredist.setToolTip('Instalar Visual C++ Redistributable')
        self.btn_dotnet = QPushButton('.NET 8')
        self.btn_dotnet.setObjectName('secondary')
        self.btn_dotnet.setToolTip('Instalar .NET 8.0 Desktop Runtime')
        for b in self.btn_mtk, self.btn_qcom, self.btn_spd, self.btn_vcredist, self.btn_dotnet:
            row_drv.addWidget(b)
        layout.addLayout(row_drv)
        row2 = QHBoxLayout()
        self.btn_verify = QPushButton('Verificar')
        self.btn_verify.setObjectName('secondary')
        self.btn_verify.setToolTip('Atualiza o status de todos os drivers instalados')
        self.btn_test = QPushButton('Detectar Aparelhos Conectados')
        self.btn_test.setObjectName('secondary')
        self.btn_test.setToolTip('L├¬ o que est├í conectado nas portas USB agora (snapshot instant├óneo)')
        self.btn_devmgmt = QPushButton('Gerenciador de Dispositivos')
        self.btn_devmgmt.setObjectName('secondary')
        self.btn_devmgmt.setToolTip('Abre o Gerenciador de Dispositivos do Windows')
        self.btn_close = QPushButton('Fechar')
        self.btn_close.setObjectName('danger')
        row2.addWidget(self.btn_verify)
        row2.addWidget(self.btn_test)
        row2.addWidget(self.btn_devmgmt)
        row2.addStretch()
        row2.addWidget(self.btn_close)
        layout.addLayout(row2)
        self.btn_install_missing.clicked.connect(self._on_install_missing)
        self.btn_reinstall.clicked.connect(self._on_reinstall_all)
        self.btn_mtk.clicked.connect((lambda: self._on_driver('mediatek')))
        self.btn_qcom.clicked.connect((lambda: self._on_driver('qualcomm')))
        self.btn_spd.clicked.connect((lambda: self._on_driver('spd')))
        self.btn_vcredist.clicked.connect((lambda: self._on_driver('vcredist')))
        self.btn_dotnet.clicked.connect((lambda: self._on_driver('dotnet8')))
        self.btn_verify.clicked.connect(self._on_verify)
        self.btn_test.clicked.connect(self._on_test_usbdk)
        self.btn_devmgmt.clicked.connect(self._on_open_devmgmt)
        self.btn_close.clicked.connect(self.accept)
    def _refresh_status(self) -> None:
        st = status_dependencias()
        self.lbl_usbdk.setText(self._format_line('UsbDk', st['usbdk']))
        self.lbl_winfsp.setText(self._format_line('WinFsp', st['winfsp']))
        drv_status = {}
        for key, cfg in _DRIVERS_CFG.items():
            drv_status[key] = is_driver_installed(key)
        self.lbl_mtk.setText(self._format_line('MediaTek USB VCOM', drv_status['mediatek']))
        self.lbl_qcom.setText(self._format_line('Qualcomm QDLoader', drv_status['qualcomm']))
        self.lbl_spd.setText(self._format_line('SPD / Unisoc', drv_status['spd']))
        self.lbl_vcredist.setText(self._format_line('Visual C++ Redist', drv_status['vcredist']))
        self.lbl_dotnet.setText(self._format_line('.NET 8.0 Desktop', drv_status['dotnet8']))
        self.btn_mtk.setEnabled(True)
        self.btn_qcom.setEnabled(True)
        self.btn_spd.setEnabled(True)
        self.btn_vcredist.setEnabled(True)
        self.btn_dotnet.setEnabled(True)
        self.btn_verify.setEnabled(True)
        extras = []
        if not st['winget']:
            extras.append('Gerenciador de pacotes do Windows ausente ÔÇö ser├í usado instalador oficial alternativo.')
        if not st['admin']:
            extras.append('Privil├®gios de administrador s├úo necess├írios para instalar.')
        self.lbl_extra.setText('\n'.join(extras))
        self.lbl_extra.setVisible(bool(extras))
        all_ok = st['usbdk'] and st['winfsp']
        self.btn_install_missing.setEnabled(not all_ok)
        self.btn_test.setEnabled(st['usbdk'])
    @staticmethod
    def _format_line(nome: str, ok: bool) -> str:
        if ok:
            return f"{nome}: <b style='color:#1b5e20'>Instalado e dispon├¡vel</b>"
        return f"{nome}: <b style='color:#b71c1c'>N├úo instalado</b>"
    def _on_verify(self) -> None:
        self._refresh_status()
        self.log.setVisible(True)
        self._log('Status atualizado.')
    def _on_install_missing(self) -> None:
        alvos = []
        if not is_usbdk_installed():
            alvos.append('usbdk')
        if not is_winfsp_installed():
            alvos.append('winfsp')
        if not alvos:
            QMessageBox.information(self, 'Depend├¬ncias', 'Todas as depend├¬ncias j├í est├úo instaladas.')
            return
        self._start_worker(alvos)
    def _on_reinstall_all(self) -> None:
        r = QMessageBox.question(self, 'Confirmar', 'Deseja reinstalar UsbDk e WinFsp?\n\nIsso pode levar alguns minutos.', QMessageBox.Yes | QMessageBox.No)
        if r == QMessageBox.Yes:
            self._start_worker(['usbdk', 'winfsp'])
    def _on_driver(self, key: str) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        if self._drv_worker is not None and self._drv_worker.isRunning():
            return
        self._set_drv_busy(True)
        self.log.setVisible(True)
        self.log.clear()
        self._log(f'Iniciando: {_DRIVERS_CFG[key]['nome']}')
        self._drv_worker = _DriverWorker(key, parent=self)
        self._drv_worker.progresso.connect(self._on_progresso)
        self._drv_worker.concluido.connect(self._on_drv_done)
        self._drv_worker.start()
    def _on_drv_done(self, ok: bool, msg: str) -> None:
        self._log(msg)
        self._set_drv_busy(False)
        self._refresh_status()
        if ok:
            QMessageBox.information(self, 'Conclu├¡do', msg)
            return
        QMessageBox.warning(self, 'Aten├º├úo', msg)
    def _set_drv_busy(self, busy: bool) -> None:
        self.progresso.setVisible(busy)
        if busy:
            self.progresso.setValue(0)
        for b in self.btn_mtk, self.btn_qcom, self.btn_spd, self.btn_vcredist, self.btn_dotnet, self.btn_install_missing, self.btn_reinstall:
            b.setEnabled(not busy)
    def _start_worker(self, alvos: List[str]) -> None:
        if not _is_admin():
            QMessageBox.warning(self, 'Privil├®gios necess├írios', 'A instala├º├úo de drivers requer permiss├Áes de administrador.\n\nFeche o programa e abra novamente clicando com o bot├úo direito no ├¡cone ÔåÆ "Executar como administrador".')
            return
        if self._worker is not None and self._worker.isRunning():
            return
        self.btn_install_missing.setEnabled(False)
        self.btn_reinstall.setEnabled(False)
        self.progresso.setVisible(True)
        self.progresso.setValue(0)
        self.log.setVisible(True)
        self.log.clear()
        self._log('Iniciando: ' + ', '.join((a.upper() for a in alvos)))
        self._worker = _InstallerWorker(alvos, parent=self)
        self._worker.progresso.connect(self._on_progresso)
        self._worker.concluido.connect(self._on_concluido)
        self._worker.start()
    def _on_progresso(self, pct: int, msg: str) -> None:
        self.progresso.setValue(max(0, min(100, int(pct))))
        self._log(msg)
    def _on_concluido(self, ok: bool, msg: str) -> None:
        self.progresso.setValue(100 if ok else self.progresso.value())
        self._log(msg)
        self._refresh_status()
        self.btn_install_missing.setEnabled(True)
        self.btn_reinstall.setEnabled(True)
        if ok:
            QMessageBox.information(self, 'Conclu├¡do', msg)
            return
        QMessageBox.warning(self, 'Aten├º├úo', msg + '\n\nDicas:\nÔÇó Verifique conex├úo com a internet.\nÔÇó Reabra o programa como administrador.\nÔÇó Tente novamente em alguns instantes.')
    def _on_test_usbdk(self) -> None:
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            resumo = analisar_dispositivos_usbdk()
        finally:
            QApplication.restoreOverrideCursor()
        if not resumo.get('ok'):
            QMessageBox.warning(self, 'Verifica├º├úo USB', 'N├úo foi poss├¡vel consultar o servi├ºo USB neste momento.\n\nTente reinstalar a depend├¬ncia UsbDk e repita o teste.')
            return
        flash = list(resumo.get('flash_devices') or [])
        phones = list(resumo.get('smartphone_devices') or [])
        serials = list(resumo.get('serial_devices') or [])
        system_count = int(resumo.get('system_count', 0))
        partes = ['<b>UsbDk est├í funcionando normalmente.</b>']
        if flash:
            partes.append("<br><b style='color:#1b5e20'>ÔÜí Aparelho(s) em modo de flash:</b>")
            for label in flash[:6]:
                partes.append(f"&nbsp;&nbsp;<span style='color:#1b5e20'>Ô£ô</span> {label}")
        if phones:
            partes.append("<br><b style='color:#0D47A1'>­ƒô▒ Smartphone(s) reconhecido(s):</b>")
            for label in phones[:6]:
                partes.append(f"&nbsp;&nbsp;<span style='color:#0D47A1'>Ô£ô</span> {label}")
        if serials:
            partes.append("<br><b style='color:#37474f'>­ƒöî Adaptadores USB-Serial:</b>")
            for label in serials[:4]:
                partes.append(f"&nbsp;&nbsp;<span style='color:#37474f'>Ô£ô</span> {label}")
        if not flash and not phones and not serials:
            partes.append('<br><i>Nenhum smartphone ou adaptador de reparo foi reconhecido agora.</i><br>Conecte o aparelho na porta USB. Se j├í estiver conectado, talvez precise instalar o driver do fabricante (MediaTek / Qualcomm / Samsung) ou abrir o Gerenciador de Dispositivos para verificar.')
        if system_count > 0:
            partes.append(f"<br><span style='color:#90a4ae'>+ {system_count} dispositivo(s) do pr├│prio computador (mouse, teclado, webcam, hubs).</span>")
        QMessageBox.information(self, 'Verifica├º├úo USB', '<br>'.join(partes))
    def _on_open_devmgmt(self) -> None:
        if not abrir_gerenciador_dispositivos():
            QMessageBox.warning(self, 'Gerenciador', 'N├úo foi poss├¡vel abrir o Gerenciador de Dispositivos.')
    def _log(self, texto: str) -> None:
        try:
            self.log.append(texto)
            return
        except Exception:
            return
    def closeEvent(self, event) -> None:
        try:
            if self._worker is not None and self._worker.isRunning():
                self._worker.cancelar()
                self._worker.wait(2000)
            if self._drv_worker is not None and self._drv_worker.isRunning():
                self._drv_worker.cancelar()
                self._drv_worker.wait(2000)
        except Exception:
            pass
        super().closeEvent(event)
def abrir_janela_dependencias_usb(parent=None) -> None:
    try:
        dlg = UsbRequirementsDialog(parent=parent)
        dlg.exec_()
        return
    except Exception:
        try:
            QMessageBox.warning(parent, 'Conex├úo USB', 'N├úo foi poss├¡vel abrir a janela de depend├¬ncias USB.')
            return
        except Exception:
            pass
def abrir_gerenciador_dispositivos_seguro(parent=None) -> None:
    if not abrir_gerenciador_dispositivos():
        try:
            QMessageBox.warning(parent, 'Gerenciador de Dispositivos', 'N├úo foi poss├¡vel abrir o Gerenciador de Dispositivos.')
            return
        except Exception:
            pass
__all__ = ['abrir_gerenciador_dispositivos', 'abrir_gerenciador_dispositivos_seguro', 'abrir_janela_dependencias_usb', 'analisar_dispositivos_usbdk', 'find_usbdk_controller', 'is_usbdk_installed', 'is_winfsp_installed', 'listar_dispositivos_usbdk', 'status_dependencias', 'UsbRequirementsDialog']
