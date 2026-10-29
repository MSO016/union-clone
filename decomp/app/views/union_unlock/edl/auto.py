'''
Detec├º├úo autom├ítica EDL + Opera├º├úo em 2 etapas
================================================
TECH UNION SOLUTIONS ÔÇö Ambiente de Desenvolvimento
Fluxo:
  Etapa 1 ÔÇö Detectar: busca porta 9008, identifica chipset/marca via Sahara,
            localiza loader compat├¡vel no banco de dados (loaders_auto)
  Etapa 2 ÔÇö Operar:  executa erase-part nas parti├º├Áes corretas da marca
Parti├º├Áes FRP por marca (verificado via printgpt em dispositivos reais):
  Samsung  ÔåÆ persistent
  Xiaomi   ÔåÆ frp  (confirmado Redmi Note 8 SM6125)
  Demais   ÔåÆ frp
'''
import logging
import os
import re
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import (Dict, List, Optional)
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QFrame, QMessageBox, QTextEdit, QComboBox, QListWidget, QListWidgetItem)
from PyQt5.QtCore import (QThread, pyqtSignal, Qt, QVariantAnimation)
from PyQt5.QtGui import (QFont, QPixmap, QTransform, QColor)
try:
    from app.views.union_unlock.edl.edl_auth_config import AuthSelectorWidget
    _AUTH_SELECTOR_OK = True
except ImportError:
    try:
        from edl_auth_config import AuthSelectorWidget
        _AUTH_SELECTOR_OK = True
    except ImportError:
        _AUTH_SELECTOR_OK = False
try:
    from serial.tools import list_ports
    _SERIAL_OK = True
except ImportError:
    _SERIAL_OK = False
try:
    from app.views.union_unlock.edl.edl_sync import get_sync
    _SYNC_OK = True
except ImportError:
    try:
        from edl_sync import get_sync
        _SYNC_OK = True
    except ImportError:
        _SYNC_OK = False
try:
    from app.views.union_unlock.edl.frp_xiaomi_auth import executar_frp_auth
    _FRP_AUTH_OK = True
except ImportError:
    try:
        from frp_xiaomi_auth import executar_frp_auth
        _FRP_AUTH_OK = True
    except ImportError:
        _FRP_AUTH_OK = False
try:
    from app.views.union_unlock.edl.frp_samsung import executar_frp_samsung
    _FRP_SAMSUNG_OK = True
except ImportError:
    try:
        from frp_samsung import executar_frp_samsung
        _FRP_SAMSUNG_OK = True
    except ImportError:
        _FRP_SAMSUNG_OK = False
_logger = logging.getLogger('edl_auto')
def _log(msg: str):
    _logger.debug(msg)
try:
    from app.views.union_unlock.edl.config import (TOOLS_DIR as _TOOLS_DIR, EDL_NG as _EDL_NG, IMG_DIR as _IMG_DIR)
except ImportError:
    from config import (TOOLS_DIR as _TOOLS_DIR, EDL_NG as _EDL_NG, IMG_DIR as _IMG_DIR)
def _get_auto_tmp_dir() -> Path:
    if sys.platform == 'win32':
        base = os.environ.get('LOCALAPPDATA', tempfile.gettempdir())
    else:
        base = tempfile.gettempdir()
    parent = Path(base) / '.union_edl'
    parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == 'win32':
        try:
            import ctypes
            p_str = str(parent)
            attrs = ctypes.windll.kernel32.GetFileAttributesW(p_str)
            if attrs == -1 or not attrs & 2:
                ctypes.windll.kernel32.SetFileAttributesW(p_str, 8198)
        except Exception:
            pass
    d = parent / 'auto_loaders'
    d.mkdir(exist_ok=True)
    return d
_TEMP_DIR = _get_auto_tmp_dir()
def _limpar_temp_loaders():
    '''Remove loaders temporarios do disco para seguranca.'''
    try:
        if _TEMP_DIR.exists():
            for f in _TEMP_DIR.iterdir():
                pass
        try:
            f.unlink()
        except Exception:
            pass
    except Exception:
        return
def _matar_processos_edl():
    '''Mata processos EDL orfaos de forma segura (Windows).'''
    if sys.platform != 'win32':
        return
    for exe_name in ('edl-ng.exe', 'FRP_EDL.exe', 'emmcdl.exe', 'fh_loader.exe', 'QSaharaServer.exe'):
        try:
            result = subprocess.run(['taskkill', '/F', '/IM', exe_name], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=5)
            if result.returncode == 0:
                _log(f'Processo {exe_name} encerrado')
        except Exception:
            continue
PARTICOES_FRP: Dict[str, List[str]] = {'samsung': ['persistent'], 'xiaomi': ['frp', 'userdata'], 'oppo': ['frp'], 'realme': ['frp'], 'oneplus': ['frp'], 'vivo': ['frp'], 'lenovo_motorola': ['frp'], 'nokia_foxconn': ['frp'], 'zte': ['frp'], 'asus_wingtech': ['frp'], 'huawei': ['frp'], 'honor': ['frp'], 'lg': ['frp'], 'tcl': ['frp'], 'hmd': ['frp']}
_PARTICOES_DEFAULT = ['frp']
PARTICOES_PROIBIDAS = {'efs', 'fsg', 'sec_efs', 'modemst1', 'modemst2'}
_OEM_FOLDER = {'0000': 'qualcomm', '0001': 'sony', '0004': 'zte', '0015': 'huawei', '0017': 'lenovo_motorola', '0020': 'samsung', '0029': 'asus_wingtech', '0031': 'lg', '0035': 'nokia_foxconn', '0042': 'tcl', '0045': 'hmd', '0159': 'honor', '01a4': 'honor', '0051': 'oppo', '0072': 'xiaomi', '0073': 'vivo', '0142': 'oppo', '0168': 'lenovo_motorola', '01b0': 'lenovo_motorola', '0208': 'lenovo_motorola'}
_OEM_NOME = {'0000': 'Qualcomm', '0001': 'Sony', '0004': 'ZTE', '0015': 'Huawei', '0017': 'Motorola/Lenovo', '0020': 'Samsung', '0029': 'Asus', '0031': 'LG', '0035': 'Nokia', '0042': 'TCL', '0045': 'Nokia/HMD', '0159': 'Honor', '01a4': 'Honor', '0051': 'Oppo/OnePlus', '0072': 'Xiaomi', '0073': 'Vivo', '0142': 'Oppo', '0168': 'Motorola', '01b0': 'Motorola', '0208': 'Motorola'}
_HWID_CHIPSET = {'1b80e1': 'Snapdragon 680', '1920e1': 'Snapdragon 778G', '1a90e1': 'Snapdragon 695', '1db0e1': 'Snapdragon 6 Gen 1', '1ca0e1': 'Snapdragon 8 Gen 2', '1350e1': 'Snapdragon 888', '1630e1': 'Snapdragon 750G', '1490e1': 'Snapdragon 720G', '1360e1': 'Snapdragon 662', '10a0e1': 'Snapdragon 665', '11e0e1': 'Snapdragon 765G', '0e60e1': 'Snapdragon 730', '0c30e1': 'Snapdragon 865', '0a50e1': 'Snapdragon 855', '0ba0e1': 'Snapdragon 439/632', '0bf0e1': 'Snapdragon 439', '0db0e1': 'Snapdragon 665', '08b0e1': 'Snapdragon 845', '08c0e1': 'Snapdragon 660', '09a0e1': 'Snapdragon 450', '0950e1': 'Snapdragon 710', '05e0e1': 'Snapdragon 835', '0460e1': 'Snapdragon 625', '04f0e1': 'Snapdragon 430', '0560e1': 'Snapdragon 425'}
def _obter_loader_dummy() -> Optional[Path]:
    '''
    Retorna um arquivo qualquer para o edl-ng usar na fase de detec├º├úo Sahara.
    O Sahara retorna Serial/OEM/HWID/RKH ANTES de carregar o loader,
    ent├úo qualquer arquivo (at├® o pr├│prio edl-ng.exe) funciona.
    '''
    if _EDL_NG.exists():
        return _EDL_NG
    for ext in ('*.exe', '*.bin', '*.elf'):
        for f in _TOOLS_DIR.glob(ext):
            return f
