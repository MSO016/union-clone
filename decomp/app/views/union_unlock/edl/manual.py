'''
Modo Manual EDL ÔÇö sele├º├úo de loader por arquivo com an├ílise integrada.
TECH UNION SOLUTIONS ÔÇö Ambiente de Desenvolvimento
Fluxo:
  1. T├®cnico seleciona loader (.elf/.mbn/.bin) via FileDialog
  2. Analisador extrai: chipsets compat├¡veis, assinante (OEM), integridade
  3. T├®cnico escolhe marca + mem├│ria + opera├º├úo
  4. Executa via edl-ng (cada opera├º├úo consome sess├úo Sahara)
Parti├º├Áes FRP por marca (validado em dispositivos reais):
  Samsung  ÔåÆ persistent
  Xiaomi   ÔåÆ frp + userdata
  Demais   ÔåÆ frp
'''
import logging
import os
import re
import sys
import subprocess
from pathlib import Path
from typing import (Dict, List, Optional)
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QFrame, QMessageBox, QComboBox, QFileDialog, QScrollArea)
from PyQt5.QtCore import (QThread, pyqtSignal, Qt, QVariantAnimation)
from PyQt5.QtGui import (QFont, QPixmap, QTransform)
try:
    from app.views.union_unlock.edl.config import (TOOLS_DIR, EDL_NG, QCOMVIEW, IMG_DIR, img_path, SVG_SETA_DOWN)
    from app.views.union_unlock.edl.edl_auth_config import (AuthSelectorWidget, resolver_auth_type, is_oppo_vip, is_oppo_vip2, extrair_vip_chipset)
    from app.views.union_unlock.edl.frp_xiaomi_auth import executar_frp_auth
except ImportError:
    from config import (TOOLS_DIR, EDL_NG, QCOMVIEW, IMG_DIR, img_path, SVG_SETA_DOWN)
    from edl_auth_config import (AuthSelectorWidget, resolver_auth_type, is_oppo_vip, is_oppo_vip2, extrair_vip_chipset)
    from frp_xiaomi_auth import executar_frp_auth
try:
    import app.views.union_unlock.edl.firehose_ops
    union_unlock
    _fhops = firehose_ops
    edl
    _FHOPS_OK = True
except ImportError:
    try:
        import firehose_ops as _fhops
        _FHOPS_OK = True
    except ImportError:
        _FHOPS_OK = False
try:
    from app.views.union_unlock.edl.frp_samsung import executar_frp_samsung
    _FRP_SAMSUNG_OK = True
except ImportError:
    try:
        from frp_samsung import executar_frp_samsung
        _FRP_SAMSUNG_OK = True
    except ImportError:
        _FRP_SAMSUNG_OK = False
try:
    from app.views.union_unlock.edl.frp_oppo_vip import executar_frp_vip
    _FRP_VIP_OK = True
except ImportError:
    try:
        from frp_oppo_vip import executar_frp_vip
        _FRP_VIP_OK = True
    except ImportError:
        _FRP_VIP_OK = False
try:
    from app.views.union_unlock.edl._qcom_io import executar_frp_serial
    _FRP_VIP2_OK = True
except ImportError:
    try:
        from _qcom_io import executar_frp_serial
        _FRP_VIP2_OK = True
    except ImportError:
        _FRP_VIP2_OK = False
_logger = logging.getLogger('edl_manual')
def _log(msg: str):
    _logger.debug(msg)
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
_TOOLS_DIR = TOOLS_DIR
_EDL_NG = EDL_NG
_QCOMVIEW = QCOMVIEW
_IMG_DIR = IMG_DIR
PARTICOES_FRP: Dict[str, List[str]] = {'Samsung': ['persistent'], 'Xiaomi': ['frp', 'userdata'], 'Motorola': ['frp'], 'Oppo': ['frp'], 'Vivo': ['frp'], 'Realme': ['frp'], 'Nokia': ['frp'], 'Huawei': ['frp'], 'Honor': ['frp'], 'LG': ['frp'], 'Asus': ['frp'], 'ZTE': ['frp']}
_PARTICOES_DEFAULT = ['frp']
PARTICOES_PROIBIDAS = {'efs', 'fsg', 'sec_efs', 'modemst1', 'modemst2'}
_HWID_CHIPSET = {'1b80e1': 'Snapdragon 680', '1920e1': 'Snapdragon 778G', '1a90e1': 'Snapdragon 695', '1db0e1': 'Snapdragon 6 Gen 1', '1ca0e1': 'Snapdragon 8 Gen 2', '1350e1': 'Snapdragon 888', '1630e1': 'Snapdragon 750G', '1490e1': 'Snapdragon 720G', '1360e1': 'Snapdragon 662', '10a0e1': 'Snapdragon 665', '11e0e1': 'Snapdragon 765G', '0e60e1': 'Snapdragon 730', '0c30e1': 'Snapdragon 865', '0a50e1': 'Snapdragon 855', '0ba0e1': 'Snapdragon 439/632', '0bf0e1': 'Snapdragon 439', '0db0e1': 'Snapdragon 665', '08b0e1': 'Snapdragon 845', '08c0e1': 'Snapdragon 660', '09a0e1': 'Snapdragon 450', '0950e1': 'Snapdragon 710', '05e0e1': 'Snapdragon 835', '0460e1': 'Snapdragon 625', '04f0e1': 'Snapdragon 430', '0560e1': 'Snapdragon 425', '15a0e1': 'QRB5165'}
class _AnalisadorWorker(QThread):
    '''Analisa loader com qcomview: chipsets (/m), assinante (/o), hashes (/h).'''
    finished_signal = pyqtSignal(dict)
    def __init__(self, loader_path: str):
        super().__init__()
        self._loader = loader_path
    def _exec_qcv(self, flag: str) -> str:
        if not _QCOMVIEW.exists():
            return ''
        cmd = [str(_QCOMVIEW), flag, self._loader]
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15, creationflags=flags)
            return (r.stdout or '') + (r.stderr or '')
        except Exception:
            return ''
    def _parse_cert(self, out_c0: str) -> Dict:
        '''Extrai informa├º├Áes do certificado raiz (/c0).'''
        cert = {}
        if not out_c0.strip():
            return cert
        for line in out_c0.split('\n'):
            stripped = line.strip()
            if 'Country' in stripped:
                m = re.search('string\\s+(.+)', stripped)
                if m:
                    cert['pais'] = m.group(1).strip()
                    continue
                continue
            if 'Organizational unit' in stripped or 'Organization' in stripped:
                m = re.search('string\\s+(.+)', stripped)
                if m:
                    val = m.group(1).strip()
                    if 'org' not in cert or len(val) > len(cert.get('org', '')):
                        cert['org'] = val
                        continue
                    continue
                continue
            if 'Common name' in stripped:
                m = re.search('string\\s+(.+)', stripped)
                if m:
                    cert['cn'] = m.group(1).strip()
                    continue
            else:
                if 'UTC time' not in stripped:
                    continue
                m = re.search('UTC time\\s+(.+)', stripped)
                if not m:
                    continue
                if 'validade_inicio' not in cert:
                    cert['validade_inicio'] = m.group(1).strip()
                    continue
                cert['validade_fim'] = m.group(1).strip()
                continue
        return cert
    def run(self):
        info = {'chipsets': [], 'assinante': 'Desconhecido', 'integridade': 'N/A', 'bits': '', 'hash_algo': '', 'pk_hash': '', 'certificado': {}}
        out_m = self._exec_qcv('/m')
        if out_m.strip():
            for line in out_m.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue
                if line.lower().startswith(('elf is', 'file is', 'no ')):
                    continue
                partes = line.split()
                if len(partes) >= 2:
                    hwid = partes[0].lower()
                    codename = partes[1]
                    if '???' in codename:
                        continue
                    chipset_nome = _HWID_CHIPSET.get(hwid[2:8], '')
                    info['chipsets'].append({'hwid': hwid, 'codename': codename, 'chipset': chipset_nome})
                else:
                    if len(partes) != 1:
                        continue
                    if partes[0][0].isalpha():
                        info['chipsets'].append({'hwid': '', 'codename': partes[0], 'chipset': ''})
        out_o = self._exec_qcv('/o')
        if out_o.strip():
            for line in out_o.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue
                if line.lower().startswith(('elf is', 'file is', 'no ')):
                    continue
                if len(line) < 60:
                    info['assinante'] = line
                break
        out_h = self._exec_qcv('/h')
        if out_h.strip():
            linhas = out_h.strip().split('\n')
            for primeira in linhas:
                primeira = primeira.strip()
                if not 'bit ELF' in primeira:
                    continue
                m = re.match('(\\d+)\\s+bit\\s+ELF.*?(SHA\\w+)', primeira, re.IGNORECASE)
                if m:
                    info['bits'] = m.group(1)
                    info['hash_algo'] = m.group(2)
                break
            falhas = sum((1 for l in linhas if 'FAIL' in l.upper()))
            oks = sum((1 for l in linhas if l.strip().endswith('Ok')))
            if falhas > 0:
                info['integridade'] = f'FALHA ({falhas} segmentos corrompidos)'
            elif oks > 0:
                info['integridade'] = f'OK ({oks} segmentos verificados)'
        out_p = self._exec_qcv('/p')
        if out_p.strip():
            for line in out_p.strip().split('\n'):
                line = line.strip()
                if line.lower().startswith(('elf is', 'file is', 'no ')):
                    continue
                if not re.match('^[0-9a-f\\s]+$', line, re.IGNORECASE):
                    continue
                if not len(line) > 20:
                    continue
                pk = line.replace(' ', '')
                if len(pk) >= 16:
                    info['pk_hash'] = pk[:32] + '...' if len(pk) > 32 else pk
                break
        out_c0 = self._exec_qcv('/c0')
        info['certificado'] = self._parse_cert(out_c0)
        self.finished_signal.emit(info)
class _ManualWorker(QThread):
    '''Executa opera├º├úo edl-ng: erase-part em sequ├¬ncia + reset.'''
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, loader_path: str, particoes: List[str], memoria: str):
        super().__init__()
        self._loader = loader_path
        self._particoes = particoes
        self._mem = 'Sdcc' if memoria == 'emmc' else 'Ufs'
        self._stop = False
    def cancelar(self):
        self._stop = True
    def _exec(self, args: List[str]) -> tuple:
        cmd = [str(_EDL_NG), '--loader', self._loader, '--memory', self._mem] + args
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=str(_TOOLS_DIR), creationflags=flags)
        ok = False
        no_dev = False
        erro_op = False
        for line in iter(proc.stdout.readline, ''):
            if self._stop:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=3)
                return (False, 'Cancelado pelo usu├írio')
            linha = line.rstrip()
            self.log_signal.emit(linha)
            ll = linha.lower()
            if 'found device' in ll:
                self.status_signal.emit('connected')
                self.progress_signal.emit(40)
            if 'loader uploaded' in ll and 'started successfully' in ll:
                self.status_signal.emit('processing')
                self.progress_signal.emit(50)
            if 'successfully erased' in ll:
                ok = True
                self.progress_signal.emit(80)
            elif 'power command' in ll and 'sent successfully' in ll:
                ok = True
            if 'no qualcomm edl devices found' in ll:
                no_dev = True
            if not any((p in ll for p in ('partition not found', 'failed to erase', 'not supported', 'sahara protocol error', 'signature verification failed', 'authentication failed', 'failed to send'))):
                continue
            erro_op = True
            continue
        proc.wait()
        if no_dev:
            return (False, 'Dispositivo n├úo detectado!\n\nConecte o aparelho em modo EDL antes de iniciar.')
        if erro_op and not ok:
            return (False, 'Operacao nao concluida.\n\nEste modelo pode nao ser suportado nesta versao.\nReconecte o dispositivo e tente novamente.')
        return ok, ''
    def run(self):
        try:
            if not os.path.exists(self._loader):
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Arquivo selecionado nao encontrado.\n\nSelecione o arquivo novamente.')
                return
            if not _EDL_NG.exists():
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Componente n├úo encontrado!\n\nReinstale o programa ou entre em contato com o suporte.')
                return
            self.status_signal.emit('waiting')
            self.progress_signal.emit(10)
            total = len(self._particoes)
            for i, part in enumerate(self._particoes, 1):
                if self._stop:
                    self.finished_signal.emit(False, 'Cancelado')
                    return
                if part.lower() in PARTICOES_PROIBIDAS:
                    _log(f'BLOQUEADO: particao protegida ÔÇö {part}')
                    continue
                self.progress_signal.emit(10 + int(70 * i / (total + 1)))
                ok, motivo = self._exec(['erase-part', part])
                if ok:
                    continue
                self.status_signal.emit('error')
                self.finished_signal.emit(False, motivo or 'Falha na opera├º├úo.\n\nReconecte o dispositivo em modo EDL e tente novamente.')
                return
            if not self._stop:
                self._exec(['reset'])
            self.progress_signal.emit(100)
            self.status_signal.emit('success')
            self.finished_signal.emit(True, 'Opera├º├úo conclu├¡da com sucesso!\n\nO aparelho ir├í reiniciar.')
            return
        except OSError as e:
            self.status_signal.emit('error')
            if hasattr(e, 'winerror') and e.winerror == 740:
                self.finished_signal.emit(False, 'Execute como Administrador!\n\nClique com bot├úo direito no programa\ne selecione "Executar como administrador".')
        except Exception:
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado na execu├º├úo.')
class _ManualAuthWorker(QThread):
    '''Worker FRP via QSaharaServer + fh_loader com autenticacao.'''
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, dict)
    def __init__(self, loader_path: str, memoria: str, particoes: list, auth_manufacturer: str='xiaomi'):
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
            self.status_signal.emit('connected')
            self.status_signal.emit('processing')
            ok, msg, data = executar_frp_auth(loader_path=self._loader, memoria=self._mem, particoes_alvo=self._particoes, log_cb=self._emit, progress_cb=self.progress_signal.emit, auth_manufacturer=self._auth)
            if self._cancelado:
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Cancelado pelo usuario.', {})
                return
            self.status_signal.emit('success' if ok else 'error')
            self.finished_signal.emit(ok, msg, data)
            return
        except Exception as e:
            _log(f'Erro _ManualAuthWorker: {e}')
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado.\n\nReconecte o dispositivo e tente novamente.', {})
    def _emit(self, msg: str):
        _log(msg)
        self.log_signal.emit(msg)