def _limpar_temp():
    '''Remove arquivos tempor├írios.'''
    if _TEMP_DIR.exists():
        try:
            shutil.rmtree(_TEMP_DIR)
            return
        except Exception:
            pass
def _buscar_loader_db(hwid: str, pkhash: str) -> Optional[Path]:
    '''
    Busca loader compativel no cache DB (loaders_auto).
    Retorna o primeiro match (retrocompativel).
    '''
    resultados = _buscar_loaders_db(hwid, pkhash)
    if resultados:
        return resultados[0]['path']
def _buscar_loaders_db(hwid: str, pkhash: str) -> list:
    '''
    Busca TODOS os loaders compativeis no cache DB (loaders_auto).
    Retorna lista de dicts com: srv, id, path, memoria, requer_auth, chipset, tamanho.
    Cada item ja tem o loader baixado e pronto para uso.
    '''
    if not _SYNC_OK:
        return []
    sync = get_sync()
    matches = sync.buscar_loaders_auto(hwid, pkhash)
    if not matches:
        return []
    _log(f'Loaders auto compativeis: {len(matches)} encontrado(s)')
    _TEMP_DIR.mkdir(parents=True, exist_ok=True)
    resultados = []
    for match in matches:
        loader_id = match['id']
        srv = match.get('srv', f'SRV{len(resultados)}')
        dados = sync.download_loader_auto(loader_id)
        if not dados:
            _log(f'{srv}: falha ao baixar loader {loader_id}')
            continue
        destino = _TEMP_DIR / f'.ul_{loader_id}.tmp'
        try:
            destino.write_bytes(dados)
        except Exception as e:
            _log(f'{srv}: erro ao gravar loader {loader_id} ÔÇö {e}')
            continue
        resultados.append({'srv': srv, 'id': loader_id, 'path': destino, 'memoria': match.get('memoria', 'emmc'), 'requer_auth': match.get('requer_auth'), 'chipset': match.get('chipset', ''), 'tamanho': match.get('tamanho', 0)})
        _log(f'{srv}: loader {loader_id} pronto ({len(dados)} bytes)')
    return resultados
def _detectar_porta_9008() -> Optional[str]:
    '''Detecta porta COM Qualcomm 9008.'''
    if _SERIAL_OK:
        try:
            portas = list(list_ports.comports())
            for port in portas:
                hwid = (port.hwid or '').lower()
                desc = (port.description or '').lower()
                if '05c6:9008' in hwid or 'vid_05c6&pid_9008' in hwid:
                    return port.device
                if '9008' in hwid and '05c6' in hwid:
                    return port.device
                if '9008' not in desc:
                    continue
                if 'qdloader' in desc or 'qualcomm' in desc:
                    return port.device
        except Exception as e:
            pass
    try:
        result = subprocess.run(['powershell', '-Command', "Get-WmiObject Win32_PnPEntity | Where-Object { $_.Name -like '*COM*' } | Select-Object -ExpandProperty Name"], capture_output=True, text=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if re.search('Qualcomm|9008|QDLoader', line, re.IGNORECASE):
                    m = re.search('\\(COM(\\d+)\\)', line)
                    if m:
                        return f'COM{m.group(1)}'
    except Exception:
        return
def _obter_info_dispositivo(loader: Path) -> Optional[Dict]:
    '''
    Executa edl-ng upload-loader para obter HWID, OEM, chipset.
    O Sahara retorna Serial/OEM/HWID/RKH ANTES de carregar o loader,
    ent├úo mesmo que o loader seja incompat├¡vel as infos s├úo extra├¡das.
    O exit code pode ser != 0 (loader rejeitado) ÔÇö isso ├® esperado.
    '''
    if not _EDL_NG.exists():
        _log(f'edl-ng nao encontrado: {_EDL_NG}')
        return
    cmd = [str(_EDL_NG), 'upload-loader', '-l', str(loader), '--loglevel', 'Debug']
    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=str(_TOOLS_DIR), creationflags=flags)
        output = result.stdout + result.stderr
        serial = oem_id = model_id = rkh = product_name = None
        product_id_val = mfr_id_val = None
        for line in output.split('\n'):
            m = re.search('Serial Number:\\s*([0-9A-Fa-f]+)', line)
            if m:
                serial = m.group(1)
            m = re.search('Product ID:\\s*(\\d+)\\s*\\(([^)]+)\\)', line)
            if m:
                product_id_val = int(m.group(1))
                product_name = m.group(2)
            m = re.search('Manufacturer ID:\\s*([0-9A-Fa-f]+)', line)
            if m:
                mfr_id_val = int(m.group(1), 16)
            m = re.search('OEM:\\s*([0-9A-Fa-f]+)', line)
            if m:
                oem_id = m.group(1).lower()
            m = re.search('Model:\\s*([0-9A-Fa-f]+)', line)
            if m:
                model_id = m.group(1).lower()
            m = re.search('RKH\\[0\\]:\\s*([0-9A-Fa-f]+)', line)
            if not m:
                continue
            rkh = m.group(1).lower()
            continue
        if not serial:
            return
        if product_id_val is not None and mfr_id_val is not None:
            msm_full = f'{product_id_val << 12 | mfr_id_val:06x}'
        else:
            msm_full = '000000'
        hwid = f'00{msm_full}{oem_id or '0000'}{model_id or '0000'}'
        pkhash = rkh[:16] if rkh else ''
        vendor_folder = _OEM_FOLDER.get(oem_id or '0000', 'unknown')
        vendor_name = _OEM_NOME.get(oem_id or '0000', 'Desconhecido')
        chipset = 'Desconhecido'
        if product_name and product_name != 'Unknown':
            chipset = product_name
        if chipset == 'Desconhecido' and len(msm_full) >= 6:
            chipset = _HWID_CHIPSET.get(msm_full[:6].lower(), chipset)
        return {'serial': serial or 'N/A', 'chipset': chipset, 'vendor': vendor_name, 'vendor_folder': vendor_folder, 'oem_id': oem_id or '0000', 'model_id': model_id or '0000', 'hwid': hwid, 'pkhash': pkhash}
    except subprocess.TimeoutExpired:
        _log('Timeout na detecao')
    except Exception as e:
        _log(f'Erro na detecao: {e}')
def _particoes_para_marca(vendor_folder: str) -> List[str]:
    '''Retorna lista de parti├º├Áes FRP da marca.'''
    return PARTICOES_FRP.get(vendor_folder.lower(), _PARTICOES_DEFAULT)
class DetectarWorker(QThread):
    '''Etapa 1: detecta porta 9008, identifica chipset, busca loader no banco.'''
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, dict)
    def __init__(self):
        super().__init__()
        self._cancelado = False
    def cancelar(self):
        self._cancelado = True
    def _emit(self, msg):
        _log(msg)
        self.log_signal.emit(msg)
    def run(self):
        try:
            self.status_signal.emit('waiting')
            self.progress_signal.emit(10)
            self._emit('Procurando dispositivo Qualcomm 9008...')
            porta = _detectar_porta_9008()
            if not porta:
                self._emit('Nenhum dispositivo 9008 detectado')
                self._emit('Conecte o aparelho em modo EDL')
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Dispositivo nao encontrado', {})
                return
            self._emit(f'Porta EDL: {porta}')
            self.progress_signal.emit(25)
            if self._cancelado:
                self.finished_signal.emit(False, 'Cancelado', {})
                return
            self._emit('Preparando comunicacao...')
            dummy = _obter_loader_dummy()
            if not dummy:
                self._emit('Componente nao encontrado')
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Componente nao encontrado.\nVerifique a instalacao do programa.', {})
                return
            self.progress_signal.emit(40)
            self._emit('Identificando dispositivo...')
            self.status_signal.emit('connected')
            if self._cancelado:
                self.finished_signal.emit(False, 'Cancelado', {})
                return
            info = _obter_info_dispositivo(dummy)
            if not info:
                self._emit('Dispositivo nao respondeu')
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Dispositivo nao respondeu', {})
                return
            self.progress_signal.emit(60)
            self._emit('------------------------------------------')
            self._emit('DISPOSITIVO IDENTIFICADO')
            self._emit('------------------------------------------')
            self._emit(f'Serial       : {info['serial'].upper()}')
            self._emit(f'Fabricante   : {info['vendor']}')
            self._emit(f'Chipset      : {info['chipset']}')
            self._emit(f'HWID         : {info['hwid']}')
            self._emit('------------------------------------------')
            self._emit('Verificando compatibilidade...')
            self.progress_signal.emit(70)
            loader_matches = _buscar_loaders_db(info['hwid'], info['pkhash'])
            if loader_matches:
                info['loader_path'] = str(loader_matches[0]['path'])
                info['loader_found'] = True
                info['loader_matches'] = loader_matches
                particoes = _particoes_para_marca(info['vendor_folder'])
                info['particoes_frp'] = particoes
                mem = loader_matches[0].get('memoria', 'emmc')
                info['memoria_auto'] = mem
                mem_info = f' | Memoria: {mem.upper()}'
                self._emit(f'Modelo compativel encontrado!{mem_info}')
                self._emit('')
                self._emit('MODELO SUPORTADO')
                self._emit('')
                self._emit('Coloque o aparelho em modo EDL novamente')
                self._emit('e clique em Remover FRP para prosseguir.')
                self.progress_signal.emit(100)
                self.status_signal.emit('success')
                self.finished_signal.emit(True, 'Modelo suportado!', info)
                return
            info['loader_found'] = False
            self.progress_signal.emit(90)
            sugestao = ''
            if _SYNC_OK:
                modelos_marca = get_sync().buscar_modelos_por_marca(info['vendor'])
                if modelos_marca:
                    sugestao = f'\n\nTemos {len(modelos_marca)} modelo(s) {info['vendor']} cadastrados.\nSelecione na aba "Marca/Modelo".'
                    self._emit('Modelo nao suportado ÔÇö use o modo Manual')
                    self._emit(f'Temos {len(modelos_marca)} modelo(s) {info['vendor']} disponiveis')
                    self._emit('Selecione na aba "Marca/Modelo"')
                else:
                    self._emit('Modelo nao suportado nesta versao')
            self.progress_signal.emit(100)
            self.status_signal.emit('error')
            msg = f'Modelo nao suportado ÔÇö use o modo Manual{sugestao}'
            self.finished_signal.emit(False, msg, info)
            return
        except Exception as e:
            _log(f'Erro na detecao: {e}')
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado.\n\nReconecte o dispositivo e tente novamente.', {})
class OperarWorker(QThread):
    '''Etapa 2: executa erase-part nas parti├º├Áes da marca + reset.'''
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, loader_path: str, particoes: List[str], memoria: str='emmc'):
        super().__init__()
        self._loader = loader_path
        self._particoes = particoes
        self._mem = 'Sdcc' if memoria == 'emmc' else 'Ufs'
        self._cancelado = False
    def cancelar(self):
        self._cancelado = True
    def _emit(self, msg):
        _log(msg)
        self.log_signal.emit(msg)
    def _exec_edl(self, args: List[str]) -> tuple:
        '''Executa edl-ng com argumentos e retorna (ok, erro).'''
        cmd = [str(_EDL_NG)] + args + ['-l', self._loader, '--memory', self._mem]
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=str(_TOOLS_DIR), creationflags=flags)
        ok = False
        no_dev = False
        erro_op = False
        for line in iter(proc.stdout.readline, ''):
            if self._cancelado:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=3)
                return (False, 'Cancelado')
            linha = line.rstrip()
            self._emit(linha)
            ll = linha.lower()
            if 'successfully erased' in ll:
                ok = True
            if 'power command' in ll and 'sent successfully' in ll:
                ok = True
            if 'no qualcomm edl devices found' in ll:
                no_dev = True
            if any((p in ll for p in ('partition not found', 'failed to erase', 'not supported', 'sahara protocol error', 'signature verification failed', 'authentication failed', 'failed to send'))):
                erro_op = True
        proc.wait()
        if no_dev:
            return (False, 'Dispositivo nao encontrado!\nReconecte o aparelho em modo EDL e tente novamente.')
        return ok or proc.returncode == 0, ''
    def run(self):
        try:
            if not os.path.exists(self._loader):
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Arquivo de suporte nao encontrado.\nVerifique a instalacao do programa.')
                return
            if not _EDL_NG.exists():
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Componente nao encontrado!\n\nReinstale o programa ou entre em contato com o suporte.')
                return
            self.status_signal.emit('processing')
            self.progress_signal.emit(10)
            total = len(self._particoes)
            self._emit('==========================================')
            self._emit(f'  REMOVENDO FRP ÔÇö {total} PARTICOES')
            self._emit('==========================================')
            for i, part in enumerate(self._particoes, 1):
                if self._cancelado:
                    self.finished_signal.emit(False, 'Cancelado')
                    return
                if part.lower() in PARTICOES_PROIBIDAS:
                    self._emit(f'BLOQUEADO: particao {part} e protegida!')
                    continue
                self._emit(f'  [{i}/{total}] Apagando: {part}')
                pct = 10 + int(70 * i / (total + 1))
                self.progress_signal.emit(pct)
                ok, erro = self._exec_edl(['erase-part', part])
                if ok:
                    continue
                self.status_signal.emit('error')
                self.finished_signal.emit(False, erro or f'Falha ao apagar {part}')
                return
            self._emit('')
            self._emit('Reiniciando dispositivo...')
            self.progress_signal.emit(90)
            self._exec_edl(['reset'])
            self.progress_signal.emit(100)
            self._emit('')
            self._emit('==========================================')
            self._emit('  FRP REMOVIDO COM SUCESSO!')
            self._emit('==========================================')
            self._emit('')
            self._emit('  1. O aparelho vai reiniciar')
            self._emit('  2. Configure normalmente')
            self._emit('')
            self.status_signal.emit('success')
            self.finished_signal.emit(True, 'FRP removido com sucesso!')
            return
        except OSError as e:
            self.status_signal.emit('error')
            if hasattr(e, 'winerror') and e.winerror == 740:
                self.finished_signal.emit(False, 'Execute como Administrador!\n\nClique com botao direito no programa\ne selecione "Executar como administrador".')
        except Exception as e:
            _log(f'Erro inesperado na operacao: {e}')
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado.\n\nReconecte o dispositivo e tente novamente.')
class FrpAuthWorker(QThread):
    '''Executa FRP via QSaharaServer + fh_loader com autenticacao.'''
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, dict)
    def __init__(self, loader_path: str, memoria: str, particoes: List[str], auth_manufacturer: str='xiaomi'):
        super().__init__()
        self._loader = loader_path
        self._mem = memoria
        self._particoes = particoes
        self._auth = auth_manufacturer
        self._cancelado = False
    def cancelar(self):
        self._cancelado = True
        _matar_processos_edl()
    def run(self):
        try:
            self.status_signal.emit('processing')
            ok, msg, data = executar_frp_auth(loader_path=self._loader, memoria=self._mem, particoes_alvo=self._particoes, log_cb=self._emit_log, progress_cb=self.progress_signal.emit, auth_manufacturer=self._auth)
            if self._cancelado:
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Cancelado pelo usuario.', {})
                return
            self.status_signal.emit('success' if ok else 'error')
            self.finished_signal.emit(ok, msg, data)
            return
        except Exception as e:
            _log(f'Erro FrpAuthWorker: {e}')
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado.\n\nReconecte o dispositivo e tente novamente.', {})
    def _emit_log(self, msg: str):
        _log(msg)
        self.log_signal.emit(msg)