class _ManualSamsungWorker(QThread):
    '''Worker FRP Samsung via QSaharaServer + fh_loader (program/patch).'''
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, dict)
    def __init__(self, loader_path: str, memoria: str, particoes=None):
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
            self.status_signal.emit('connected')
            self.status_signal.emit('processing')
            ok, msg, data = executar_frp_samsung(loader_path=self._loader, memoria=self._mem, particoes_alvo=self._particoes, log_cb=self._emit, progress_cb=self.progress_signal.emit)
            if self._cancelado:
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Cancelado pelo usuario.', {})
                return
            self.status_signal.emit('success' if ok else 'error')
            self.finished_signal.emit(ok, msg, data)
            return
        except Exception as e:
            _log(f'Erro _ManualSamsungWorker: {e}')
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado.\n\nReconecte o dispositivo e tente novamente.', {})
    def _emit(self, msg: str):
        _log(msg)
        self.log_signal.emit(msg)
class _ManualFhWorker(QThread):
    '''Worker FRP generico via QSaharaServer + fh_loader (program/patch).
Usa o mesmo padrao validado do Samsung:
  1. Detecta porta ÔåÆ Upload loader (Sahara)
  2. Detecta storage ÔåÆ Le GPT
  3. Localiza particoes alvo ÔåÆ program zeros (fallback: patch)
  4. Reset
Funciona para qualquer marca sem autenticacao.
'''
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, loader_path: str, memoria: str, particoes: list):
        super().__init__()
        self._loader = loader_path
        self._mem = memoria
        self._particoes = particoes or ['frp']
        self._cancelado = False
    def cancelar(self):
        self._cancelado = True
        _matar_processos_edl()
    def run(self):
        try:
            self._executar()
            return
        except Exception as e:
            _log(f'Erro _ManualFhWorker: {e}')
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Operacao nao concluida.\n\nReconecte o dispositivo em modo EDL e tente novamente.')
    def _executar(self):
        self.progress_signal.emit(5)
        porta = _fhops.detectar_porta_com()
        if not porta:
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Dispositivo EDL nao encontrado.\n\nConecte o aparelho em modo EDL e tente novamente.')
            return
        self.status_signal.emit('connected')
        self.progress_signal.emit(15)
        _log(f'FH Worker: porta {porta}')
        ok, msg = _fhops.upload_loader(porta, self._loader, log_cb=self._lcb)
        if not ok:
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Falha na comunicacao com o dispositivo.\n\nReconecte em modo EDL e tente novamente.')
            return
        if self._cancelado:
            self.finished_signal.emit(False, 'Cancelado.')
            return
        self.status_signal.emit('processing')
        self.progress_signal.emit(30)
        mem_type, sector, num_luns, _ = _fhops.detect_storage_auto(porta, log_cb=self._lcb, memory_hint=self._mem)
        self.progress_signal.emit(45)
        try:
            from app.views.union_unlock.edl.gpt_parser import parse_gpt_file
        except ImportError:
            from gpt_parser import parse_gpt_file
        todas_particoes = []
        if mem_type == 'ufs':
            gpt_results = _fhops.get_all_gpt_ufs(porta, num_luns, log_cb=self._lcb)
            for lun, gpt_path in gpt_results:
                gpt_data = parse_gpt_file(gpt_path, sector)
                for p in gpt_data.get('partitions', []):
                    p['lun'] = lun
                todas_particoes.extend(gpt_data.get('partitions', []))
        else:
            ok_gpt, gpt_path = _fhops.get_gpt(porta, mem_type, 0, log_cb=self._lcb)
            if ok_gpt and gpt_path:
                gpt_data = parse_gpt_file(gpt_path, sector)
                for p in gpt_data.get('partitions', []):
                    p['lun'] = 0
                todas_particoes.extend(gpt_data.get('partitions', []))
        if not todas_particoes:
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Nao foi possivel ler as particoes do dispositivo.\n\nReconecte em modo EDL e tente novamente.')
            return
        self.progress_signal.emit(60)
        _log(f'FH Worker: {len(todas_particoes)} particoes encontradas')
        if self._cancelado:
            self.finished_signal.emit(False, 'Cancelado.')
            return
        alguma_ok = False
        for part_name in self._particoes:
            if self._cancelado:
                break
            lower = part_name.lower()
            if lower in PARTICOES_PROIBIDAS:
                continue
            matches = [p for p in todas_particoes if p['name'].lower() == lower]
            if not matches:
                self._lcb(f"Particao '{part_name}' nao encontrada.")
                if lower == 'userdata':
                    continue
                self.status_signal.emit('error')
                self.finished_signal.emit(False, f"Particao '{part_name}' nao encontrada no dispositivo.\n\nVerifique se o loader e compativel com este modelo.")
                return
            part_info = matches[0]
            lun = part_info.get('lun', 0)
            num_sectors = part_info.get('num_sectors', 0)
            size_mb = num_sectors * sector / 1048576
            self._lcb(f'Processando {part_name.upper()} ({size_mb:.1f} MB)...')
            if num_sectors > 20480:
                ok_op, msg_op = _fhops.erase_partition(porta, mem_type, part_info, sector, lun=lun, log_cb=self._lcb)
                if ok_op:
                    _log(f'{part_name} apagada via erase')
                    alguma_ok = True
                    continue
                _log(f'Erase falhou para {part_name}: {msg_op}')
            ok_prog, msg_prog = _fhops.program_partition(porta, mem_type, part_info, sector, lun=lun, log_cb=self._lcb)
            if ok_prog:
                _log(f'{part_name} zerada via program')
                alguma_ok = True
                continue
            self._lcb(f'Modo alternativo para {part_name.upper()}...')
            ok_patch, msg_patch = _fhops.patch_partition(porta, mem_type, part_info, sector, lun=lun, max_sectors=4, log_cb=self._lcb, progress_cb=self.progress_signal.emit, full_zero=False)
            if ok_patch:
                _log(f'{part_name} zerada via patch')
                alguma_ok = True
                continue
            _log(f'Falha em {part_name}: {msg_patch}')
            self.status_signal.emit('error')
            self.finished_signal.emit(False, f"Nao foi possivel processar '{part_name}'.\n\nEste modelo pode nao ser compativel com esta operacao.")
            return
        if not alguma_ok:
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Nenhuma particao foi processada.')
            return
        self.progress_signal.emit(90)
        _fhops.reset_device(porta, mem_type, log_cb=self._lcb)
        self.progress_signal.emit(100)
        self.status_signal.emit('success')
        self.finished_signal.emit(True, 'Operacao concluida com sucesso!\n\nO aparelho ira reiniciar.')
    def _lcb(self, msg: str):
        _log(msg)
class _ManualVipWorker(QThread):
    '''Worker FRP via QSaharaServer + VIP Auth + fh_loader patch.'''
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, dict)
    def __init__(self, loader_path: str, memoria: str, particoes: list, digest_data: bytes, sign_data: bytes):
        super().__init__()
        self._loader = loader_path
        self._mem = memoria
        self._particoes = particoes
        self._digest = digest_data
        self._sign = sign_data
        self._cancelado = False
    def cancelar(self):
        self._cancelado = True
        _matar_processos_edl()
    def run(self):
        try:
            self.status_signal.emit('connected')
            self.status_signal.emit('processing')
            ok, msg, data = executar_frp_vip(loader_path=self._loader, memoria=self._mem, digest_data=self._digest, sign_data=self._sign, particoes_alvo=self._particoes, log_cb=self._emit, progress_cb=self.progress_signal.emit)
            if self._cancelado:
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Cancelado pelo usuario.', {})
                return
            self.status_signal.emit('success' if ok else 'error')
            self.finished_signal.emit(ok, msg, data)
            return
        except Exception as e:
            _log(f'Erro _ManualVipWorker: {e}')
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado.\n\nReconecte o dispositivo e tente novamente.', {})
    def _emit(self, msg: str):
        _log(msg)
        self.log_signal.emit(msg)