class FrpSamsungWorker(QThread):
    '''Executa FRP Samsung via QSaharaServer + fh_loader (program/patch).'''
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, dict)
    def __init__(self, loader_path: str, memoria: str, particoes: Optional[List[str]]=None):
        super().__init__()
        self._loader = loader_path
        self._mem = memoria
        self._particoes = particoes or ['persistent']
        self._cancelado = False
    def cancelar(self):
        self._cancelado = True
        _matar_processos_edl()
    def run(self):
        try:
            self.status_signal.emit('processing')
            ok, msg, data = executar_frp_samsung(loader_path=self._loader, memoria=self._mem, particoes_alvo=self._particoes, log_cb=self._emit_log, progress_cb=self.progress_signal.emit)
            if self._cancelado:
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Cancelado pelo usuario.', {})
                return
            self.status_signal.emit('success' if ok else 'error')
            self.finished_signal.emit(ok, msg, data)
            return
        except Exception as e:
            _log(f'Erro FrpSamsungWorker: {e}')
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado.\n\nReconecte o dispositivo e tente novamente.', {})
    def _emit_log(self, msg: str):
        _log(msg)
        self.log_signal.emit(msg)
class _Cores:
    BG = '#f5f5f5'
    BG_DARK = '#e8e8e8'
    BG_WHITE = '#ffffff'
    PRIMARY = '#2471a3'
    PRI_HOV = '#1a5276'
    SUCCESS = '#27ae60'
    ERROR = '#e74c3c'
    WARNING = '#f39c12'
    TEXT = '#2c3e50'
    MUTED = '#7f8c8d'
    WHITE = '#ffffff'
    BORDER = '#bdc3c7'