class _ManualVip2Worker(QThread):
    '''Worker FRP via sessao direta (VIP 2).'''
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, dict)
    def __init__(self, port: str, loader_path: str, qsahara_path: str, memoria: str, digest_data: bytes, sign_data: bytes):
        super().__init__()
        self._port = port
        self._loader = loader_path
        self._qsahara = qsahara_path
        self._mem = memoria
        self._digest = digest_data
        self._sign = sign_data
        self._cancelado = False
    def cancelar(self):
        self._cancelado = True
    def run(self):
        try:
            self.status_signal.emit('connected')
            self.status_signal.emit('processing')
            ok, msg, data = executar_frp_serial(port=self._port, loader_path=self._loader, qsahara_path=self._qsahara, memory=self._mem, digest=self._digest, sign=self._sign, log_cb=self._emit, progress_cb=self.progress_signal.emit)
            if self._cancelado:
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Cancelado pelo usuario.', {})
                return
            self.status_signal.emit('success' if ok else 'error')
            self.finished_signal.emit(ok, msg, data)
            return
        except Exception as e:
            _log(f'Erro _ManualVip2Worker: {e}')
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado.\n\nReconecte o dispositivo e tente novamente.', {})
    def _emit(self, msg: str):
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
    INFO_BG = '#eaf2f8'
    INFO_BD = '#85c1e9'
class EdlManualWidget(QWidget):
    '''
Aba de modo manual ÔÇö fluxo simplificado:
  1. Selecionar loader ÔåÆ an├ílise autom├ítica (qcomview)
  2. Configurar marca + mem├│ria
  3. Escolher opera├º├úo (Remover FRP ou Factory Reset)
  4. Executar (consome sess├úo Sahara)
'''
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._analise_worker = None
        self._loader_path = None
        self._loader_info = {}
        self._em_exec = False
        self._setup_ui()
        self._init_animation()
    def _img(self, nome: str) -> str:
        return os.path.join(_IMG_DIR, nome)
    def _setup_ui(self):
        self.setStyleSheet(f'background-color: {_Cores.BG};')
        main = QHBoxLayout(self)
        main.setContentsMargins(10, 10, 10, 10)
        main.setSpacing(20)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left = QWidget()
        left.setStyleSheet('background: transparent;')
        ll = QVBoxLayout(left)
        ll.setContentsMargins(20, 15, 20, 15)
        ll.setSpacing(8)
        titulo = QLabel('Modo Manual EDL')
        titulo.setFont(QFont('Segoe UI', 20, QFont.Bold))
        titulo.setStyleSheet(f'color: {_Cores.PRIMARY};')
        titulo.setWordWrap(True)
        ll.addWidget(titulo)
        subtitulo = QLabel('Qualcomm Emergency Download (9008)')
        subtitulo.setFont(QFont('Segoe UI', 10))
        subtitulo.setStyleSheet(f'color: {_Cores.MUTED};')
        ll.addWidget(subtitulo)
        ll.addSpacing(12)
        self.btn_selecionar = QPushButton('­ƒôé  Selecionar Arquivo')
        self.btn_selecionar.setFixedHeight(42)
        self.btn_selecionar.setMinimumWidth(220)
        self.btn_selecionar.setMaximumWidth(320)
        self.btn_selecionar.setFont(QFont('Segoe UI', 12, QFont.Bold))
        self.btn_selecionar.setCursor(Qt.PointingHandCursor)
        self.btn_selecionar.setStyleSheet(f'\n            QPushButton {{\n                background-color: {_Cores.PRIMARY}; color: {_Cores.WHITE};\n                border: none; border-radius: 6px;\n            }}\n            QPushButton:hover {{ background-color: {_Cores.PRI_HOV}; }}\n        ')
        self.btn_selecionar.clicked.connect(self._selecionar_loader)
        ll.addWidget(self.btn_selecionar)
        self.lbl_arquivo = QLabel('Nenhum arquivo selecionado')
        self.lbl_arquivo.setFont(QFont('Segoe UI', 9))
        self.lbl_arquivo.setStyleSheet(f'color: {_Cores.MUTED};')
        self.lbl_arquivo.setWordWrap(True)
        ll.addWidget(self.lbl_arquivo)
        ll.addSpacing(4)
        self._info_frame = QFrame()
        self._info_frame.setStyleSheet(f'QFrame {{ background-color: {_Cores.INFO_BG}; border: 1px solid {_Cores.INFO_BD}; border-radius: 8px; }}')
        self._info_frame.setVisible(False)
        info_layout = QVBoxLayout(self._info_frame)
        info_layout.setContentsMargins(12, 10, 12, 10)
        info_layout.setSpacing(3)
        self._lbl_info_titulo = QLabel('­ƒöì Analise do Arquivo')
        self._lbl_info_titulo.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self._lbl_info_titulo.setStyleSheet(f'color: {_Cores.PRIMARY}; border: none;')
        info_layout.addWidget(self._lbl_info_titulo)
        self._lbl_assinante = QLabel()
        self._lbl_assinante.setFont(QFont('Segoe UI', 9))
        self._lbl_assinante.setStyleSheet(f'color: {_Cores.TEXT}; border: none;')
        self._lbl_assinante.setWordWrap(True)
        info_layout.addWidget(self._lbl_assinante)
        self._lbl_chipsets = QLabel()
        self._lbl_chipsets.setFont(QFont('Segoe UI', 9))
        self._lbl_chipsets.setStyleSheet(f'color: {_Cores.TEXT}; border: none;')
        self._lbl_chipsets.setWordWrap(True)
        info_layout.addWidget(self._lbl_chipsets)
        self._lbl_integridade = QLabel()
        self._lbl_integridade.setFont(QFont('Segoe UI', 9))
        self._lbl_integridade.setStyleSheet(f'color: {_Cores.TEXT}; border: none;')
        info_layout.addWidget(self._lbl_integridade)
        self._lbl_pkhash = QLabel()
        self._lbl_pkhash.setFont(QFont('Consolas', 8))
        self._lbl_pkhash.setStyleSheet(f'color: {_Cores.MUTED}; border: none;')
        self._lbl_pkhash.setWordWrap(True)
        self._lbl_pkhash.setTextInteractionFlags(Qt.TextSelectableByMouse)
        info_layout.addWidget(self._lbl_pkhash)
        self._lbl_certificado = QLabel()
        self._lbl_certificado.setFont(QFont('Segoe UI', 9))
        self._lbl_certificado.setStyleSheet(f'color: {_Cores.TEXT}; border: none;')
        self._lbl_certificado.setWordWrap(True)
        info_layout.addWidget(self._lbl_certificado)
        self._lbl_formato = QLabel()
        self._lbl_formato.setFont(QFont('Segoe UI', 9))
        self._lbl_formato.setStyleSheet(f'color: {_Cores.MUTED}; border: none;')
        info_layout.addWidget(self._lbl_formato)
        ll.addWidget(self._info_frame)
        ll.addSpacing(8)
        config_row = QHBoxLayout()
        config_row.setSpacing(8)
        lbl_marca = QLabel('Marca:')
        lbl_marca.setFont(QFont('Segoe UI', 10))
        lbl_marca.setStyleSheet(f'color: {_Cores.TEXT};')
        config_row.addWidget(lbl_marca)
        self.combo_marca = QComboBox()
        self.combo_marca.setFont(QFont('Segoe UI', 10))
        self.combo_marca.setFixedHeight(30)
        self.combo_marca.setMinimumWidth(100)
        self.combo_marca.setMaximumWidth(150)
        self.combo_marca.setStyleSheet(self._combo_style())
        for marca in ('Samsung', 'Xiaomi', 'Motorola', 'Oppo', 'Vivo', 'Realme', 'Nokia', 'Huawei', 'Honor', 'LG', 'Asus', 'ZTE', 'Gen├®rico'):
            self.combo_marca.addItem(marca)
        config_row.addWidget(self.combo_marca)
        config_row.addSpacing(8)
        lbl_mem = QLabel('Mem├│ria:')
        lbl_mem.setFont(QFont('Segoe UI', 10))
        lbl_mem.setStyleSheet(f'color: {_Cores.TEXT};')
        config_row.addWidget(lbl_mem)
        self.combo_mem = QComboBox()
        self.combo_mem.setFont(QFont('Segoe UI', 10))
        self.combo_mem.setFixedHeight(30)
        self.combo_mem.setMinimumWidth(80)
        self.combo_mem.setMaximumWidth(120)
        self.combo_mem.setStyleSheet(self._combo_style())
        self.combo_mem.addItem('UFS', 'ufs')
        self.combo_mem.addItem('eMMC', 'emmc')
        config_row.addWidget(self.combo_mem)
        config_row.addStretch()
        ll.addLayout(config_row)
        self._auth_selector = AuthSelectorWidget()
        ll.addWidget(self._auth_selector)
        ll.addSpacing(10)
        self.btn_frp = QPushButton('Remover FRP')
        self.btn_frp.setFixedSize(200, 42)
        self.btn_frp.setCursor(Qt.PointingHandCursor)
        self.btn_frp.setFont(QFont('Segoe UI', 12, QFont.Bold))
        self.btn_frp.setStyleSheet(f'\n            QPushButton {{\n                background-color: {_Cores.SUCCESS}; color: {_Cores.WHITE};\n                border: none; border-radius: 6px;\n            }}\n            QPushButton:hover {{ background-color: #229954; }}\n            QPushButton:disabled {{ background-color: {_Cores.BORDER}; }}\n        ')
        self.btn_frp.setEnabled(False)
        self.btn_frp.clicked.connect(self._remover_frp)
        ll.addWidget(self.btn_frp)
        self.btn_factory = QPushButton('Factory Reset')
        self.btn_factory.setFixedSize(200, 42)
        self.btn_factory.setCursor(Qt.PointingHandCursor)
        self.btn_factory.setFont(QFont('Segoe UI', 12, QFont.Bold))
        self.btn_factory.setStyleSheet(f'\n            QPushButton {{\n                background-color: {_Cores.ERROR}; color: {_Cores.WHITE};\n                border: none; border-radius: 6px;\n            }}\n            QPushButton:hover {{ background-color: #c0392b; }}\n            QPushButton:disabled {{ background-color: {_Cores.BORDER}; }}\n        ')
        self.btn_factory.setEnabled(False)
        self.btn_factory.clicked.connect(self._factory_reset)
        ll.addWidget(self.btn_factory)
        self.btn_parar = QPushButton('Parar')
        self.btn_parar.setFixedSize(120, 34)
        self.btn_parar.setCursor(Qt.PointingHandCursor)
        self.btn_parar.setFont(QFont('Segoe UI', 10))
        self.btn_parar.setStyleSheet(f'\n            QPushButton {{\n                background-color: {_Cores.BG_DARK}; color: {_Cores.TEXT};\n                border: 1px solid {_Cores.BORDER}; border-radius: 6px;\n            }}\n            QPushButton:hover {{ background-color: {_Cores.BORDER}; }}\n            QPushButton:disabled {{\n                background-color: {_Cores.BG}; border-color: {_Cores.BG};\n            }}\n        ')
        self.btn_parar.setEnabled(False)
        self.btn_parar.clicked.connect(self._parar)
        ll.addWidget(self.btn_parar)
        ll.addSpacing(4)
        self.barra = QProgressBar()
        self.barra.setMinimumWidth(220)
        self.barra.setMaximumWidth(320)
        self.barra.setFixedHeight(18)
        self.barra.setValue(0)
        self.barra.setTextVisible(False)
        self.barra.setStyleSheet(f'\n            QProgressBar {{ border: 1px solid {_Cores.BORDER}; border-radius: 9px;\n                background-color: {_Cores.BG_WHITE}; }}\n            QProgressBar::chunk {{ background-color: {_Cores.PRIMARY};\n                border-radius: 8px; }}\n        ')
        ll.addWidget(self.barra)
        ll.addStretch()
        aviso = QLabel('COMO ENTRAR EM MODO EDL:\n\nOP├ç├âO 1 ÔÇö Test Point (mais confi├ível):\n  Abra o aparelho e fa├ºa curto no ponto EDL\n\nOP├ç├âO 2 ÔÇö Bot├Áes:\n  Desligue, segure Vol+ e Vol-, conecte USB')
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
        scroll.setWidget(left)
        main.addWidget(scroll, stretch=1)
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
    def _combo_style(self) -> str:
        svg = SVG_SETA_DOWN.replace('\\', '/')
        return f'\n            QComboBox {{\n                background-color: {_Cores.BG_WHITE}; color: {_Cores.TEXT};\n                border: 1px solid {_Cores.BORDER}; border-radius: 4px;\n                padding: 2px 24px 2px 8px;\n            }}\n            QComboBox:hover {{ border-color: {_Cores.PRIMARY}; }}\n            QComboBox::drop-down {{\n                subcontrol-origin: padding;\n                subcontrol-position: top right;\n                width: 22px;\n                border-left: 1px solid {_Cores.BORDER};\n                border-top-right-radius: 4px;\n                border-bottom-right-radius: 4px;\n                background-color: #ecf0f1;\n            }}\n            QComboBox::drop-down:hover {{ background-color: #d5dbdb; }}\n            QComboBox::down-arrow {{\n                image: url({svg});\n                width: 10px; height: 10px;\n            }}\n            QComboBox QAbstractItemView {{\n                background-color: {_Cores.BG_WHITE}; color: {_Cores.TEXT};\n                border: 1px solid {_Cores.BORDER};\n                selection-background-color: {_Cores.PRIMARY};\n                selection-color: {_Cores.WHITE};\n                outline: none;\n            }}\n        '
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
    def _selecionar_loader(self):
        if self._em_exec:
            return
        docs_path = str(Path.home() / 'Documents')
        if not os.path.isdir(docs_path):
            docs_path = str(Path.home())
        path, _ = QFileDialog.getOpenFileName(self, 'Selecionar Arquivo de Suporte', docs_path, 'Arquivos Qualcomm (*.elf *.mbn *.bin *.melf);;Todos os arquivos (*.*)')
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        if ext not in ('.elf', '.mbn', '.bin', '.melf'):
            QMessageBox.warning(self, 'Arquivo inv├ílido', 'Selecione um arquivo .elf, .mbn, .bin ou .melf v├ílido.')
            return
        self._loader_path = path
        nome_arquivo = os.path.basename(path)
        self.lbl_arquivo.setText(f'Arquivo: {nome_arquivo}')
        self.lbl_arquivo.setStyleSheet(f'color: {_Cores.SUCCESS};')
        _log(f'Loader selecionado: {nome_arquivo}')
        mem_det = self._detectar_mem_do_loader(path)
        idx = 0 if mem_det == 'ufs' else 1
        self.combo_mem.setCurrentIndex(idx)
        _log(f'Memoria detectada pelo nome: {mem_det.upper()}')
        self._info_frame.setVisible(False)
        self._lbl_assinante.setText('')
        self._lbl_chipsets.setText('')
        self._lbl_integridade.setText('')
        self._lbl_pkhash.setText('')
        self._lbl_certificado.setText('')
        self._lbl_formato.setText('')
        self.btn_frp.setEnabled(False)
        self.btn_factory.setEnabled(False)
        self.lbl_status.setText('Analisando arquivo...')
        self.lbl_status.setStyleSheet(f'color: {_Cores.PRIMARY};')
        self.lbl_phone.setText('Analisando...')
        self._set_phone('loading')
        self._anim.start()
        self._analise_worker = _AnalisadorWorker(path)
        self._analise_worker.finished_signal.connect(self._on_analise_concluida)
        self._analise_worker.start()
    def _on_analise_concluida(self, info: dict):
        self._anim.stop()
        self._set_phone('notfound')
        self._loader_info = info
        assinante = info.get('assinante', 'Desconhecido')
        chipsets = info.get('chipsets', [])
        integridade = info.get('integridade', 'N/A')
        bits = info.get('bits', '')
        hash_algo = info.get('hash_algo', '')
        pk_hash = info.get('pk_hash', '')
        cert = info.get('certificado', {})
        self._lbl_assinante.setText(f'Fabricante: {assinante}')
        if chipsets:
            snapdragons = [c['chipset'] for c in chipsets if c.get('chipset')]
            unicos = list(dict.fromkeys(snapdragons))
            if unicos:
                snap_txt = ', '.join(unicos[:3])
                if len(unicos) > 3:
                    snap_txt += f' (+{len(unicos) - 3})'
                self._lbl_chipsets.setText(f'Processador: {snap_txt}')
            else:
                self._lbl_chipsets.setText(f'Compat├¡vel com {len(chipsets)} processadores Qualcomm')
        else:
            self._lbl_chipsets.setText('Processador: n├úo identificado')
        cor_integ = _Cores.SUCCESS if integridade.startswith('OK') else _Cores.ERROR
        if integridade == 'N/A':
            cor_integ = _Cores.MUTED
        self._lbl_integridade.setText(f'Integridade: {integridade}')
        self._lbl_integridade.setStyleSheet(f'color: {cor_integ}; border: none;')
        if pk_hash:
            self._lbl_pkhash.setText(f'PK_HASH: {pk_hash}')
            self._lbl_pkhash.setVisible(True)
        else:
            self._lbl_pkhash.setVisible(False)
        cert_parts = []
        if cert.get('org'):
            cert_parts.append(f'Origem: {cert['org']}')
        if cert.get('pais'):
            pais_map = {'CN': 'China', 'US': 'EUA', 'KR': 'Coreia do Sul', 'JP': 'Jap├úo', 'TW': 'Taiwan', 'IN': '├ìndia', 'DE': 'Alemanha', 'FI': 'Finl├óndia'}
            pais_nome = pais_map.get(cert['pais'], cert['pais'])
            cert_parts.append(f'Pa├¡s: {pais_nome}')
        if cert_parts:
            self._lbl_certificado.setText(' | '.join(cert_parts))
            self._lbl_certificado.setVisible(True)
        else:
            self._lbl_certificado.setVisible(False)
        fmt_parts = []
        if bits:
            fmt_parts.append(f'{bits}-bit')
        if hash_algo:
            fmt_parts.append(hash_algo)
        tamanho_kb = os.path.getsize(self._loader_path) // 1024 if self._loader_path and os.path.exists(self._loader_path) else 0
        if tamanho_kb > 0:
            fmt_parts.append(f'{tamanho_kb} KB')
        self._lbl_formato.setText(' | '.join(fmt_parts) if fmt_parts else '')
        self._info_frame.setVisible(True)
        assinante_lower = assinante.lower()
        org_lower = cert.get('org', '').lower()
        busca = assinante_lower + ' ' + org_lower
        marca_map = {'samsung': 'Samsung', 'xiaomi': 'Xiaomi', 'motorola': 'Motorola', 'lenovo': 'Motorola', 'oppo': 'Oppo', 'oneplus': 'Oppo', 'vivo': 'Vivo', 'realme': 'Realme', 'nokia': 'Nokia', 'hmd': 'Nokia', 'huawei': 'Huawei', 'honor': 'Honor', 'lg': 'LG', 'asus': 'Asus', 'zte': 'ZTE'}
        marca_detectada = None
        for chave, valor in marca_map.items():
            if not chave in busca:
                continue
            marca_detectada = valor
            break
        if marca_detectada:
            idx = self.combo_marca.findText(marca_detectada)
            if idx >= 0:
                self.combo_marca.setCurrentIndex(idx)
            _log(f'Marca auto-detectada: {marca_detectada}')
        has_fail = 'FALHA' in integridade
        if has_fail:
            self.lbl_status.setText('Arquivo com falha de integridade!')
            self.lbl_status.setStyleSheet(f'color: {_Cores.ERROR};')
            self.lbl_phone.setText('Arquivo corrompido')
            self._set_phone('error')
            self.btn_frp.setEnabled(False)
            self.btn_factory.setEnabled(False)
            QMessageBox.warning(self, 'Atencao', 'O arquivo selecionado apresenta falha de integridade.\n\nEste arquivo pode estar corrompido.\nSelecione outro arquivo.')
            return
        self.lbl_status.setText('Pronto ÔÇö selecione a operacao')
        self.lbl_status.setStyleSheet(f'color: {_Cores.SUCCESS}; font-weight: bold;')
        self.lbl_phone.setText('Pronto para operar')
        self._set_phone('connected')
        self.btn_frp.setEnabled(True)
        self.btn_factory.setEnabled(True)
    def _detectar_mem_do_loader(self, path: str) -> str:
        '''Detecta eMMC/UFS pelo nome do arquivo ou conteudo binario.'''
        nome = os.path.basename(path).lower()
        if 'ufs' in nome or 'prog_ufs' in nome:
            return 'ufs'
        if 'emmc' in nome or 'prog_emmc' in nome:
            return 'emmc'
        try:
            with open(path, 'rb') as f:
                dados = f.read(min(os.path.getsize(path), 65536))
            if b'ufs_' in dados or b'UFS_' in dados or b'prog_ufs' in dados:
                return 'ufs'
        except Exception:
            pass
        return 'emmc'
    def _remover_frp(self):
        if self._em_exec or not self._loader_path:
            return
        marca = self.combo_marca.currentText()
        particoes = PARTICOES_FRP.get(marca, _PARTICOES_DEFAULT)
        mem = self.combo_mem.currentData() or 'ufs'
        particoes_txt = ', '.join(particoes)
        reply = QMessageBox.question(self, 'Confirmar Remo├º├úo de FRP', f'Marca: {marca}\nMem├│ria: {mem.upper()}\nParti├º├Áes: {particoes_txt}\n\nO aparelho precisa estar em modo EDL.\nO FRP ser├í removido e o aparelho reiniciar├í.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self._iniciar_operacao(particoes, mem, 'Removendo FRP...')
    def _factory_reset(self):
        if self._em_exec or not self._loader_path:
            return
        mem = self.combo_mem.currentData() or 'ufs'
        reply = QMessageBox.warning(self, 'Factory Reset', f'ATEN├ç├âO: Factory Reset ir├í APAGAR TODOS OS DADOS!\n\nEsta a├º├úo n├úo pode ser desfeita.\n\nMem├│ria: {mem.upper()}\n\nO aparelho precisa estar em modo EDL.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self._iniciar_operacao(['userdata'], mem, 'Factory Reset...')
    def _iniciar_operacao(self, particoes: List[str], memoria: str, msg: str):
        self._em_exec = True
        self.btn_selecionar.setEnabled(False)
        self.btn_frp.setEnabled(False)
        self.btn_factory.setEnabled(False)
        self.btn_parar.setEnabled(True)
        self.combo_marca.setEnabled(False)
        self.combo_mem.setEnabled(False)
        self.barra.setValue(5)
        self.lbl_status.setText(msg)
        self.lbl_status.setStyleSheet(f'color: {_Cores.WARNING};')
        self.lbl_phone.setText('Conecte o celular em modo EDL')
        self._set_phone('loading')
        self._anim.start()
        marca = self.combo_marca.currentText()
        is_samsung = marca.lower() == 'samsung'
        auth_tipo = resolver_auth_type(None, self._auth_selector)
        if is_samsung and _FRP_SAMSUNG_OK and not auth_tipo:
            _log('Samsung detectado ÔÇö usando FRP Samsung (program/patch)')
            worker = _ManualSamsungWorker(self._loader_path, memoria, list(particoes))
            worker.log_signal.connect(self._on_samsung_log)
            worker.progress_signal.connect(self.barra.setValue)
            worker.status_signal.connect(self._on_status)
            worker.finished_signal.connect(self._on_auth_finished)
            self._worker = worker
            worker.start()
            return
        if is_oppo_vip2(auth_tipo) and _FRP_VIP2_OK:
            _log('OPPO VIP2 detectado ÔÇö sessao direta')
            _chipset = extrair_vip_chipset(auth_tipo)
            vip_digest, vip_sign = self._carregar_vip_data(chipset=_chipset)
            if not vip_digest or not vip_sign:
                self._finalizar_erro('Dados VIP nao encontrados para este chipset.\nCadastre no painel administrativo.')
                return
            from app.views.union_unlock.edl._qcom_io import detectar_porta_edl
            from app.views.union_unlock.edl.config import QSAHARA
            porta = detectar_porta_edl()
            if not porta:
                self._finalizar_erro('Dispositivo EDL nao encontrado.\nConecte em modo EDL e tente novamente.')
                return
            worker = _ManualVip2Worker(porta, self._loader_path, str(QSAHARA), memoria, vip_digest, vip_sign)
            worker.log_signal.connect(self._on_auth_log)
            worker.progress_signal.connect(self.barra.setValue)
            worker.status_signal.connect(self._on_status)
            worker.finished_signal.connect(self._on_auth_finished)
            self._worker = worker
            worker.start()
            return
        if is_oppo_vip(auth_tipo) and _FRP_VIP_OK:
            _log('OPPO VIP detectado ÔÇö usando FRP VIP (QSahara + VIP Auth + patch)')
            _chipset = extrair_vip_chipset(auth_tipo)
            vip_digest, vip_sign = self._carregar_vip_data(chipset=_chipset)
            if not vip_digest or not vip_sign:
                self._finalizar_erro('Dados VIP nao encontrados para este chipset.\nCadastre no painel administrativo.')
                return
            worker = _ManualVipWorker(self._loader_path, memoria, list(particoes), vip_digest, vip_sign)
            worker.log_signal.connect(self._on_auth_log)
            worker.progress_signal.connect(self.barra.setValue)
            worker.status_signal.connect(self._on_status)
            worker.finished_signal.connect(self._on_auth_finished)
            self._worker = worker
            worker.start()
            return
        if auth_tipo:
            _log(f'Auth selecionado: {auth_tipo} ÔÇö usando QSaharaServer + fh_loader')
            worker = _ManualAuthWorker(self._loader_path, memoria, list(particoes), auth_tipo)
            worker.log_signal.connect(self._on_auth_log)
            worker.progress_signal.connect(self.barra.setValue)
            worker.status_signal.connect(self._on_status)
            worker.finished_signal.connect(self._on_auth_finished)
            self._worker = worker
            worker.start()
            return
        if _FHOPS_OK:
            _log('Sem auth ÔÇö usando fh_loader (program/patch)')
            worker = _ManualFhWorker(self._loader_path, memoria, list(particoes))
            worker.log_signal.connect((lambda m: _log(m)))
            worker.progress_signal.connect(self.barra.setValue)
            worker.status_signal.connect(self._on_status)
            worker.finished_signal.connect(self._on_finished)
            self._worker = worker
            worker.start()
            return
        _log('Fallback: usando edl-ng')
        self._worker = _ManualWorker(self._loader_path, particoes, memoria)
        self._worker.log_signal.connect((lambda m: _log(m)))
        self._worker.progress_signal.connect(self.barra.setValue)
        self._worker.status_signal.connect(self._on_status)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.start()
    def _on_status(self, estado):
        if estado == 'waiting':
            self.lbl_status.setText('Aguardando dispositivo...')
            self.lbl_status.setStyleSheet(f'color: {_Cores.MUTED};')
            return
        if estado == 'connected':
            self._set_phone('loading')
            self.lbl_status.setText('Dispositivo conectado!')
            self.lbl_status.setStyleSheet(f'color: {_Cores.PRIMARY};')
            self.lbl_phone.setText('Conectando...')
            return
        if estado == 'processing':
            self._anim.stop()
            self._set_phone('connected')
            self.lbl_status.setText('Processando...')
            self.lbl_status.setStyleSheet(f'color: {_Cores.WARNING};')
            self.lbl_phone.setText('Opera├º├úo em andamento...')
            return
        if estado == 'success':
            self._anim.stop()
            self._set_phone('success')
            self.lbl_status.setText('Finalizado com sucesso!')
            self.lbl_status.setStyleSheet(f'color: {_Cores.SUCCESS}; font-weight: bold;')
            self.lbl_phone.setText('Conclu├¡do! Ô£à')
            return
        if estado == 'error':
            self._anim.stop()
            self._set_phone('error')
            self.lbl_status.setText('Erro no processo')
            self.lbl_status.setStyleSheet(f'color: {_Cores.ERROR};')
            self.lbl_phone.setText('Falha na opera├º├úo')
    def _on_finished(self, sucesso, msg):
        self._em_exec = False
        self._anim.stop()
        self.btn_selecionar.setEnabled(True)
        self.btn_parar.setEnabled(False)
        self.combo_marca.setEnabled(True)
        self.combo_mem.setEnabled(True)
        if self._loader_path:
            self.btn_frp.setEnabled(True)
            self.btn_factory.setEnabled(True)
        if sucesso:
            _log('Opera├º├úo conclu├¡da com sucesso')
            self._set_phone('success')
            self.barra.setValue(100)
            QMessageBox.information(self, 'Sucesso', msg)
            return
        _log('Opera├º├úo falhou')
        self._set_phone('error')
        self.lbl_phone.setText('Falha no processo')
        self.barra.setValue(0)
        QMessageBox.critical(self, 'Erro', msg)
    def _on_samsung_log(self, msg: str):
        '''Filtra e exibe progresso do frp_samsung na GUI.'''
        txt = msg.strip()
        if not txt or txt.startswith('=') or txt.startswith('-'):
            return
        lower = txt.lower()
        if 'enviando programador' in lower or 'carregando' in lower:
            self.lbl_status.setText('Carregando loader...')
            self.lbl_status.setStyleSheet(f'color: {_Cores.PRIMARY};')
            return
        if 'configurando' in lower or 'memoria' in lower:
            self.lbl_status.setText('Configurando dispositivo...')
            self.lbl_status.setStyleSheet(f'color: {_Cores.PRIMARY};')
            return
        if 'lendo mapa' in lower or 'particoes' in lower:
            self.lbl_status.setText('Lendo parti├º├Áes...')
            self.lbl_status.setStyleSheet(f'color: {_Cores.PRIMARY};')
            return
        if 'zerando' in lower or 'program' in lower:
            self.lbl_status.setText('Removendo FRP...')
            self.lbl_status.setStyleSheet(f'color: {_Cores.WARNING};')
            return
        if 'modo alternativo' in lower:
            self.lbl_status.setText('Removendo FRP (modo alternativo)...')
            self.lbl_status.setStyleSheet(f'color: {_Cores.WARNING};')
            return
        if '% concluido' in lower:
            self.lbl_status.setText(f'Removendo FRP... {txt}')
            self.lbl_status.setStyleSheet(f'color: {_Cores.WARNING};')
            return
        if 'reiniciando' in lower:
            self.lbl_status.setText('Reiniciando dispositivo...')
            self.lbl_status.setStyleSheet(f'color: {_Cores.PRIMARY};')
            return
        if 'sucesso' in lower or 'success' in lower:
            self.lbl_status.setText('FRP Samsung removido!')
            self.lbl_status.setStyleSheet(f'color: {_Cores.SUCCESS}; font-weight: bold;')
    def _on_auth_log(self, msg: str):
        '''Filtra e exibe progresso do frp_xiaomi_auth na GUI.'''
        txt = msg.strip()
        if not txt or txt.startswith('=') or txt.startswith('-'):
            return
        lower = txt.lower()
        if any((k in lower for k in ('sahara', 'uploading loader', 'loader carregado'))):
            self.lbl_status.setText('Carregando loader...')
            self.lbl_status.setStyleSheet(f'color: {_Cores.PRIMARY};')
            return
        if 'autenticando' in lower or 'auth' in lower:
            self.lbl_status.setText('Autenticando dispositivo...')
            self.lbl_status.setStyleSheet(f'color: {_Cores.WARNING};')
            return
        if 'parti├º├úo' in lower or 'partition' in lower or 'lun' in lower:
            self.lbl_status.setText('Lendo parti├º├Áes...')
            self.lbl_status.setStyleSheet(f'color: {_Cores.PRIMARY};')
            return
        if 'apagando' in lower or 'erase' in lower:
            self.lbl_status.setText(txt[:80])
            self.lbl_status.setStyleSheet(f'color: {_Cores.WARNING};')
            return
        if 'sucesso' in lower or 'success' in lower:
            self.lbl_status.setText('Opera├º├úo conclu├¡da!')
            self.lbl_status.setStyleSheet(f'color: {_Cores.SUCCESS}; font-weight: bold;')
    def _carregar_vip_data(self, chipset: Optional[str]=None, vip_auth_id: Optional[int]=None):
        '''Busca digest/sign VIP do cache SQLite local ou MySQL via _app_cfg.
        Prioridade: vip_auth_id (FK direta) > chipset > primeiro ativo.
        '''
        where = 'WHERE ativo=1'
        params_sqlite = ()
        params_mysql = ()
        if vip_auth_id is not None:
            where = 'WHERE id=?'
            params_sqlite = (vip_auth_id,)
            params_mysql = (vip_auth_id,)
        elif chipset:
            where += ' AND chipset=?'
            params_sqlite = (chipset,)
            params_mysql = (chipset,)
        query_sqlite = f'SELECT digest, sign_data FROM edl_auth_vip {where} LIMIT 1'
        query_mysql = query_sqlite.replace('?', '%s')
        try:
            import sqlite3
            _vip_db = None
            try:
                from app.utils.path_manager import PathManager
                tools = PathManager.get_unlock_tools_dir()
                if tools:
                    _candidate = os.path.normpath(os.path.join(os.path.dirname(tools), 'edl', 'edl_qcom.db'))
                    if os.path.isfile(_candidate):
                        _vip_db = _candidate
            except Exception:
                pass
            else:
                if not _vip_db:
                    _vip_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'edl_qcom.db')
                if os.path.exists(_vip_db):
                    conn = sqlite3.connect(_vip_db)
                    cur = conn.cursor()
        except Exception as e:
            _log(f'Cache VIP local nao disponivel: {e}')
        try:
            import pymysql
            from app.utils._app_cfg import db_config
            cfg = db_config(connect_timeout=10, read_timeout=15)
            conn = pymysql.connect(**cfg)
            cur = conn.cursor()
            cur.execute(query_mysql, params_mysql)
            row = cur.fetchone()
            conn.close()
            if row and row[0] and row[1]:
                _log(f'VIP data do MySQL ({len(row[0])}B + {len(row[1])}B){' chipset=' + chipset if chipset else ''}')
                return row[0], row[1]
        except Exception as e:
            _log(f'MySQL VIP nao disponivel: {e}')
        return (None, None)
    def _finalizar_erro(self, msg: str):
        '''Finaliza execucao com erro.'''
        self._em_exec = False
        self._anim.stop()
        self.btn_selecionar.setEnabled(True)
        self.btn_parar.setEnabled(False)
        self.combo_marca.setEnabled(True)
        self.combo_mem.setEnabled(True)
        if self._loader_path:
            self.btn_frp.setEnabled(True)
            self.btn_factory.setEnabled(True)
        self._set_phone('error')
        self.lbl_phone.setText('Erro')
        self.barra.setValue(0)
        QMessageBox.critical(self, 'Erro', msg)
    def _on_auth_finished(self, ok: bool, msg: str, device_data: dict):
        '''Callback do _ManualAuthWorker.'''
        self._em_exec = False
        self._anim.stop()
        self.btn_selecionar.setEnabled(True)
        self.btn_parar.setEnabled(False)
        self.combo_marca.setEnabled(True)
        self.combo_mem.setEnabled(True)
        if self._loader_path:
            self.btn_frp.setEnabled(True)
            self.btn_factory.setEnabled(True)
        if ok:
            _log('Opera├º├úo Auth conclu├¡da com sucesso')
            self._set_phone('success')
            self.barra.setValue(100)
            self.lbl_phone.setText('Conclu├¡do! Ô£à')
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
            QMessageBox.information(self, 'Sucesso', f'Operacao concluida com sucesso!\n\n{info_text}\n\nO aparelho vai reiniciar.\nConfigure normalmente.')
            return
        _log('Opera├º├úo Auth falhou')
        self._set_phone('error')
        self.lbl_phone.setText('Falha no processo')
        self.barra.setValue(0)
        QMessageBox.critical(self, 'Erro', msg)
    def _parar(self):
        try:
            if self._worker and self._worker.isRunning():
                self._worker.cancelar()
            _matar_processos_edl()
        finally:
            self._em_exec = False
            self._anim.stop()
            self._set_phone('notfound')
            self.barra.setValue(0)
            self.btn_selecionar.setEnabled(True)
            self.btn_parar.setEnabled(False)
            self.combo_marca.setEnabled(True)
            self.combo_mem.setEnabled(True)
            if self._loader_path:
                self.btn_frp.setEnabled(True)
                self.btn_factory.setEnabled(True)
            self.lbl_status.setText('Cancelado')
            self.lbl_status.setStyleSheet(f'color: {_Cores.MUTED};')
            self.lbl_phone.setText('')
    def closeEvent(self, event):
        self._parar()
        super().closeEvent(event)
# WARNING: Decompyle incomplete