class EdlAutoWidget(QWidget):
    '''
Aba de detec├º├úo autom├ítica ÔÇö fluxo de 2 etapas:
  [Detectar] ÔåÆ identifica marca/chipset/loader ÔåÆ "Modelo Suportado"
                                                      Ôåô
  [Remover FRP] ÔåÆ apaga parti├º├Áes corretas da marca ÔåÆ "Sucesso"
Se o checkbox "Forcar autenticacao" estiver marcado, redireciona
para a aba Particoes em vez de usar edl-ng (que nao suporta auth).
'''
    redirecionar_particoes = pyqtSignal(dict)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._detect_worker = None
        self._oper_worker = None
        self._frp_auth_worker = None
        self._frp_samsung_worker = None
        self._device_info = {}
        self._loader_path = None
        self._em_exec = False
        self._setup_ui()
        self._init_animation()
    def _img(self, nome: str) -> str:
        return os.path.join(_IMG_DIR, nome)
    def _setup_ui(self):
        self.setStyleSheet(f'background-color: {_Cores.BG};')
        main = QHBoxLayout(self)
        main.setContentsMargins(20, 20, 20, 20)
        main.setSpacing(20)
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(8)
        titulo = QLabel('Deteccao Automatica EDL')
        titulo.setFont(QFont('Segoe UI', 18, QFont.Bold))
        titulo.setStyleSheet(f'color: {_Cores.PRIMARY};')
        titulo.setWordWrap(True)
        ll.addWidget(titulo)
        subtitulo = QLabel('Qualcomm Emergency Download Mode (9008)')
        subtitulo.setFont(QFont('Segoe UI', 10))
        subtitulo.setStyleSheet(f'color: {_Cores.MUTED};')
        subtitulo.setWordWrap(True)
        ll.addWidget(subtitulo)
        ll.addSpacing(10)
        self._info_frame = QFrame()
        self._info_frame.setMinimumWidth(200)
        self._info_frame.setStyleSheet(f'QFrame {{ background-color: {_Cores.BG_WHITE}; border: 1px solid {_Cores.BORDER}; border-radius: 8px; }}')
        self._info_frame.setVisible(False)
        info_layout = QVBoxLayout(self._info_frame)
        info_layout.setContentsMargins(14, 10, 14, 10)
        info_layout.setSpacing(4)
        self._lbl_fabricante = QLabel()
        self._lbl_fabricante.setFont(QFont('Segoe UI', 13, QFont.Bold))
        self._lbl_fabricante.setStyleSheet(f'color: {_Cores.TEXT}; border: none;')
        self._lbl_fabricante.setWordWrap(True)
        info_layout.addWidget(self._lbl_fabricante)
        self._lbl_chipset = QLabel()
        self._lbl_chipset.setFont(QFont('Segoe UI', 11))
        self._lbl_chipset.setStyleSheet(f'color: {_Cores.MUTED}; border: none;')
        self._lbl_chipset.setWordWrap(True)
        info_layout.addWidget(self._lbl_chipset)
        self._lbl_serial = QLabel()
        self._lbl_serial.setFont(QFont('Segoe UI', 10))
        self._lbl_serial.setStyleSheet(f'color: {_Cores.MUTED}; border: none;')
        self._lbl_serial.setWordWrap(True)
        info_layout.addWidget(self._lbl_serial)
        self._lbl_instrucao = QLabel()
        self._lbl_instrucao.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self._lbl_instrucao.setStyleSheet(f'color: {_Cores.SUCCESS}; border: none;')
        self._lbl_instrucao.setWordWrap(True)
        info_layout.addWidget(self._lbl_instrucao)
        ll.addWidget(self._info_frame)
        ll.addSpacing(4)
        if _AUTH_SELECTOR_OK:
            self._auth_selector = AuthSelectorWidget()
            ll.addWidget(self._auth_selector)
        else:
            self._auth_selector = None
        ll.addSpacing(4)
        self.btn_detectar = QPushButton('Detectar')
        self.btn_detectar.setMinimumWidth(200)
        self.btn_detectar.setMaximumWidth(300)
        self.btn_detectar.setFixedHeight(44)
        self.btn_detectar.setFont(QFont('Segoe UI', 13, QFont.Bold))
        self.btn_detectar.setCursor(Qt.PointingHandCursor)
        self.btn_detectar.setStyleSheet(f'\n            QPushButton {{\n                background-color: {_Cores.PRIMARY}; color: {_Cores.WHITE};\n                border: none; border-radius: 6px;\n            }}\n            QPushButton:hover {{ background-color: {_Cores.PRI_HOV}; }}\n            QPushButton:disabled {{ background-color: {_Cores.BORDER}; }}\n        ')
        self.btn_detectar.clicked.connect(self._detectar)
        ll.addWidget(self.btn_detectar)
        self.btn_remover = QPushButton('Remover FRP')
        self.btn_remover.setMinimumWidth(200)
        self.btn_remover.setMaximumWidth(300)
        self.btn_remover.setFixedHeight(44)
        self.btn_remover.setFont(QFont('Segoe UI', 13, QFont.Bold))
        self.btn_remover.setCursor(Qt.PointingHandCursor)
        self.btn_remover.setStyleSheet(f'\n            QPushButton {{\n                background-color: {_Cores.SUCCESS}; color: {_Cores.WHITE};\n                border: none; border-radius: 6px;\n            }}\n            QPushButton:hover {{ background-color: #229954; }}\n            QPushButton:disabled {{ background-color: {_Cores.BORDER}; }}\n        ')
        self.btn_remover.setEnabled(False)
        self.btn_remover.clicked.connect(self._remover_frp)
        ll.addWidget(self.btn_remover)
        self._srv_frame = QFrame()
        self._srv_frame.setVisible(False)
        srv_lay = QVBoxLayout(self._srv_frame)
        srv_lay.setContentsMargins(0, 2, 0, 2)
        srv_lay.setSpacing(2)
        srv_lbl = QLabel('Servidor de origem:')
        srv_lbl.setFont(QFont('Segoe UI', 9))
        srv_lbl.setStyleSheet(f'color:{_Cores.MUTED};')
        srv_lay.addWidget(srv_lbl)
        self._srv_list = QListWidget()
        self._srv_list.setMinimumWidth(200)
        self._srv_list.setMaximumWidth(300)
        self._srv_list.setMaximumHeight(90)
        self._srv_list.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self._srv_list.setStyleSheet(f'\n            QListWidget{{background-color:{_Cores.BG_WHITE};border:1px solid {_Cores.BORDER};\n                border-radius:6px;color:{_Cores.PRIMARY};}}\n            QListWidget::item{{padding:4px 8px;}}\n            QListWidget::item:selected{{background-color:{_Cores.PRIMARY};color:{_Cores.WHITE};}}\n        ')
        self._srv_list.currentRowChanged.connect(self._on_srv_changed)
        srv_lay.addWidget(self._srv_list)
        ll.addWidget(self._srv_frame)
        self.btn_parar = QPushButton('Parar')
        self.btn_parar.setMinimumWidth(200)
        self.btn_parar.setMaximumWidth(300)
        self.btn_parar.setFixedHeight(36)
        self.btn_parar.setFont(QFont('Segoe UI', 10))
        self.btn_parar.setCursor(Qt.PointingHandCursor)
        self.btn_parar.setStyleSheet(f'\n            QPushButton {{\n                background-color: {_Cores.BG_DARK}; color: {_Cores.TEXT};\n                border: 1px solid {_Cores.BORDER}; border-radius: 6px;\n            }}\n            QPushButton:hover {{ background-color: {_Cores.BORDER}; }}\n            QPushButton:disabled {{ background-color: {_Cores.BG}; border-color: {_Cores.BG}; }}\n        ')
        self.btn_parar.setEnabled(False)
        self.btn_parar.clicked.connect(self._parar)
        ll.addWidget(self.btn_parar)
        ll.addSpacing(4)
        self.barra = QProgressBar()
        self.barra.setMinimumWidth(200)
        self.barra.setMaximumWidth(300)
        self.barra.setFixedHeight(18)
        self.barra.setValue(0)
        self.barra.setTextVisible(False)
        self.barra.setStyleSheet(f'\n            QProgressBar {{ border: 1px solid {_Cores.BORDER}; border-radius: 9px;\n                background-color: {_Cores.BG_WHITE}; }}\n            QProgressBar::chunk {{ background-color: {_Cores.PRIMARY}; border-radius: 8px; }}\n        ')
        ll.addWidget(self.barra)
        ll.addStretch()
        aviso = QLabel('COMO ENTRAR EM MODO EDL:\n\nOPCAO 1 - Test Point (mais confiavel):\n  Abra o aparelho e faca curto no ponto EDL\n\nOPCAO 2 - Botoes:\n  Desligue, segure Vol+ e Vol-, conecte USB')
        aviso.setFont(QFont('Segoe UI', 9))
        aviso.setStyleSheet(f'color: {_Cores.PRIMARY}; padding: 10px; background-color: {_Cores.BG_WHITE}; border-radius: 6px; border-left: 3px solid {_Cores.PRIMARY};')
        aviso.setWordWrap(True)
        ll.addWidget(aviso)
        ll.addSpacing(4)
        self.lbl_status = QLabel('Pronto')
        self.lbl_status.setFont(QFont('Segoe UI', 12))
        self.lbl_status.setStyleSheet(f'color: {_Cores.MUTED};')
        self.lbl_status.setWordWrap(True)
        ll.addWidget(self.lbl_status)
        main.addWidget(left, stretch=1)
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setAlignment(Qt.AlignCenter)
        self.phone_container = QFrame()
        self.phone_container.setFixedSize(250, 250)
        self.phone_container.setStyleSheet(f'background-color: {_Cores.BG_DARK}; border-radius: 125px; border: 2px solid {_Cores.BORDER};')
        fl = QVBoxLayout(self.phone_container)
        fl.setAlignment(Qt.AlignCenter)
        self.phone_image = QLabel()
        self.phone_image.setFixedSize(140, 140)
        self.phone_image.setAlignment(Qt.AlignCenter)
        fl.addWidget(self.phone_image)
        rl.addWidget(self.phone_container)
        self.lbl_phone = QLabel('')
        self.lbl_phone.setAlignment(Qt.AlignCenter)
        self.lbl_phone.setFont(QFont('Segoe UI', 11))
        self.lbl_phone.setStyleSheet(f'color: {_Cores.MUTED}; margin-top: 15px;')
        rl.addWidget(self.lbl_phone)
        main.addWidget(right, stretch=1)
        self._set_phone('notfound')
    def _init_animation(self):
        self._anim = QVariantAnimation()
        self._anim.setDuration(3000)
        self._anim.setStartValue(0)
        self._anim.setEndValue(360)
        self._anim.setLoopCount(-1)
        self._anim.valueChanged.connect(self._rotate_phone)
        self._original_pix = None
    def _set_phone(self, status):
        imgs = {'notfound': 'phone_notfound.png', 'loading': 'phone_loading.png', 'connected': 'phone_connected.png', 'success': 'phone_success.png', 'error': 'phone_error.png'}
        estilos = {'notfound': f'background-color:{_Cores.BG_DARK};border-radius:125px;border:2px solid {_Cores.BORDER};', 'loading': f'background-color:{_Cores.BG_DARK};border-radius:125px;border:2px solid {_Cores.PRIMARY};', 'connected': f'background-color:{_Cores.BG_DARK};border-radius:125px;border:2px solid {_Cores.PRIMARY};', 'success': f'background-color:{_Cores.SUCCESS};border-radius:125px;border:2px solid {_Cores.SUCCESS};', 'error': f'background-color:{_Cores.ERROR};border-radius:125px;border:2px solid {_Cores.ERROR};'}
        self.phone_container.setStyleSheet(estilos.get(status, estilos['notfound']))
        path = self._img(imgs.get(status, 'phone_notfound.png'))
        if os.path.exists(path):
            pix = QPixmap(path).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.phone_image.setPixmap(pix)
            if status == 'loading':
                self._original_pix = pix
                return
            return
        self.phone_image.setText('­ƒô▒')
        self.phone_image.setStyleSheet(f'font-size: 50px; color: {_Cores.TEXT};')
    def _rotate_phone(self, angle):
        if self._original_pix:
            rot = self._original_pix.transformed(QTransform().rotate(angle), Qt.SmoothTransformation)
            dx = (rot.width() - self._original_pix.width()) // 2
            dy = (rot.height() - self._original_pix.height()) // 2
            self.phone_image.setPixmap(rot.copy(dx, dy, self._original_pix.width(), self._original_pix.height()))
    def _detectar(self):
        if self._em_exec:
            return
        try:
            from app.views.union_unlock.edl.firehose_ops import detectar_boxes_ativas
        except ImportError:
            from firehose_ops import detectar_boxes_ativas
        boxes = detectar_boxes_ativas()
        if boxes:
            lista = ', '.join(boxes)
            resp = QMessageBox.warning(self, 'Conflito de Porta', f'Programas que podem bloquear a porta EDL:\n\n  {lista}\n\nFeche-os para garantir o acesso ao dispositivo.\nDeseja tentar mesmo assim?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if resp == QMessageBox.No:
                return
        self._em_exec = True
        self._device_info = {}
        self._loader_path = None
        self._info_frame.setVisible(False)
        self._srv_frame.setVisible(False)
        self._srv_list.clear()
        self.btn_detectar.setEnabled(False)
        self.btn_remover.setEnabled(False)
        self.btn_parar.setEnabled(True)
        self.barra.setValue(5)
        self.lbl_status.setText('Procurando dispositivo...')
        self.lbl_status.setStyleSheet(f'color: {_Cores.MUTED};')
        self.lbl_phone.setText('Conecte o celular em modo EDL')
        self._set_phone('loading')
        self._anim.start()
        self._detect_worker = DetectarWorker()
        self._detect_worker.progress_signal.connect(self.barra.setValue)
        self._detect_worker.status_signal.connect(self._on_detect_status)
        self._detect_worker.finished_signal.connect(self._on_detect_finished)
        self._detect_worker.start()
    def _on_detect_status(self, status):
        if status == 'waiting':
            self.lbl_status.setText('Procurando dispositivo...')
            return
        if status == 'connected':
            self._set_phone('loading')
            self.lbl_status.setText('Dispositivo conectado!')
            self.lbl_status.setStyleSheet(f'color: {_Cores.PRIMARY};')
            self.lbl_phone.setText('Identificando...')
            return
        if status == 'success':
            self._anim.stop()
            self._set_phone('connected')
            self.lbl_status.setText('Modelo suportado!')
            self.lbl_status.setStyleSheet(f'color: {_Cores.SUCCESS}; font-weight: bold;')
            self.lbl_phone.setText('Pronto para remover FRP')
            return
        if status == 'error':
            self._anim.stop()
            self._set_phone('error')
            self.lbl_status.setText('Erro na detecao')
            self.lbl_status.setStyleSheet(f'color: {_Cores.ERROR};')
    def _on_srv_changed(self, row):
        '''Troca o loader ativo quando o t├®cnico seleciona outro SRV.'''
        matches = self._device_info.get('loader_matches', [])
        if 0 <= row < len(matches):
            self._loader_path = str(matches[row]['path'])
            mem = matches[row].get('memoria', 'emmc')
            self._device_info['memoria_auto'] = mem
            _log(f'Loader alterado para {matches[row].get('srv', '')} (id={matches[row]['id']}, mem={mem})')
    def _on_detect_finished(self, ok, msg, info):
        self._em_exec = False
        self.btn_parar.setEnabled(False)
        if ok and info.get('loader_found'):
            self._device_info = info
            self._loader_path = info.get('loader_path')
            self._lbl_fabricante.setText(info.get('vendor', 'Desconhecido'))
            self._lbl_chipset.setText(f'Qualcomm {info.get('chipset', '?')}')
            self._lbl_serial.setText(f'Serial: {info.get('serial', 'N/A').upper()}')
            self._lbl_instrucao.setText('Modelo suportado! Coloque o aparelho em modo EDL novamente e clique em Remover FRP.')
            self._lbl_instrucao.setStyleSheet(f'color: {_Cores.SUCCESS}; border: none;')
            self._info_frame.setVisible(True)
            matches = info.get('loader_matches', [])
            self._srv_list.clear()
            if len(matches) > 1:
                for m in matches:
                    self._srv_list.addItem(QListWidgetItem(m.get('srv', 'SRV?')))
                self._srv_list.setCurrentRow(0)
                self._srv_frame.setVisible(True)
            else:
                self._srv_frame.setVisible(False)
            self.btn_detectar.setEnabled(False)
            self.btn_remover.setEnabled(True)
            QMessageBox.information(self, 'Modelo Suportado', f'Fabricante: {info.get('vendor', '?')}\nChipset: Qualcomm {info.get('chipset', '?')}\nSerial: {info.get('serial', 'N/A').upper()}\n\nColoque o aparelho em modo EDL novamente\ne clique em "Remover FRP" para prosseguir.')
            return
        self.btn_detectar.setEnabled(True)
        self.btn_remover.setEnabled(False)
        self._info_frame.setVisible(False)
        if info:
            self._lbl_fabricante.setText(info.get('vendor', 'Desconhecido'))
            self._lbl_chipset.setText(f'Qualcomm {info.get('chipset', '?')}')
            self._lbl_instrucao.setText('Modelo nao suportado ÔÇö use o modo Manual')
            self._info_frame.setVisible(True)
            QMessageBox.warning(self, 'Modelo Nao Suportado', f'Fabricante: {info.get('vendor', '?')}\nChipset: {info.get('chipset', '?')}\n\nEste modelo ainda n├úo ├® suportado no modo autom├ítico.\nUse o modo Manual ou Parti├º├Áes.')
            return
        _log(f'Erro detecao: {msg}')
        QMessageBox.critical(self, 'Erro', 'N├úo foi poss├¡vel identificar o dispositivo.\n\nReconecte o aparelho em modo EDL e tente novamente.')
    def _remover_frp(self):
        if self._em_exec or not self._loader_path:
            return
        if self._auth_selector and self._auth_selector.is_forced():
            auth_tipo = self._auth_selector.get_auth_type()
            if _FRP_AUTH_OK and auth_tipo in ('xiaomi',):
                _log(f'Auth forcado ({auth_tipo}) ÔÇö usando FRP Auth direto')
                memoria = self._device_info.get('memoria_auto', 'emmc')
                vendor = self._device_info.get('vendor', 'Desconhecido')
                chipset = self._device_info.get('chipset', '?')
                reply = QMessageBox.question(self, 'Confirmar Remocao FRP', f'Fabricante: {vendor}\nChipset: Qualcomm {chipset}\n\nO aparelho precisa estar em modo EDL.\nO FRP sera removido e o aparelho reiniciara.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
                particoes = ['frp']
                factory = QMessageBox.question(self, 'Apagar dados do usuario?', 'Deseja tambem realizar o Factory Reset?\n\nIsso apagara todos os dados do usuario (fotos, apps, contas).\nRecomendado quando o aparelho esta com conta Google.\n\nApagar USERDATA?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if factory == QMessageBox.Yes:
                    particoes.append('userdata')
                    _log('Usuario optou por apagar userdata (Factory Reset)')
                else:
                    _log('Usuario optou por apagar somente FRP')
                self._em_exec = True
                self.btn_detectar.setEnabled(False)
                self.btn_remover.setEnabled(False)
                self.btn_parar.setEnabled(True)
                self.barra.setValue(5)
                self.lbl_status.setText('Conectando ao dispositivo...')
                self.lbl_status.setStyleSheet(f'color: {_Cores.WARNING};')
                self.lbl_phone.setText('Processando...')
                self._set_phone('loading')
                self._anim.start()
                self._frp_auth_worker = FrpAuthWorker(self._loader_path, memoria, particoes, auth_tipo)
                self._frp_auth_worker.log_signal.connect(self._on_frp_auth_log)
                self._frp_auth_worker.progress_signal.connect(self.barra.setValue)
                self._frp_auth_worker.status_signal.connect(self._on_oper_status)
                self._frp_auth_worker.finished_signal.connect(self._on_frp_auth_finished)
                self._frp_auth_worker.start()
                return
            _log(f'Auth forcado ({auth_tipo}) ÔÇö redirecionando para Particoes')
            QMessageBox.information(self, 'Verificacao Adicional', 'Este dispositivo precisa de uma etapa extra de verificacao.\n\nVoce sera redirecionado para a aba Particoes.\nAs particoes serao carregadas automaticamente.\n\nReconecte o aparelho em modo EDL\ne clique em OK para continuar.')
            self.redirecionar_particoes.emit({'auth_type': auth_tipo, 'loader_path': self._loader_path, 'device_info': self._device_info})
            return
        particoes = self._device_info.get('particoes_frp', _PARTICOES_DEFAULT)
        vendor = self._device_info.get('vendor', 'Desconhecido')
        chipset = self._device_info.get('chipset', '?')
        vendor_folder = self._device_info.get('vendor_folder', '')
        is_samsung = vendor_folder == 'samsung' or vendor.lower() == 'samsung'
        reply = QMessageBox.question(self, 'Confirmar Remocao FRP', f'Fabricante: {vendor}\nChipset: Qualcomm {chipset}\n\nO aparelho precisa estar em modo EDL.\nO FRP sera removido e o aparelho reiniciara.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self._em_exec = True
        self.btn_detectar.setEnabled(False)
        self.btn_remover.setEnabled(False)
        self.btn_parar.setEnabled(True)
        self.barra.setValue(10)
        self.lbl_status.setStyleSheet(f'color: {_Cores.WARNING};')
        self.lbl_phone.setText('Processando...')
        self._set_phone('loading')
        self._anim.start()
        memoria = self._device_info.get('memoria_auto', 'emmc')
        if is_samsung and _FRP_SAMSUNG_OK:
            _log('Samsung detectado ÔÇö usando FRP Samsung (program/patch)')
            self.lbl_status.setText('Removendo FRP Samsung...')
            self._frp_samsung_worker = FrpSamsungWorker(self._loader_path, memoria, ['persistent'])
            self._frp_samsung_worker.log_signal.connect(self._on_frp_auth_log)
            self._frp_samsung_worker.progress_signal.connect(self.barra.setValue)
            self._frp_samsung_worker.status_signal.connect(self._on_oper_status)
            self._frp_samsung_worker.finished_signal.connect(self._on_frp_auth_finished)
            self._frp_samsung_worker.start()
            return
        self.lbl_status.setText('Apagando particoes...')
        self._oper_worker = OperarWorker(self._loader_path, particoes, memoria)
        self._oper_worker.progress_signal.connect(self.barra.setValue)
        self._oper_worker.status_signal.connect(self._on_oper_status)
        self._oper_worker.finished_signal.connect(self._on_oper_finished)
        self._oper_worker.start()
    def _on_oper_status(self, status):
        if status == 'processing':
            self.lbl_status.setText('Apagando particoes...')
            self.lbl_status.setStyleSheet(f'color: {_Cores.WARNING};')
            return
        if status == 'success':
            self._anim.stop()
            self._set_phone('success')
            self.lbl_status.setText('FRP removido!')
            self.lbl_status.setStyleSheet(f'color: {_Cores.SUCCESS}; font-weight: bold;')
            self.lbl_phone.setText('Sucesso!')
            return
        if status == 'error':
            self._anim.stop()
            self._set_phone('error')
            self.lbl_status.setText('Erro')
            self.lbl_status.setStyleSheet(f'color: {_Cores.ERROR};')
    def _on_oper_finished(self, ok, msg):
        self._em_exec = False
        self._anim.stop()
        self.btn_parar.setEnabled(False)
        self.btn_detectar.setEnabled(True)
        matches = list(self._device_info.get('loader_matches', [])) if self._device_info else []
        mais_de_um_loader = len(matches) > 1
        if ok:
            self.btn_remover.setEnabled(False)
            self._loader_path = None
            self._device_info = {}
            self._info_frame.setVisible(False)
            self._srv_frame.setVisible(False)
            self._srv_list.clear()
            _limpar_temp_loaders()
            self.barra.setValue(100)
            QMessageBox.information(self, 'Sucesso', 'Opera├º├úo conclu├¡da com sucesso!\n\nReinicie o dispositivo para aplicar as altera├º├Áes.')
            return
        _log(f'Falha operacao FRP: {msg}')
        self.barra.setValue(0)
        if mais_de_um_loader:
            self._info_frame.setVisible(True)
            self._srv_frame.setVisible(True)
            if self._srv_list.count() != len(matches):
                self._srv_list.clear()
                for m in matches:
                    self._srv_list.addItem(QListWidgetItem(m.get('srv', 'SRV?')))
            row = self._srv_list.currentRow()
            if row < 0 or row >= len(matches):
                row = 0
                self._srv_list.setCurrentRow(0)
            self._loader_path = str(matches[row]['path'])
            self._device_info['memoria_auto'] = matches[row].get('memoria', 'emmc')
            self._lbl_instrucao.setText('Nao funcionou com esta origem de suporte.\nEscolha OUTRA opcao em Servidor de origem, reconecte em modo EDL\ne clique em Remover FRP novamente.')
            self._lbl_instrucao.setStyleSheet(f'color:{_Cores.WARNING};')
            self.lbl_status.setText('Escolha outra origem na lista abaixo')
            self.lbl_status.setStyleSheet(f'color:{_Cores.WARNING};')
            self._set_phone('error')
            self.lbl_phone.setText('Tente outra origem')
            self.btn_remover.setEnabled(True)
            QMessageBox.warning(self, 'Tente outra origem', 'Esta origem de suporte nao funcionou neste aparelho.\n\n1. Na lista Servidor de origem, selecione OUTRA opcao.\n2. Coloque o aparelho em modo EDL de novo.\n3. Clique em Remover FRP.\n\nSe nenhuma opcao funcionar, use a aba Manual ou Particoes.')
            return
        self.btn_remover.setEnabled(False)
        self._loader_path = None
        self._device_info = {}
        self._info_frame.setVisible(False)
        self._srv_frame.setVisible(False)
        self._srv_list.clear()
        _limpar_temp_loaders()
        QMessageBox.critical(self, 'Erro', 'Nao foi possivel concluir neste momento.\n\nReconecte o aparelho em modo EDL e clique em Detectar de novo.\nSe continuar falhando, use a aba Manual ou Particoes.')
    def _on_frp_auth_log(self, msg: str):
        '''Filtra logs do FRP Auth/Samsung e mostra etapas ao tecnico.'''
        txt = msg.strip()
        if not txt or txt.startswith('=') or txt.startswith('-'):
            return
        lower = txt.lower()
        if 'enviando programador' in lower:
            self.lbl_status.setText('Carregando loader...')
            self.lbl_phone.setText('Enviando...')
        elif 'autenticando' in lower:
            self.lbl_status.setText('Autenticando dispositivo...')
            self.lbl_phone.setText('Autenticando...')
        elif 'configurando' in lower:
            self.lbl_status.setText('Configurando dispositivo...')
        elif 'lendo mapa' in lower or 'particoes' in lower:
            self.lbl_status.setText('Lendo parti├º├Áes...')
            self.lbl_phone.setText('Lendo particoes...')
        elif 'zerando' in lower or 'apagando frp' in lower:
            self.lbl_status.setText('Removendo FRP...')
            self.lbl_phone.setText('Removendo FRP...')
        elif 'modo alternativo' in lower:
            self.lbl_status.setText('Removendo FRP (modo alternativo)...')
            self.lbl_phone.setText('Removendo FRP...')
        elif '% concluido' in lower:
            self.lbl_status.setText(f'Removendo FRP... {txt}')
        elif 'apagando userdata' in lower:
            self.lbl_status.setText('Factory Reset...')
            self.lbl_phone.setText('Factory Reset...')
        elif 'reiniciando' in lower:
            self.lbl_status.setText('Reiniciando dispositivo...')
            self.lbl_phone.setText('Reiniciando...')
        else:
            if 'sucesso' in lower or 'removido' in lower:
                self.lbl_status.setText('FRP removido com sucesso!')
                self.lbl_status.setStyleSheet(f'color: {_Cores.SUCCESS};')
                return
            return
        self.lbl_status.setStyleSheet(f'color: {_Cores.WARNING};')
    def _on_frp_auth_finished(self, ok, msg, device_data):
        self._em_exec = False
        self._anim.stop()
        self.btn_parar.setEnabled(False)
        self.btn_detectar.setEnabled(True)
        if ok:
            self.btn_remover.setEnabled(False)
            self._set_phone('success')
            self.lbl_status.setText('FRP removido!')
            self.lbl_status.setStyleSheet(f'color: {_Cores.SUCCESS}; font-weight: bold;')
            self.lbl_phone.setText('Sucesso!')
            self.barra.setValue(100)
            tempo = device_data.get('tempo_total', 0)
            apagadas = device_data.get('particoes_apagadas', [])
            mem = device_data.get('mem_type', '').upper()
            storage = device_data.get('storage_label', '')
            cap = device_data.get('capacidade_gb', 0)
            detalhes = []
            if mem:
                info_mem = f'Memoria: {mem}'
                if storage:
                    info_mem += f' ({storage})'
                if cap:
                    info_mem += f' ~{cap:.0f}GB'
                detalhes.append(info_mem)
            if apagadas:
                detalhes.append('FRP removido')
            if tempo:
                detalhes.append(f'Tempo: {tempo}s')
            info_text = '\n'.join(detalhes)
            QMessageBox.information(self, 'Sucesso', f'FRP removido com sucesso!\n\n{info_text}\n\nO aparelho vai reiniciar.\nConfigure normalmente.')
            self._loader_path = None
            self._device_info = {}
            self._info_frame.setVisible(False)
            self._srv_frame.setVisible(False)
            self._srv_list.clear()
            _limpar_temp_loaders()
            return
        _log(f'FRP Auth falhou: {msg} ÔÇö fallback para Particoes')
        self._set_phone('error')
        self.barra.setValue(0)
        auth_tipo = 'xiaomi'
        if self._auth_selector:
            auth_tipo = self._auth_selector.get_auth_type() or 'xiaomi'
        reply = QMessageBox.question(self, 'Operacao nao concluida', f'{msg}\n\nDeseja tentar pela aba Particoes?\n(La voce pode selecionar manualmente as particoes)', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            self.redirecionar_particoes.emit({'auth_type': auth_tipo, 'loader_path': self._loader_path, 'device_info': self._device_info})
            return
        self.btn_remover.setEnabled(True)
    def _parar(self):
        try:
            if self._detect_worker and self._detect_worker.isRunning():
                self._detect_worker.cancelar()
            if self._oper_worker and self._oper_worker.isRunning():
                self._oper_worker.cancelar()
            if self._frp_auth_worker and self._frp_auth_worker.isRunning():
                self._frp_auth_worker.cancelar()
            if self._frp_samsung_worker and self._frp_samsung_worker.isRunning():
                self._frp_samsung_worker.cancelar()
            _matar_processos_edl()
        finally:
            self._em_exec = False
            self._anim.stop()
            self._set_phone('notfound')
            self.barra.setValue(0)
            self.btn_detectar.setEnabled(True)
            self.btn_remover.setEnabled(False)
            self.btn_parar.setEnabled(False)
            self.lbl_status.setText('Cancelado')
            self.lbl_status.setStyleSheet(f'color: {_Cores.MUTED};')
            self.lbl_phone.setText('')
    def closeEvent(self, event):
        self._parar()
        _limpar_temp()
        super().closeEvent(event)
