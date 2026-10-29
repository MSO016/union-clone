import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import (Dict, List, Optional)
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QFrame, QMessageBox, QComboBox, QFileDialog, QScrollArea, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QListWidget, QListWidgetItem, QLineEdit, QStackedWidget, QSizePolicy)
from PyQt5.QtCore import (QThread, pyqtSignal, pyqtSlot, Qt, QVariantAnimation)
from PyQt5.QtGui import (QFont, QPixmap, QTransform, QColor, QBrush)
try:
    from app.views.union_unlock.edl.config import (TOOLS_DIR, EDL_NG, QCOMVIEW, IMG_DIR, QSAHARA, FH_LOADER, img_path, SVG_SETA_DOWN)
    from app.views.union_unlock.edl.gpt_parser import parse_gpt_file, is_critical
    import app.views.union_unlock.edl.firehose_ops
    union_unlock
    fhops = firehose_ops
    edl
    from app.views.union_unlock.edl.edl_auth_config import (AuthSelectorWidget, resolver_auth_type, is_oppo_vip, is_oppo_vip2, extrair_vip_chipset)
except ImportError:
    from config import (TOOLS_DIR, EDL_NG, QCOMVIEW, IMG_DIR, QSAHARA, FH_LOADER, img_path, SVG_SETA_DOWN)
    from gpt_parser import parse_gpt_file, is_critical
    import firehose_ops as fhops
    from edl_auth_config import (AuthSelectorWidget, resolver_auth_type, is_oppo_vip, is_oppo_vip2, extrair_vip_chipset)
_logger = logging.getLogger('edl_partitions')
def _log(msg: str):
    _logger.debug(msg)
def _matar_processos_edl():
    if sys.platform != 'win32':
        return
    for exe in ('fh_loader.exe', 'QSaharaServer.exe', 'edl-ng.exe', 'FRP_EDL.exe', 'emmcdl.exe'):
        try:
            result = subprocess.run(['taskkill', '/F', '/IM', exe], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=5)
            if result.returncode == 0:
                _log(f'Processo {exe} encerrado')
        except Exception:
            continue
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
STORAGE_EMMC = 'emmc'
STORAGE_UFS = 'ufs'
STORAGE_INFO = {STORAGE_EMMC: {'label': 'eMMC', 'sector_size': 512, 'luns': [0], 'memory_arg': 'emmc'}, STORAGE_UFS: {'label': 'UFS', 'sector_size': 4096, 'luns': [0, 1, 2, 3, 4, 5], 'memory_arg': 'ufs'}}
ALL_BRANDS = [('Samsung', '#1428A0'), ('Xiaomi', '#ff6700'), ('Motorola', '#2471a3'), ('Oppo', '#1a9c2d'), ('Vivo', '#415fff'), ('Realme', '#ffc800'), ('Nokia', '#124191'), ('Huawei', '#cf0a2c'), ('LG', '#a50034'), ('Asus', '#00539b'), ('ZTE', '#0065b3')]
class _LoaderAnalyzerWorker(QThread):
    finished_signal = pyqtSignal(dict)
    def __init__(self, loader_path: str):
        super().__init__()
        self._loader = loader_path
    def _exec_qcv(self, flag: str) -> str:
        if not QCOMVIEW.exists():
            return ''
        cmd = [str(QCOMVIEW), flag, self._loader]
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15, creationflags=flags)
            return (r.stdout or '') + (r.stderr or '')
        except Exception:
            return ''
    def run(self):
        info = {'fabricante': 'Desconhecido', 'chipsets_total': 0, 'integridade': 'N/A', 'bits': '', 'hash_algo': '', 'pk_hash': '', 'tamanho_kb': 0}
        try:
            info['tamanho_kb'] = os.path.getsize(self._loader) // 1024
        except OSError:
            pass
        out_o = self._exec_qcv('/o')
        if out_o.strip():
            for line in out_o.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue
                if line.lower().startswith(('elf is', 'file is', 'no ')):
                    continue
                if len(line) < 60:
                    info['fabricante'] = line
                break
        out_m = self._exec_qcv('/m')
        if out_m.strip():
            total = 0
            for line in out_m.strip().split('\n'):
                line = line.strip()
                if not line or line.lower().startswith(('elf is', 'file is', 'no ')):
                    continue
                partes = line.split()
                if not len(partes) >= 2:
                    continue
                if '???' not in partes[1]:
                    total += 1
            info['chipsets_total'] = total
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
                info['integridade'] = f'FALHA ({falhas} segmentos)'
            elif oks > 0:
                info['integridade'] = f'OK ({oks} segmentos)'
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
        self.finished_signal.emit(info)
class _DetectPortWorker(QThread):
    finished = pyqtSignal(str)
    def run(self):
        self.finished.emit(fhops.detectar_porta_com() or '')
class _LoadGptWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished = pyqtSignal(bool, dict, str)
    def __init__(self, com_port, loader_path, memory, lun=0, skip_sahara=False, auto_detect=True, requer_auth=None, vip_auth_id=None):
        super().__init__()
        self._port = com_port
        self._loader = loader_path
        self._mem = memory
        self._lun = lun
        self._skip_sahara = skip_sahara
        self._auto_detect = auto_detect
        self._requer_auth = requer_auth
        self._vip_auth_id = vip_auth_id
    def run(self):
        vip_tmp = None
        try:
            self.progress_signal.emit(5)
            if not self._skip_sahara:
                ok, msg = fhops.upload_loader(self._port, self._loader, log_cb=self.log_signal.emit)
                if not ok:
                    self.finished.emit(False, {}, msg)
                    if vip_tmp:
                        if os.path.isdir(vip_tmp):
                            try:
                                shutil.rmtree(vip_tmp, ignore_errors=True)
                            except OSError:
                                pass
                            return
                        return
                    return
            else:
                self.log_signal.emit('Dispositivo ja conectado ÔÇö prosseguindo')
        except Exception as e:
            _log(f'Erro worker GPT: {e}')
            self.finished.emit(False, {}, 'Erro inesperado ao obter informacoes do dispositivo.\n\nReconecte o aparelho em modo EDL e tente novamente.')
        self.progress_signal.emit(15)
        if self._requer_auth == 'oneplus':
            auth_ok, auth_msg = fhops.firehose_auth_oneplus(self._port, self._loader, log_cb=self.log_signal.emit)
            if auth_ok:
                self.log_signal.emit('Dispositivo autenticado com sucesso!')
            else:
                self.log_signal.emit(f'Autenticacao: {auth_msg}')
        elif self._requer_auth == 'oneplus_vip':
            self.log_signal.emit('Este modelo nao e suportado nesta versao')
        elif self._requer_auth == 'xiaomi':
            auth_ok, auth_msg = fhops.firehose_auth(self._port, manufacturer='xiaomi', log_cb=self.log_signal.emit)
            if auth_ok:
                self.log_signal.emit('Dispositivo autenticado')
            else:
                self.log_signal.emit('Verificacao concluida')
        else:
            if is_oppo_vip2(self._requer_auth):
                _chipset = extrair_vip_chipset(self._requer_auth)
                dbytes, sbytes = get_vip_digest_sign(chipset=_chipset, vip_auth_id=self._vip_auth_id)
                if not dbytes or not sbytes:
                    self.finished.emit(False, {}, 'Dados VIP nao encontrados.\nSincronize o EDL (cache) ou cadastre no painel.')
                    if vip_tmp:
                        if os.path.isdir(vip_tmp):
                            try:
                                shutil.rmtree(vip_tmp, ignore_errors=True)
                            except OSError:
                                pass
                            return
                        return
                    return
                try:
                    mem_vip = (self._mem or 'emmc').lower()
                    if mem_vip not in ('emmc', 'ufs'):
                        mem_vip = 'emmc'
                    _session = QcomSession(self._port, mem_vip, log_cb=self.log_signal.emit)
                    if not _session.auth(dbytes, sbytes):
                        _session.close()
                        self.finished.emit(False, {}, 'Falha na autenticacao.')
                        if vip_tmp:
                            if os.path.isdir(vip_tmp):
                                try:
                                    shutil.rmtree(vip_tmp, ignore_errors=True)
                                except OSError:
                                    pass
                                return
                            return
                        return
                except Exception as e:
                    _log(f'Erro worker GPT: {e}')
                    self.finished.emit(False, {}, 'Erro inesperado ao obter informacoes do dispositivo.\n\nReconecte o aparelho em modo EDL e tente novamente.')
                try:
                    self.log_signal.emit('Autenticacao concluida ÔÇö lendo particoes...')
                    self.progress_signal.emit(35)
                    parts = _session.list_partitions()
                    if not parts:
                        _session.close()
                        self.finished.emit(False, {}, 'Nenhuma particao encontrada.')
                        if vip_tmp:
                            if os.path.isdir(vip_tmp):
                                try:
                                    shutil.rmtree(vip_tmp, ignore_errors=True)
                                except OSError:
                                    pass
                                return
                            return
                        return
                except Exception as e:
                    _log(f'Erro worker GPT: {e}')
                    self.finished.emit(False, {}, 'Erro inesperado ao obter informacoes do dispositivo.\n\nReconecte o aparelho em modo EDL e tente novamente.')
                try:
                    self._vip2_ser = _session._ser
                    _session._ser = None
                    sector = 512 if _session.memory == 'emmc' else 4096
                    from app.views.union_unlock.edl.gpt_parser import is_critical
                    _safe = frozenset({'frp', 'config', 'persist', 'persistent'})
                    _caution = frozenset({'misc', 'cache', 'userdata'})
                    all_partitions = []
                    for name, start, end, sz_mb in parts:
                        nl = name.lower()
                        if is_critical(name):
                            safety = 'critical'
                        elif nl in _safe:
                            safety = 'safe'
                        elif nl in _caution:
                            safety = 'caution'
                        else:
                            safety = 'unknown'
                        if sz_mb < 1:
                            size_human = f'{sz_mb * 1024:.1f} KB'
                        elif sz_mb < 1024:
                            size_human = f'{sz_mb:.1f} MB'
                        else:
                            size_human = f'{sz_mb / 1024:.2f} GB'
                        all_partitions.append({'name': name, 'start_lba': start, 'end_lba': end, 'num_sectors': end - start + 1, 'size_mb': sz_mb, 'size_human': size_human, 'safety': safety, 'lun': 0, 'critical': is_critical(name)})
                    self.progress_signal.emit(90)
                    self.log_signal.emit(f'Total: {len(all_partitions)} particoes')
                    self.finished.emit(True, {'partitions': all_partitions, 'mem_type': _session.memory, 'sector_size': sector, 'num_luns': 1}, '')
                except Exception as e:
                    _log(f'Erro worker GPT: {e}')
                    self.finished.emit(False, {}, 'Erro inesperado ao obter informacoes do dispositivo.\n\nReconecte o aparelho em modo EDL e tente novamente.')
                if vip_tmp:
                    if os.path.isdir(vip_tmp):
                        try:
                            shutil.rmtree(vip_tmp, ignore_errors=True)
                        except OSError:
                            pass
                        return
                    return
                return
            try:
                if is_oppo_vip(self._requer_auth):
                    pass
                try:
                    from app.views.union_unlock.edl.edl_sync import get_vip_digest_sign
                    from app.views.union_unlock.edl.frp_oppo_vip import _executar_vip_auth
                except ImportError:
                    from edl_sync import get_vip_digest_sign
                    from frp_oppo_vip import _executar_vip_auth
                else:
                    _chipset = extrair_vip_chipset(self._requer_auth)
                    dbytes, sbytes = get_vip_digest_sign(chipset=_chipset, vip_auth_id=self._vip_auth_id)
                    if not dbytes or not sbytes:
                        self.finished.emit(False, {}, 'Dados OPPO VIP nao encontrados.\nSincronize o EDL (cache) ou cadastre digest/sign no painel.')
            except Exception as e:
                _log(f'Erro worker GPT: {e}')
                self.finished.emit(False, {}, 'Erro inesperado ao obter informacoes do dispositivo.\n\nReconecte o aparelho em modo EDL e tente novamente.')
        self.progress_signal.emit(25)
        if self._auto_detect:
            mem_type, sector, num_luns, info = fhops.detect_storage_auto(self._port, log_cb=self.log_signal.emit, memory_hint=self._mem)
            self.log_signal.emit(f'Detectado: {mem_type.upper()} ÔÇö setor {sector}B ÔÇö {num_luns} LUN(s)')
        else:
            mem_type = self._mem
            ok_info, info = fhops.get_storage_info(self._port, self._mem, self._lun, log_cb=self.log_signal.emit)
            sector = info.get('sector_size', 512) if ok_info else 512
            detected = info.get('memory_type', self._mem)
            if detected == 'ufs' and mem_type != 'ufs':
                self.log_signal.emit('Dispositivo UFS detectado! Ajustando...')
                mem_type = 'ufs'
                sector = max(sector, 4096)
            num_luns = info.get('num_luns', 1)
            if mem_type == 'ufs' and num_luns < 2:
                num_luns = 6
        self.progress_signal.emit(35)
        is_ufs = mem_type == 'ufs'
        mem_arg = 'ufs' if is_ufs else 'emmc'
        _usa_read_gpt = is_oppo_vip(self._requer_auth) or is_oppo_vip2(self._requer_auth)
        if is_ufs:
            all_partitions = []
            all_lun_data = {}
            if _usa_read_gpt:
                gpt_results = []
                for lun_i in range(num_luns):
                    ok_g, gp = fhops.get_gpt_via_read(self._port, mem_arg, lun_i, log_cb=self.log_signal.emit)
                    if ok_g:
                        gpt_results.append((lun_i, gp))
            else:
                gpt_results = fhops.get_all_gpt_ufs(self._port, num_luns, log_cb=self.log_signal.emit)
            total_luns = len(gpt_results)
            for idx, (lun, gpt_path) in enumerate(gpt_results):
                pct = 35 + int((idx + 1) / max(total_luns, 1) * 55)
                self.progress_signal.emit(pct)
                gpt_data = parse_gpt_file(gpt_path, sector)
                parts = gpt_data.get('partitions', [])
                for p in parts:
                    p['lun'] = lun
                all_partitions.extend(parts)
                all_lun_data[lun] = gpt_data
            result = {'partitions': all_partitions, 'storage_info': info, 'lun': 'all', 'lun_data': all_lun_data, 'com_port': self._port, 'memory': mem_arg, 'loader': self._loader, 'sector_size': sector, 'is_ufs': True, 'num_luns': num_luns}
            self.progress_signal.emit(95)
            self.log_signal.emit(f'UFS: {len(all_partitions)} particoes em {total_luns} LUN(s) com dados')
        else:
            self.progress_signal.emit(50)
            if _usa_read_gpt:
                ok_gpt, gpt_path = fhops.get_gpt_via_read(self._port, mem_arg, self._lun, log_cb=self.log_signal.emit)
            else:
                ok_gpt, gpt_path = fhops.get_gpt(self._port, mem_arg, self._lun, log_cb=self.log_signal.emit)
            if not ok_gpt:
                self.finished.emit(False, {}, gpt_path)
                if vip_tmp:
                    if os.path.isdir(vip_tmp):
                        try:
                            shutil.rmtree(vip_tmp, ignore_errors=True)
                        except OSError:
                            pass
                        return
                    return
                return
        self.progress_signal.emit(100)
        self.finished.emit(True, result, '')
        if vip_tmp:
            if os.path.isdir(vip_tmp):
                try:
                    self.progress_signal.emit(80)
                    gpt_data = parse_gpt_file(gpt_path, sector)
                    for p in gpt_data.get('partitions', []):
                        p['lun'] = 0
                    result = gpt_data
                    result['storage_info'] = info
                    result['lun'] = self._lun
                    result['com_port'] = self._port
                    result['memory'] = mem_arg
                    result['loader'] = self._loader
                    result['sector_size'] = sector
                    result['is_ufs'] = False
                except OSError:
                    return
                    try:
                        shutil.rmtree(vip_tmp, ignore_errors=True)
                    except Exception as e:
                        _log(f'Erro worker GPT: {e}')
                        self.finished.emit(False, {}, 'Erro inesperado ao obter informacoes do dispositivo.\n\nReconecte o aparelho em modo EDL e tente novamente.')
class _OperationWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, op, com_port, memory, partition, sector_size, lun=0, file_path='', requer_auth=None, loader_path='', vip_auth_id=None, vip2_ser=None):
        super().__init__()
        self._op = op
        self._port = com_port
        self._mem = memory
        self._part = partition
        self._sector = sector_size
        self._lun = lun
        self._file = file_path
        self._requer_auth = requer_auth
        self._vip2_ser = vip2_ser
        self._loader_path = loader_path
        self._vip_auth_id = vip_auth_id
    def _run_vip2(self):
        try:
            from app.views.union_unlock.edl._qcom_io import QcomSession, _XML_H as XML_HEADER
            from app.views.union_unlock.edl.config import QSAHARA
            from app.views.union_unlock.edl.edl_sync import get_vip_digest_sign
        except ImportError:
            from _qcom_io import QcomSession, _XML_H as XML_HEADER
            from config import QSAHARA
            from edl_sync import get_vip_digest_sign
        session = QcomSession(self._port, self._mem, log_cb=self.log_signal.emit, progress_cb=self.progress_signal.emit)
        ser = self._vip2_ser
        if ser and ser.is_open:
            session._ser = ser
            nop = XML_HEADER + b'<data><nop /></data>'
            try:
                ser.write(nop)
                ser.flush()
                resp = session._recv(b'ACK', timeout_s=4.0)
                if b'ACK' not in resp or b'VIP is enabled' in resp:
                    ser = None
            except Exception:
                ser = None
        if not ser or not ser.is_open:
            session._ser = None
            self.log_signal.emit('Reconectando ao dispositivo...')
            _chipset = extrair_vip_chipset(self._requer_auth)
            dbytes, sbytes = get_vip_digest_sign(chipset=_chipset, vip_auth_id=self._vip_auth_id)
            if not dbytes or not sbytes:
                return (False, 'Dados de autenticacao nao disponiveis.')
            if not session.sahara(self._loader_path, str(QSAHARA)):
                session.close()
                return (False, 'Falha na comunicacao inicial.')
            import time
            time.sleep(0.5)
            if not session.auth(dbytes, sbytes):
                session.close()
                return (False, 'Falha na autenticacao.')
        name = self._part.get('name', '') if isinstance(self._part, dict) else ''
        start = self._part.get('start_lba', 0) if isinstance(self._part, dict) else 0
        sectors = self._part.get('num_sectors', 0) if isinstance(self._part, dict) else 0
        ok = False
        msg = ''
        try:
            if self._op == 'erase':
                ok = session.erase_partition(name, start, sectors)
                msg = 'Particao limpa.' if ok else 'Falha ao limpar.'
            elif self._op == 'read':
                ok = session.read_partition(start, sectors, self._file)
                msg = 'Leitura concluida.' if ok else 'Falha na leitura.'
            elif self._op in ('write', 'program'):
                if self._file and os.path.isfile(self._file):
                    data = open(self._file, 'rb').read()
                    ok = session.write_partition(start, sectors, data)
                    if ok:
                        msg = 'Escrita concluida.'
                    elif getattr(session, '_write_fw_blocked', False):
                        msg = 'Escrita nao permitida pelo firmware.'
                    else:
                        msg = 'Falha na escrita.'
                else:
                    ok = session.erase_header(name, start, sectors)
                    msg = 'Particao invalidada.' if ok else 'Falha na operacao.'
            else:
                msg = 'Operacao nao suportada.'
        finally:
            self._vip2_ser = session._ser
            session._ser = None
        return ok, msg
    def run(self):
        try:
            self.progress_signal.emit(20)
            self.status_signal.emit('processing')
            if is_oppo_vip2(self._requer_auth):
                ok, msg = self._run_vip2()
                self.progress_signal.emit(100)
                self.status_signal.emit('success' if ok else 'error')
                self.finished_signal.emit(ok, msg)
                return
            _vip = is_oppo_vip(self._requer_auth)
            if self._op == 'erase':
                if _vip:
                    self.log_signal.emit('VIP: usando patch mode (erase bloqueado neste loader)')
                    ok, msg = fhops.patch_partition(self._port, self._mem, self._part, self._sector, self._lun, max_sectors=4, log_cb=self.log_signal.emit, progress_cb=self.progress_signal.emit)
                else:
                    ok, msg = fhops.erase_partition(self._port, self._mem, self._part, self._sector, self._lun, log_cb=self.log_signal.emit)
            elif self._op == 'program':
                if _vip:
                    self.log_signal.emit('VIP: usando patch mode (program bloqueado neste loader)')
                    ok, msg = fhops.patch_partition(self._port, self._mem, self._part, self._sector, self._lun, max_sectors=4, log_cb=self.log_signal.emit, progress_cb=self.progress_signal.emit)
                else:
                    ok, msg = fhops.program_partition(self._port, self._mem, self._part, self._sector, self._lun, log_cb=self.log_signal.emit)
                    if not ok:
                        if msg == 'NAK_PROGRAM':
                            self.log_signal.emit('Program bloqueado, tentando modo alternativo...')
                            ok, msg = fhops.patch_partition(self._port, self._mem, self._part, self._sector, self._lun, max_sectors=4, log_cb=self.log_signal.emit, progress_cb=self.progress_signal.emit, full_zero=False)
            elif self._op == 'read':
                if _vip:
                    ok, msg = fhops.read_partition_via_sendxml(self._port, self._mem, self._part, self._sector, self._file, self._lun, log_cb=self.log_signal.emit)
                else:
                    ok, msg = fhops.read_partition(self._port, self._mem, self._part, self._sector, self._file, self._lun, log_cb=self.log_signal.emit)
            elif self._op == 'write':
                ok, msg = fhops.write_partition(self._port, self._mem, self._part, self._sector, self._file, self._lun, log_cb=self.log_signal.emit)
            else:
                ok, msg = False, f'Operacao desconhecida: {self._op}'
            self.progress_signal.emit(100)
            self.status_signal.emit('success' if ok else 'error')
            self.finished_signal.emit(ok, msg)
            return
        except Exception as e:
            _log(f'Erro operacao: {e}')
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado')
class _PartitionOpsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._gpt_data = {}
        self._com_port = ''
        self._loader_path = ''
        self._storage_type = STORAGE_EMMC
        self._current_lun = 0
        self._sector_size = 512
        self._em_operacao = False
        self._skip_sahara = False
        self._requer_auth = None
        self._vip_auth_id = None
        self._auto_start_leitura = False
        self._gpt_worker = None
        self._op_worker = None
        self._vip2_ser = None
        self._multi_queue = None
        self._multi_total = 0
        self._multi_done = 0
        self._multi_op_type = 'read'
        self._setup_ui()
        self._init_animation()
    def _setup_ui(self):
        self.setStyleSheet(f'background-color: {_Cores.BG};')
        main = QHBoxLayout(self)
        main.setContentsMargins(6, 4, 6, 4)
        main.setSpacing(8)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea{border:none;background:transparent;}')
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left = QWidget()
        left.setStyleSheet('background:transparent;')
        ll = QVBoxLayout(left)
        ll.setContentsMargins(6, 4, 6, 4)
        ll.setSpacing(4)
        cfg = QHBoxLayout()
        cfg.setSpacing(8)
        lbl_st = QLabel('Armazenamento:')
        lbl_st.setFont(QFont('Segoe UI', 10))
        lbl_st.setStyleSheet(f'color:{_Cores.TEXT};')
        cfg.addWidget(lbl_st)
        self.combo_storage = QComboBox()
        self.combo_storage.setFont(QFont('Segoe UI', 10))
        self.combo_storage.setMinimumSize(80, 28)
        self.combo_storage.setMaximumHeight(28)
        self.combo_storage.setStyleSheet(self._combo_css())
        self.combo_storage.addItem('eMMC', STORAGE_EMMC)
        self.combo_storage.addItem('UFS', STORAGE_UFS)
        self.combo_storage.currentIndexChanged.connect(self._on_storage_changed)
        cfg.addWidget(self.combo_storage)
        self.lbl_lun = QLabel('LUN:')
        self.lbl_lun.setFont(QFont('Segoe UI', 10))
        self.lbl_lun.setStyleSheet(f'color:{_Cores.TEXT};')
        self.lbl_lun.setVisible(False)
        cfg.addWidget(self.lbl_lun)
        self.combo_lun = QComboBox()
        self.combo_lun.setFont(QFont('Segoe UI', 10))
        self.combo_lun.setFixedSize(55, 28)
        self.combo_lun.setStyleSheet(self._combo_css())
        self.combo_lun.addItem('0', 0)
        self.combo_lun.setVisible(False)
        cfg.addWidget(self.combo_lun)
        self._auth_selector = AuthSelectorWidget()
        cfg.addWidget(self._auth_selector)
        cfg.addStretch()
        self.btn_ler = QPushButton('Ler Particoes')
        self.btn_ler.setMinimumSize(120, 32)
        self.btn_ler.setMaximumSize(180, 32)
        self.btn_ler.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self.btn_ler.setCursor(Qt.PointingHandCursor)
        self.btn_ler.setStyleSheet(f'\n            QPushButton{{background-color:{_Cores.WARNING};color:{_Cores.WHITE};\n                border:none;border-radius:5px;}}\n            QPushButton:hover{{background-color:#d68910;}}\n            QPushButton:disabled{{background-color:{_Cores.BORDER};}}\n        ')
        self.btn_ler.setEnabled(False)
        self.btn_ler.clicked.connect(self._ler_particoes)
        cfg.addWidget(self.btn_ler)
        ll.addLayout(cfg)
        self._info_frame = QFrame()
        self._info_frame.setStyleSheet(f'QFrame{{background-color:{_Cores.INFO_BG};border:1px solid {_Cores.INFO_BD};border-radius:6px;}}')
        self._info_frame.setVisible(False)
        self._info_frame.setMinimumHeight(36)
        self._info_frame.setMaximumHeight(50)
        ifl = QHBoxLayout(self._info_frame)
        ifl.setContentsMargins(10, 4, 10, 4)
        ifl.setSpacing(12)
        self._lbl_storage = QLabel()
        self._lbl_storage.setFont(QFont('Segoe UI', 9))
        self._lbl_storage.setStyleSheet(f'color:{_Cores.TEXT};border:none;')
        ifl.addWidget(self._lbl_storage)
        self._lbl_pcount = QLabel()
        self._lbl_pcount.setFont(QFont('Segoe UI', 9, QFont.Bold))
        self._lbl_pcount.setStyleSheet(f'color:{_Cores.PRIMARY};border:none;')
        ifl.addWidget(self._lbl_pcount)
        ifl.addStretch()
        ll.addWidget(self._info_frame)
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(['', 'Nome', 'LUN', 'Inicio (LBA)', 'Setores', 'Tamanho', 'Status'])
        h = self.table.horizontalHeader()
        h.setFont(QFont('Segoe UI', 9, QFont.Bold))
        self.table.setColumnWidth(0, 30)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(2, 40)
        self.table.setColumnWidth(3, 95)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 80)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setMinimumHeight(120)
        self.table.setStyleSheet(f'\n            QTableWidget{{background-color:{_Cores.BG_WHITE};color:{_Cores.TEXT};\n                gridline-color:{_Cores.BORDER};border:1px solid {_Cores.BORDER};\n                border-radius:4px;}}\n            QTableWidget::item{{padding:3px 5px;}}\n            QTableWidget::item:selected{{background-color:{_Cores.PRIMARY};\n                color:{_Cores.WHITE};}}\n            QHeaderView::section{{background-color:{_Cores.BG_DARK};color:{_Cores.TEXT};\n                border:1px solid {_Cores.BORDER};padding:3px;font-weight:bold;}}\n        ')
        self.table.setVisible(False)
        self.table.itemChanged.connect(self._on_check_changed)
        ll.addWidget(self.table, stretch=1)
        sel_row = QHBoxLayout()
        sel_row.setSpacing(6)
        _btn_css_sm = f'QPushButton{{background-color:{_Cores.BG_WHITE};color:{_Cores.TEXT};border:1px solid {_Cores.BORDER};border-radius:3px;padding:2px 8px;font-size:9px;}}QPushButton:hover{{background-color:{_Cores.BG_DARK};}}'
        self.btn_sel_all = QPushButton('Selecionar Tudo')
        self.btn_sel_all.setCursor(Qt.PointingHandCursor)
        self.btn_sel_all.setStyleSheet(_btn_css_sm)
        self.btn_sel_all.setFixedHeight(22)
        self.btn_sel_all.clicked.connect(self._select_all)
        self.btn_sel_all.setVisible(False)
        sel_row.addWidget(self.btn_sel_all)
        self.btn_unsel_all = QPushButton('Desmarcar Tudo')
        self.btn_unsel_all.setCursor(Qt.PointingHandCursor)
        self.btn_unsel_all.setStyleSheet(_btn_css_sm)
        self.btn_unsel_all.setFixedHeight(22)
        self.btn_unsel_all.clicked.connect(self._unselect_all)
        self.btn_unsel_all.setVisible(False)
        sel_row.addWidget(self.btn_unsel_all)
        self.lbl_sel_count = QLabel('')
        self.lbl_sel_count.setFont(QFont('Segoe UI', 9))
        self.lbl_sel_count.setStyleSheet(f'color:{_Cores.PRIMARY};font-weight:bold;')
        self.lbl_sel_count.setVisible(False)
        sel_row.addWidget(self.lbl_sel_count)
        sel_row.addStretch()
        ll.addLayout(sel_row)
        ops = QHBoxLayout()
        ops.setSpacing(6)
        self.btn_backup = QPushButton('Backup')
        self.btn_backup.setMinimumSize(70, 32)
        self.btn_backup.setMaximumHeight(32)
        self.btn_backup.setCursor(Qt.PointingHandCursor)
        self.btn_backup.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self.btn_backup.setStyleSheet(f'\n            QPushButton{{background-color:{_Cores.PRIMARY};color:{_Cores.WHITE};\n                border:none;border-radius:5px;}}\n            QPushButton:hover{{background-color:{_Cores.PRI_HOV};}}\n            QPushButton:disabled{{background-color:{_Cores.BORDER};}}\n        ')
        self.btn_backup.setEnabled(False)
        self.btn_backup.clicked.connect(self._backup)
        ops.addWidget(self.btn_backup)
        self.btn_write = QPushButton('Gravar')
        self.btn_write.setMinimumSize(70, 32)
        self.btn_write.setMaximumHeight(32)
        self.btn_write.setCursor(Qt.PointingHandCursor)
        self.btn_write.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self.btn_write.setStyleSheet(f'\n            QPushButton{{background-color:{_Cores.WARNING};color:{_Cores.WHITE};\n                border:none;border-radius:5px;}}\n            QPushButton:hover{{background-color:#d68910;}}\n            QPushButton:disabled{{background-color:{_Cores.BORDER};}}\n        ')
        self.btn_write.setEnabled(False)
        self.btn_write.clicked.connect(self._write)
        ops.addWidget(self.btn_write)
        self.btn_program = QPushButton('Zerar')
        self.btn_program.setMinimumSize(70, 32)
        self.btn_program.setMaximumHeight(32)
        self.btn_program.setCursor(Qt.PointingHandCursor)
        self.btn_program.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self.btn_program.setToolTip('Grava zeros na parti├º├úo (program/patch).\nFunciona em Samsung e Oppo onde Apagar ├® bloqueado.')
        self.btn_program.setStyleSheet(f'\n            QPushButton{{background-color:#e67e22;color:{_Cores.WHITE};\n                border:none;border-radius:5px;}}\n            QPushButton:hover{{background-color:#d68910;}}\n            QPushButton:disabled{{background-color:{_Cores.BORDER};}}\n        ')
        self.btn_program.setEnabled(False)
        self.btn_program.clicked.connect(self._program)
        ops.addWidget(self.btn_program)
        self.btn_erase = QPushButton('Apagar')
        self.btn_erase.setMinimumSize(70, 32)
        self.btn_erase.setMaximumHeight(32)
        self.btn_erase.setCursor(Qt.PointingHandCursor)
        self.btn_erase.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self.btn_erase.setStyleSheet(f'\n            QPushButton{{background-color:{_Cores.ERROR};color:{_Cores.WHITE};\n                border:none;border-radius:5px;}}\n            QPushButton:hover{{background-color:#c0392b;}}\n            QPushButton:disabled{{background-color:{_Cores.BORDER};}}\n        ')
        self.btn_erase.setEnabled(False)
        self.btn_erase.clicked.connect(self._erase)
        ops.addWidget(self.btn_erase)
        self.btn_reset = QPushButton('Reiniciar')
        self.btn_reset.setMinimumSize(70, 32)
        self.btn_reset.setMaximumHeight(32)
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.setFont(QFont('Segoe UI', 10))
        self.btn_reset.setStyleSheet(f'\n            QPushButton{{background-color:{_Cores.BG_DARK};color:{_Cores.TEXT};\n                border:1px solid {_Cores.BORDER};border-radius:5px;}}\n            QPushButton:hover{{background-color:{_Cores.BORDER};}}\n            QPushButton:disabled{{background-color:{_Cores.BG};border-color:{_Cores.BG};}}\n        ')
        self.btn_reset.setEnabled(False)
        self.btn_reset.clicked.connect(self._reset_dev)
        ops.addWidget(self.btn_reset)
        self.btn_parar = QPushButton('Parar')
        self.btn_parar.setMinimumSize(60, 32)
        self.btn_parar.setMaximumHeight(32)
        self.btn_parar.setCursor(Qt.PointingHandCursor)
        self.btn_parar.setFont(QFont('Segoe UI', 10))
        self.btn_parar.setStyleSheet(f'\n            QPushButton{{background-color:{_Cores.BG_DARK};color:{_Cores.ERROR};\n                border:1px solid {_Cores.ERROR};border-radius:5px;}}\n            QPushButton:hover{{background-color:{_Cores.ERROR};color:{_Cores.WHITE};}}\n            QPushButton:disabled{{background-color:{_Cores.BG};\n                border-color:{_Cores.BG};color:{_Cores.BORDER};}}\n        ')
        self.btn_parar.setEnabled(False)
        self.btn_parar.clicked.connect(self._parar_operacao)
        ops.addWidget(self.btn_parar)
        ops.addStretch()
        ll.addLayout(ops)
        bottom = QHBoxLayout()
        bottom.setSpacing(6)
        bottom.setContentsMargins(0, 0, 0, 0)
        self.barra = QProgressBar()
        self.barra.setFixedHeight(6)
        self.barra.setMinimumWidth(120)
        self.barra.setMaximumWidth(220)
        self.barra.setValue(0)
        self.barra.setTextVisible(False)
        self.barra.setStyleSheet(f'\n            QProgressBar{{border:1px solid {_Cores.BORDER};border-radius:3px;\n                background-color:{_Cores.BG_WHITE};}}\n            QProgressBar::chunk{{background-color:{_Cores.PRIMARY};border-radius:2px;}}\n        ')
        bottom.addWidget(self.barra)
        self.lbl_status = QLabel('Pronto')
        self.lbl_status.setFont(QFont('Segoe UI', 9))
        self.lbl_status.setStyleSheet(f'color:{_Cores.MUTED};')
        self.lbl_status.setWordWrap(True)
        bottom.addWidget(self.lbl_status, stretch=1)
        ll.addLayout(bottom)
        scroll.setWidget(left)
        main.addWidget(scroll, stretch=3)
        right = QWidget()
        right.setMinimumWidth(100)
        right.setMaximumWidth(180)
        right.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        rl = QVBoxLayout(right)
        rl.setAlignment(Qt.AlignCenter)
        self.phone_container = QFrame()
        self.phone_container.setMinimumSize(100, 100)
        self.phone_container.setMaximumSize(150, 150)
        self.phone_container.setStyleSheet(f'background-color:{_Cores.BG_DARK};border-radius:75px;border:2px solid {_Cores.BORDER};')
        fl = QVBoxLayout(self.phone_container)
        fl.setAlignment(Qt.AlignCenter)
        self.phone_image = QLabel()
        self.phone_image.setMinimumSize(50, 50)
        self.phone_image.setMaximumSize(80, 80)
        self.phone_image.setAlignment(Qt.AlignCenter)
        fl.addWidget(self.phone_image)
        rl.addWidget(self.phone_container)
        self.lbl_phone = QLabel('')
        self.lbl_phone.setAlignment(Qt.AlignCenter)
        self.lbl_phone.setFont(QFont('Segoe UI', 9))
        self.lbl_phone.setStyleSheet(f'color:{_Cores.MUTED};margin-top:8px;')
        rl.addWidget(self.lbl_phone)
        main.addWidget(right)
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
        r = 75
        estilos = {'notfound': f'background-color:{_Cores.BG_DARK};border-radius:{r}px;border:2px solid {_Cores.BORDER};', 'loading': f'background-color:{_Cores.BG_DARK};border-radius:{r}px;border:2px solid {_Cores.PRIMARY};', 'connected': f'background-color:{_Cores.BG_DARK};border-radius:{r}px;border:2px solid {_Cores.PRIMARY};', 'success': f'background-color:{_Cores.SUCCESS};border-radius:{r}px;border:2px solid {_Cores.SUCCESS};', 'error': f'background-color:{_Cores.ERROR};border-radius:{r}px;border:2px solid {_Cores.ERROR};'}
        self.phone_container.setStyleSheet(estilos.get(status, estilos['notfound']))
        path = img_path(imgs.get(status, 'phone_notfound.png'))
        if os.path.exists(path):
            pix = QPixmap(path).scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.phone_image.setPixmap(pix)
            if status == 'loading':
                self._original_pix = pix
                return
            return
        self.phone_image.setText('­ƒô▒')
        self.phone_image.setStyleSheet(f'font-size:32px;color:{_Cores.TEXT};')
    def _rotate_phone(self, angle):
        if self._original_pix:
            rot = self._original_pix.transformed(QTransform().rotate(angle), Qt.SmoothTransformation)
            dx = (rot.width() - self._original_pix.width()) // 2
            dy = (rot.height() - self._original_pix.height()) // 2
            self.phone_image.setPixmap(rot.copy(dx, dy, self._original_pix.width(), self._original_pix.height()))
    def _combo_css(self):
        svg = SVG_SETA_DOWN.replace('\\', '/')
        return f'\n            QComboBox{{background-color:{_Cores.BG_WHITE};color:{_Cores.TEXT};\n                border:1px solid {_Cores.BORDER};border-radius:4px;\n                padding:2px 24px 2px 6px;}}\n            QComboBox:hover{{border-color:{_Cores.PRIMARY};}}\n            QComboBox::drop-down{{\n                subcontrol-origin:padding;subcontrol-position:top right;\n                width:22px;border-left:1px solid {_Cores.BORDER};\n                border-top-right-radius:4px;border-bottom-right-radius:4px;\n                background-color:#ecf0f1;}}\n            QComboBox::drop-down:hover{{background-color:#d5dbdb;}}\n            QComboBox::down-arrow{{\n                image:url({svg});width:10px;height:10px;}}\n            QComboBox QAbstractItemView{{background-color:{_Cores.BG_WHITE};color:{_Cores.TEXT};\n                border:1px solid {_Cores.BORDER};selection-background-color:{_Cores.PRIMARY};\n                selection-color:{_Cores.WHITE};outline:none;}}\n        '
    def _on_storage_changed(self, _):
        tipo = self.combo_storage.currentData() or STORAGE_EMMC
        self._storage_type = tipo
        self._sector_size = STORAGE_INFO[tipo]['sector_size']
        is_ufs = tipo == STORAGE_UFS
        self.lbl_lun.setVisible(is_ufs)
        self.combo_lun.setVisible(is_ufs)
        if is_ufs:
            self.combo_lun.blockSignals(True)
            self.combo_lun.clear()
            for l in STORAGE_INFO[tipo]['luns']:
                self.combo_lun.addItem(str(l), l)
            self.combo_lun.setCurrentIndex(0)
            self.combo_lun.blockSignals(False)
        self._current_lun = 0
    @pyqtSlot(str, str)
    def set_loader(self, loader_path: str, memoria: str='emmc', requer_auth: str=None):
        self._loader_path = loader_path
        if requer_auth is not None:
            self._requer_auth = requer_auth
        if memoria == 'ufs':
            self.combo_storage.setCurrentIndex(1)
        else:
            self.combo_storage.setCurrentIndex(0)
        self.btn_ler.setEnabled(True)
        self.lbl_status.setText('Pronto ÔÇö detectando dispositivo...')
        self.lbl_status.setStyleSheet(f'color:{_Cores.MUTED};')
        auto = getattr(self, '_auto_start_leitura', False)
        self._detect_port(auto_start=auto)
    @pyqtSlot(str, str, bool)
    def set_loader_skip_sahara(self, loader_path: str, memoria: str='emmc', skip: bool=False, requer_auth: str=None):
        self._skip_sahara = skip
        self._auto_start_leitura = True
        self.set_loader(loader_path, memoria, requer_auth=requer_auth)
    def _detect_port(self, auto_start: bool=False):
        self._auto_start_leitura = auto_start
        self._set_phone('loading')
        self._anim.start()
        w = _DetectPortWorker()
        w.finished.connect(self._on_port)
        w.start()
        self._detect_w = w
    def _on_port(self, porta):
        self._anim.stop()
        if porta:
            self._com_port = porta
            if getattr(self, '_auto_start_leitura', False):
                self._auto_start_leitura = False
                self.lbl_status.setText(f'Porta: {porta} ÔÇö Lendo particoes...')
                self.lbl_status.setStyleSheet(f'color:{_Cores.SUCCESS};font-weight:bold;')
                self.lbl_phone.setText(f'Conectado ({porta})')
                self._set_phone('connected')
                self._ler_particoes()
                return
            self.lbl_status.setText(f'Porta: {porta} ÔÇö Clique em Ler Particoes')
            self.lbl_status.setStyleSheet(f'color:{_Cores.SUCCESS};font-weight:bold;')
            self.lbl_phone.setText(f'Conectado ({porta})')
            self._set_phone('connected')
            return
        self.lbl_status.setText('Sem dispositivo ÔÇö conecte em modo EDL')
        self.lbl_status.setStyleSheet(f'color:{_Cores.WARNING};')
        self.lbl_phone.setText('Aguardando')
        self._set_phone('notfound')
    def _ler_particoes(self):
        if self._em_operacao:
            return
        if not self._loader_path:
            QMessageBox.warning(self, 'Sem selecao', 'Selecione um modelo ou arquivo primeiro.')
            return
        if not self._com_port:
            p = fhops.detectar_porta_com()
            if p:
                self._com_port = p
            else:
                QMessageBox.warning(self, 'Sem dispositivo', 'Nenhum dispositivo detectado.\nConecte o aparelho em modo EDL e tente novamente.')
                return
        lun = self.combo_lun.currentData() if self._storage_type == STORAGE_UFS else 0
        if lun is None:
            lun = 0
        self._current_lun = lun
        mem = STORAGE_INFO[self._storage_type]['memory_arg']
        self._em_operacao = True
        self._set_btns(False)
        self.barra.setValue(0)
        self.table.setRowCount(0)
        self.table.setVisible(False)
        self._info_frame.setVisible(False)
        self.lbl_status.setText('Detectando armazenamento e lendo particoes...')
        self.lbl_status.setStyleSheet(f'color:{_Cores.WARNING};')
        self.lbl_phone.setText('Conectando...')
        self._set_phone('loading')
        self._anim.start()
        auth_efetivo = resolver_auth_type(self._requer_auth, self._auth_selector)
        self._gpt_worker = _LoadGptWorker(self._com_port, self._loader_path, mem, lun, skip_sahara=self._skip_sahara, auto_detect=True, requer_auth=auth_efetivo, vip_auth_id=getattr(self, '_vip_auth_id', None))
        self._gpt_worker.log_signal.connect((lambda m: _log(m)))
        self._gpt_worker.progress_signal.connect(self.barra.setValue)
        self._gpt_worker.finished.connect(self._on_gpt)
        self._gpt_worker.start()
    def _on_gpt(self, ok, data, erro):
        self._em_operacao = False
        self._skip_sahara = False
        self._anim.stop()
        if self._gpt_worker and hasattr(self._gpt_worker, '_vip2_ser'):
            ser = self._gpt_worker._vip2_ser
            if ser and ser.is_open:
                if self._vip2_ser and self._vip2_ser.is_open:
                    try:
                        self._vip2_ser.close()
                    except Exception:
                        pass
                self._vip2_ser = ser
        if not ok:
            _log(f'Falha GPT: {erro}')
            self.lbl_status.setText('Falha ao ler particoes')
            self.lbl_status.setStyleSheet(f'color:{_Cores.ERROR};')
            self._set_phone('error')
            self.lbl_phone.setText('Erro')
            self._set_btns(True)
            self.barra.setValue(0)
            QMessageBox.critical(self, 'Erro', 'N├úo foi poss├¡vel ler as parti├º├Áes.\n\nReconecte o dispositivo em modo EDL e tente novamente.\nSe o problema persistir, o dispositivo pode n├úo suportar esta opera├º├úo.')
            return
        self._gpt_data = data
        parts = data.get('partitions', [])
        is_ufs = data.get('is_ufs', False)
        sector = data.get('sector_size', self._sector_size)
        if sector != self._sector_size:
            self._sector_size = sector
        if is_ufs:
            self._storage_type = STORAGE_UFS
            self.combo_storage.blockSignals(True)
            self.combo_storage.setCurrentIndex(1)
            self.combo_storage.blockSignals(False)
            tipo_label = 'UFS'
            num_luns = data.get('num_luns', 6)
            lun_txt = f' | {num_luns} LUNs'
        else:
            tipo_label = STORAGE_INFO.get(self._storage_type, STORAGE_INFO[STORAGE_EMMC])['label']
            lun_txt = f' | LUN {self._current_lun}' if self._storage_type == STORAGE_UFS else ''
        self._info_frame.setVisible(True)
        self._lbl_storage.setText(f'Tipo: {tipo_label}{lun_txt} | Setor: {self._sector_size} bytes | Porta: {self._com_port}')
        self._lbl_pcount.setText(f'{len(parts)} particoes')
        self._fill_table(parts)
        self.table.setVisible(True)
        has_parts = len(parts) > 0
        self.btn_sel_all.setVisible(has_parts)
        self.btn_unsel_all.setVisible(has_parts)
        self.lbl_sel_count.setVisible(has_parts)
        self._update_sel_count()
        self._set_btns(True)
        self.btn_backup.setEnabled(has_parts)
        self.btn_write.setEnabled(has_parts)
        self.btn_program.setEnabled(has_parts)
        self.btn_erase.setEnabled(has_parts)
        self.btn_reset.setEnabled(True)
        self.lbl_status.setText(f'{len(parts)} particoes ÔÇö {tipo_label}{lun_txt}')
        self.lbl_status.setStyleSheet(f'color:{_Cores.SUCCESS};font-weight:bold;')
        self.lbl_phone.setText('Particoes carregadas')
        self._set_phone('connected')
    def _fill_table(self, parts):
        self.table.setRowCount(len(parts))
        sc = {'safe': _Cores.SUCCESS, 'caution': _Cores.WARNING, 'critical': _Cores.ERROR, 'unknown': _Cores.TEXT}
        sl = {'safe': 'Seguro', 'caution': 'Cuidado', 'critical': 'CRITICO', 'unknown': '--'}
        for row, p in enumerate(parts):
            s = p.get('safety', 'unknown')
            cb = QTableWidgetItem()
            cb.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            cb.setCheckState(Qt.Unchecked)
            self.table.setItem(row, 0, cb)
            ni = QTableWidgetItem(p['name'])
            ni.setFont(QFont('Consolas', 10))
            if s == 'critical':
                ni.setForeground(QBrush(QColor(_Cores.ERROR)))
            self.table.setItem(row, 1, ni)
            li = QTableWidgetItem(str(p.get('lun', 0)))
            li.setTextAlignment(Qt.AlignCenter)
            li.setFont(QFont('Consolas', 9))
            self.table.setItem(row, 2, li)
            si = QTableWidgetItem(str(p['start_lba']))
            si.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, si)
            ci = QTableWidgetItem(str(p['num_sectors']))
            ci.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 4, ci)
            zi = QTableWidgetItem(p.get('size_human', ''))
            zi.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 5, zi)
            ti = QTableWidgetItem(sl.get(s, '--'))
            ti.setTextAlignment(Qt.AlignCenter)
            ti.setForeground(QBrush(QColor(sc.get(s, _Cores.TEXT))))
            ti.setFont(QFont('Segoe UI', 9, QFont.Bold))
            self.table.setItem(row, 6, ti)
            continue
    def _select_all(self):
        self.table.blockSignals(True)
        for i in range(self.table.rowCount()):
            cb = self.table.item(i, 0)
            if cb:
                cb.setCheckState(Qt.Checked)
        self.table.blockSignals(False)
        self._update_sel_count()
    def _unselect_all(self):
        self.table.blockSignals(True)
        for i in range(self.table.rowCount()):
            cb = self.table.item(i, 0)
            if cb:
                cb.setCheckState(Qt.Unchecked)
        self.table.blockSignals(False)
        self._update_sel_count()
    def _on_check_changed(self, item):
        if item.column() == 0:
            self._update_sel_count()
    def _update_sel_count(self):
        total = 0
        for i in range(self.table.rowCount()):
            cb = self.table.item(i, 0)
            if not cb:
                continue
            if cb.checkState() == Qt.Checked:
                total += 1
        rows = self.table.rowCount()
        if rows > 0:
            self.lbl_sel_count.setText(f'{total} de {rows} selecionada(s)')
            self.lbl_sel_count.setVisible(True)
            return
        self.lbl_sel_count.setVisible(False)
    def _get_sel(self):
        pts = self._gpt_data.get('partitions', [])
        for i in range(self.table.rowCount()):
            cb = self.table.item(i, 0)
            if not cb:
                continue
            if cb.checkState() != Qt.Checked:
                continue
            if i < len(pts):
                return pts[i]
        r = self.table.currentRow()
        if r >= 0 and r < len(pts):
            return pts[r]
    def _get_checked(self):
        pts = self._gpt_data.get('partitions', [])
        checked = []
        for i in range(self.table.rowCount()):
            cb = self.table.item(i, 0)
            if not cb:
                continue
            if cb.checkState() != Qt.Checked:
                continue
            if i < len(pts):
                checked.append(pts[i])
        return checked
    def _backup(self):
        if self._em_operacao:
            return
        checked = self._get_checked()
        if len(checked) > 1:
            self._backup_multi(checked)
            return
        p = self._get_sel()
        if not p:
            QMessageBox.information(self, 'Selecione', 'Selecione uma particao na tabela para fazer backup.')
            return
        docs = str(Path.home() / 'Documents')
        sp, _ = QFileDialog.getSaveFileName(self, f'Salvar Backup ÔÇö {p['name']}', os.path.join(docs, f'{p['name']}_backup.bin'), 'Binarios (*.bin);;Todos (*.*)')
        if sp:
            self._run_op('read', p, file_path=sp, msg=f'Fazendo backup de {p['name']}...')
    def _backup_multi(self, partitions):
        nomes = ', '.join((p['name'] for p in partitions))
        r = QMessageBox.question(self, 'Backup Multiplo', f'Fazer backup de {len(partitions)} particoes?\n\n{nomes}', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if r != QMessageBox.Yes:
            return
        folder = QFileDialog.getExistingDirectory(self, 'Pasta para salvar os backups', str(Path.home() / 'Documents'))
        if not folder:
            return
        self._multi_queue = []
        for p in partitions:
            fp = os.path.join(folder, f'{p['name']}_backup.bin')
            self._multi_queue.append((p, fp))
        self._multi_total = len(self._multi_queue)
        self._multi_done = 0
        self._multi_op_type = 'read'
        self._run_next_multi()
    def _run_next_multi(self):
        if not self._multi_queue:
            return
        item = self._multi_queue.pop(0)
        idx = self._multi_done + 1
        op = self._multi_op_type
        if op == 'read':
            part, fp = item
            self._run_op('read', part, file_path=fp, msg=f'Backup {idx}/{self._multi_total}: {part['name']}...')
            return
        if op == 'erase':
            part = item
            self._run_op('erase', part, msg=f'Apagando {idx}/{self._multi_total}: {part['name']}...')
    def _write(self):
        if self._em_operacao:
            return
        p = self._get_sel()
        if not p:
            QMessageBox.information(self, 'Selecione', 'Selecione uma particao na tabela para gravar.')
            return
        name = p['name']
        if is_critical(name):
            QMessageBox.critical(self, 'BLOQUEADO', f'A particao "{name}" e CRITICA.\nGravar nela pode causar BRICK PERMANENTE.\nOperacao bloqueada por seguranca.')
            return
        docs = str(Path.home() / 'Documents')
        fp, _ = QFileDialog.getOpenFileName(self, f'Selecionar Imagem ÔÇö {name}', docs, 'Binarios (*.bin *.img *.mbn);;Todos (*.*)')
        if not fp:
            return
        file_size = os.path.getsize(fp)
        part_size = p.get('num_sectors', 0) * self._sector_size
        if part_size > 0 and file_size > part_size:
            QMessageBox.warning(self, 'Arquivo muito grande', f'O arquivo ({file_size:,} bytes) e maior que a particao ({part_size:,} bytes).\n\nOperacao cancelada.')
            return
        s = p.get('safety', 'unknown')
        if s == 'caution':
            r = QMessageBox.warning(self, 'ATENCAO', f'Gravar em "{name}" pode afetar dados importantes!\n\nArquivo: {os.path.basename(fp)}\nTamanho: {file_size:,} bytes\nParticao: {p.get('size_human', '?')}\n\nTem certeza que deseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if r != QMessageBox.Yes:
                return
            r2 = QMessageBox.question(self, 'Confirmacao Final', f'ULTIMA CHANCE: gravar em "{name}"?\nNAO pode ser desfeito.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if r2 != QMessageBox.Yes:
                return
        else:
            r = QMessageBox.question(self, f'Gravar ÔÇö {name}', f'Particao: {name}\nArquivo: {os.path.basename(fp)}\nTamanho: {file_size:,} bytes\n\nContinuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if r != QMessageBox.Yes:
                return
        self._run_op('write', p, file_path=fp, msg=f'Gravando {name}...')
    def _program(self):
        if self._em_operacao:
            return
        p = self._get_sel()
        if not p:
            QMessageBox.information(self, 'Selecione', 'Selecione uma particao na tabela para zerar.')
            return
        name = p['name']
        if is_critical(name):
            QMessageBox.critical(self, 'BLOQUEADO', f'A particao "{name}" e CRITICA.\nOperacao bloqueada por seguranca.')
            return
        r = QMessageBox.question(self, f'Zerar ÔÇö {name}', f'Particao: {name}\nTamanho: {p.get('size_human', '?')}\n\nGravar zeros na particao?\n(Funciona onde Apagar e bloqueado)', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if r != QMessageBox.Yes:
            return
        self._run_op('program', p, msg=f'Zerando {name}...')
    def _erase(self):
        if self._em_operacao:
            return
        checked = self._get_checked()
        if len(checked) > 1:
            self._erase_multi(checked)
            return
        p = self._get_sel()
        if not p:
            QMessageBox.information(self, 'Selecione', 'Selecione uma particao na tabela para apagar.')
            return
        name = p['name']
        if is_critical(name):
            QMessageBox.critical(self, 'BLOQUEADO', f'A particao "{name}" e CRITICA.\nApagar causa BRICK PERMANENTE.\nOperacao bloqueada por seguranca.')
            return
        s = p.get('safety', 'unknown')
        if s == 'caution':
            r = QMessageBox.warning(self, 'ATENCAO', f'"{name}" contem dados importantes!\n\nSetores: {p['start_lba']} ÔÇô {p['start_lba'] + p['num_sectors'] - 1}\nTamanho: {p.get('size_human', '?')}\n\nRECOMENDADO: Faca backup antes.\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if r != QMessageBox.Yes:
                return
            r2 = QMessageBox.question(self, 'Confirmacao Final', f'CERTEZA que deseja apagar "{name}"?\nNAO pode ser desfeito.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if r2 != QMessageBox.Yes:
                return
        else:
            r = QMessageBox.question(self, f'Apagar ÔÇö {name}', f'Particao: {name}\nTamanho: {p.get('size_human', '?')}\n\nContinuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if r != QMessageBox.Yes:
                return
        self._run_op('erase', p, msg=f'Apagando {name}...')
    def _erase_multi(self, partitions):
        seguras = []
        bloqueadas = []
        for p in partitions:
            if is_critical(p['name']):
                bloqueadas.append(p['name'])
            else:
                seguras.append(p)
        if bloqueadas:
            QMessageBox.warning(self, 'Particoes bloqueadas', f'As seguintes particoes sao criticas e foram IGNORADAS:\n\n{', '.join(bloqueadas)}\n\nApaga-las causa BRICK PERMANENTE.')
        if not seguras:
            return
        nomes = ', '.join((p['name'] for p in seguras))
        r = QMessageBox.warning(self, 'Apagar Multiplas Particoes', f'Deseja apagar {len(seguras)} particoes?\n\n{nomes}\n\nATENCAO: Esta operacao NAO pode ser desfeita!', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if r != QMessageBox.Yes:
            return
        r2 = QMessageBox.question(self, 'Confirmacao Final', f'CERTEZA que deseja apagar {len(seguras)} particoes?\nNAO pode ser desfeito.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if r2 != QMessageBox.Yes:
            return
        self._multi_queue = list(seguras)
        self._multi_total = len(seguras)
        self._multi_done = 0
        self._multi_op_type = 'erase'
        self._run_next_multi()
    def _reset_dev(self):
        if self._em_operacao or not self._com_port:
            return
        r = QMessageBox.question(self, 'Reiniciar', 'Reiniciar o dispositivo?\nO aparelho saira do modo EDL.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if r != QMessageBox.Yes:
            return
        self._em_operacao = True
        self._set_btns(False)
        self.lbl_status.setText('Reiniciando...')
        self.lbl_status.setStyleSheet(f'color:{_Cores.WARNING};')
        self._set_phone('loading')
        self._anim.start()
        _auth = resolver_auth_type(self._requer_auth, self._auth_selector)
        if is_oppo_vip2(_auth):
            ok = self._reset_dev_vip2()
        else:
            mem = STORAGE_INFO[self._storage_type]['memory_arg']
            ok, _ = fhops.reset_device(self._com_port, mem, log_cb=(lambda m: _log(m)))
        self._em_operacao = False
        self._anim.stop()
        self._set_btns(True)
        if ok:
            self.lbl_status.setText('Dispositivo reiniciado')
            self.lbl_status.setStyleSheet(f'color:{_Cores.SUCCESS};font-weight:bold;')
            self._set_phone('success')
            self.lbl_phone.setText('Reiniciado')
            return
        self.lbl_status.setText('Falha no reinicio')
        self.lbl_status.setStyleSheet(f'color:{_Cores.ERROR};')
        self._set_phone('error')
    def _reset_dev_vip2(self) -> bool:
        try:
            from app.views.union_unlock.edl._qcom_io import _XML_H
        except ImportError:
            _XML_H = b'<?xml version="1.0" encoding="UTF-8" ?>'
        ser = self._vip2_ser
        if not ser or not ser.is_open:
            _log('Sessao serial nao disponivel para reinicio.')
            return False
        reboot_xml = _XML_H + b'<data><power value="reset"/></data>'
        try:
            ser.write(reboot_xml)
            ser.flush()
        except (Exception,):
            _log('Dispositivo reiniciando...')
            self._vip2_ser = None
            return True
        import time
        time.sleep(1.0)
        _log('Dispositivo reiniciando...')
        try:
            ser.close()
        except Exception:
            pass
        self._vip2_ser = None
        return True
    def _run_op(self, op, part, file_path='', msg=''):
        self._em_operacao = True
        self._set_btns(False)
        self.barra.setValue(5)
        self.lbl_status.setText(msg)
        self.lbl_status.setStyleSheet(f'color:{_Cores.WARNING};')
        self._set_phone('loading')
        self._anim.start()
        self.lbl_phone.setText('Processando...')
        mem = self._gpt_data.get('memory', STORAGE_INFO[self._storage_type]['memory_arg'])
        part_lun = part.get('lun', self._current_lun)
        _auth = resolver_auth_type(self._requer_auth, self._auth_selector)
        self._op_worker = _OperationWorker(op, self._com_port, mem, part, self._sector_size, part_lun, file_path, requer_auth=_auth, loader_path=self._loader_path, vip_auth_id=self._vip_auth_id, vip2_ser=self._vip2_ser if is_oppo_vip2(_auth) else None)
        self._op_worker.log_signal.connect((lambda m: _log(m)))
        self._op_worker.progress_signal.connect(self.barra.setValue)
        self._op_worker.status_signal.connect(self._on_op_st)
        self._op_worker.finished_signal.connect(self._on_op_done)
        self._op_worker.start()
    def _on_op_st(self, st):
        if st == 'success':
            self._anim.stop()
            self._set_phone('success')
            self.lbl_phone.setText('Concluido')
            return
        if st == 'error':
            self._anim.stop()
            self._set_phone('error')
            self.lbl_phone.setText('Erro')
    def _on_op_done(self, ok, msg):
        if self._op_worker and hasattr(self._op_worker, '_vip2_ser'):
            ser = self._op_worker._vip2_ser
            if ser and ser.is_open:
                self._vip2_ser = ser
        if hasattr(self, '_multi_queue') and self._multi_queue is not None:
            self._multi_done += 1
            op_label = 'Backup' if self._multi_op_type == 'read' else 'Erase'
            if ok:
                _log(f'Multi-{op_label} {self._multi_done}/{self._multi_total} OK')
            else:
                _log(f'Multi-{op_label} {self._multi_done}/{self._multi_total} FALHA: {msg}')
            if self._multi_queue:
                self._run_next_multi()
                return
            self._em_operacao = False
            self._anim.stop()
            self._set_btns(True)
            if self.table.rowCount() > 0:
                self.btn_backup.setEnabled(True)
                self.btn_write.setEnabled(True)
                self.btn_program.setEnabled(True)
                self.btn_erase.setEnabled(True)
            self.btn_reset.setEnabled(True)
            self.barra.setValue(100)
            if self._multi_op_type == 'read':
                resumo = f'Backup concluido ÔÇö {self._multi_done} particoes'
                titulo = 'Backup Multiplo'
            else:
                resumo = f'Limpeza concluida ÔÇö {self._multi_done} particoes'
                titulo = 'Limpeza Multipla'
            self.lbl_status.setText(resumo)
            self.lbl_status.setStyleSheet(f'color:{_Cores.SUCCESS};font-weight:bold;')
            self._set_phone('success')
            self.lbl_phone.setText('Concluido')
            QMessageBox.information(self, titulo, f'{resumo}!')
            self._multi_queue = None
            return
        self._em_operacao = False
        self._anim.stop()
        self._set_btns(True)
        if self.table.rowCount() > 0:
            self.btn_backup.setEnabled(True)
            self.btn_write.setEnabled(True)
            self.btn_program.setEnabled(True)
            self.btn_erase.setEnabled(True)
        self.btn_reset.setEnabled(True)
        if ok:
            self.barra.setValue(100)
            self.lbl_status.setText('Operacao concluida!')
            self.lbl_status.setStyleSheet(f'color:{_Cores.SUCCESS};font-weight:bold;')
            QMessageBox.information(self, 'Sucesso', 'Operacao concluida com sucesso!')
            return
        _log(f'Falha operacao: {msg}')
        self.barra.setValue(0)
        self.lbl_status.setText('Falha na operacao')
        self.lbl_status.setStyleSheet(f'color:{_Cores.ERROR};')
        if 'firmware' in msg.lower() or 'nao permitida' in msg.lower():
            QMessageBox.warning(self, 'Operacao nao permitida', 'O dispositivo bloqueou esta operacao.\n\nO firmware protege esta particao contra escrita direta.\nLeitura (backup) continua disponivel.')
            return
        QMessageBox.warning(self, 'Operacao falhou', 'Nao foi possivel concluir a operacao.\n\nTente novamente. Se necessario, ponha o\ndispositivo em modo EDL novamente.')
    def _set_btns(self, en):
        self.btn_ler.setEnabled(en and bool(self._loader_path))
        self.btn_backup.setEnabled(False)
        self.btn_write.setEnabled(False)
        self.btn_program.setEnabled(False)
        self.btn_erase.setEnabled(False)
        self.btn_reset.setEnabled(False)
        self.btn_parar.setEnabled(not en and self._em_operacao)
        self.combo_storage.setEnabled(en)
        self.combo_lun.setEnabled(en)
    def _parar_operacao(self):
        try:
            _matar_processos_edl()
            if self._gpt_worker and self._gpt_worker.isRunning():
                self._gpt_worker.terminate()
                if not self._gpt_worker.wait(2000):
                    _log('GPT worker nao respondeu ao terminate')
            if self._op_worker and self._op_worker.isRunning():
                self._op_worker.terminate()
                if not self._op_worker.wait(2000):
                    _log('OP worker nao respondeu ao terminate')
        except Exception:
            _log('Erro ao parar operacao')
        else:
            self._em_operacao = False
            self._anim.stop()
            self._set_phone('notfound')
            self.barra.setValue(0)
            self.btn_parar.setEnabled(False)
            self._set_btns(True)
            if self.table.rowCount() > 0:
                self.btn_backup.setEnabled(True)
                self.btn_write.setEnabled(True)
                self.btn_program.setEnabled(True)
                self.btn_erase.setEnabled(True)
                self.btn_reset.setEnabled(True)
            self.lbl_status.setText('Operacao cancelada')
            self.lbl_status.setStyleSheet(f'color:{_Cores.MUTED};')
            self.lbl_phone.setText('')
            _log('Operacao cancelada pelo usuario')
        finally:
            self._em_operacao = False
            self._anim.stop()
            self._set_phone('notfound')
            self.barra.setValue(0)
            self.btn_parar.setEnabled(False)
            self._set_btns(True)
            if self.table.rowCount() > 0:
                self.btn_backup.setEnabled(True)
                self.btn_write.setEnabled(True)
                self.btn_program.setEnabled(True)
                self.btn_erase.setEnabled(True)
                self.btn_reset.setEnabled(True)
            self.lbl_status.setText('Operacao cancelada')
            self.lbl_status.setStyleSheet(f'color:{_Cores.MUTED};')
            self.lbl_phone.setText('')
            _log('Operacao cancelada pelo usuario')
class _ModeMarcaModelo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._carregado = False
        self._setup_ui()
    def _setup_ui(self):
        self.setStyleSheet(f'background-color:{_Cores.BG};')
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        left = QFrame()
        left.setMinimumWidth(200)
        left.setMaximumWidth(280)
        left.setStyleSheet(f'background-color:{_Cores.BG_WHITE};border-right:1px solid {_Cores.BORDER};')
        ll = QVBoxLayout(left)
        ll.setContentsMargins(6, 6, 6, 6)
        ll.setSpacing(4)
        lbl = QLabel('Marca / Modelo')
        lbl.setFont(QFont('Segoe UI', 12, QFont.Bold))
        lbl.setStyleSheet(f'color:{_Cores.PRIMARY};')
        ll.addWidget(lbl)
        self.combo_marca = QComboBox()
        self.combo_marca.setFont(QFont('Segoe UI', 10))
        self.combo_marca.setFixedHeight(30)
        self.combo_marca.setStyleSheet(self._combo_css())
        self._popular_marcas_combo()
        self.combo_marca.currentIndexChanged.connect(self._on_marca_changed)
        ll.addWidget(self.combo_marca)
        self.busca = QLineEdit()
        self.busca.setPlaceholderText('Buscar modelo...')
        self.busca.setFixedHeight(30)
        self.busca.setFont(QFont('Segoe UI', 10))
        self.busca.setStyleSheet(f'\n            QLineEdit{{background-color:{_Cores.BG};border:1px solid {_Cores.BORDER};\n                border-radius:15px;padding:0 12px;color:{_Cores.TEXT};}}\n            QLineEdit:focus{{border:2px solid {_Cores.PRIMARY};}}\n        ')
        self.busca.textChanged.connect(self._filtrar)
        ll.addWidget(self.busca)
        self.lista = QListWidget()
        self.lista.setFont(QFont('Segoe UI', 10))
        self.lista.setStyleSheet(f'\n            QListWidget{{background-color:{_Cores.BG_WHITE};border:none;}}\n            QListWidget::item{{color:{_Cores.TEXT};padding:6px 8px;\n                border-radius:4px;margin:1px 0;}}\n            QListWidget::item:hover{{background-color:{_Cores.BG};}}\n            QListWidget::item:selected{{background-color:{_Cores.PRIMARY};\n                color:{_Cores.WHITE};}}\n        ')
        self.lista.currentItemChanged.connect(self._on_select)
        ll.addWidget(self.lista)
        lay.addWidget(left)
        self.ops_panel = _PartitionOpsPanel()
        lay.addWidget(self.ops_panel, stretch=1)
    def _popular_marcas_combo(self):
        try:
            try:
                from app.views.union_unlock.edl.edl_sync import get_sync
            except ImportError:
                from edl_sync import get_sync
        except Exception:
            marcas_db = []
        sync = get_sync()
        marcas_db = sync.listar_marcas_disponiveis()
        if marcas_db:
            for marca in marcas_db:
                self.combo_marca.addItem(marca)
            return
        for marca, _ in ALL_BRANDS:
            self.combo_marca.addItem(marca)
    def _combo_css(self):
        svg = SVG_SETA_DOWN.replace('\\', '/')
        return f'\n            QComboBox{{background-color:{_Cores.BG_WHITE};color:{_Cores.TEXT};\n                border:1px solid {_Cores.BORDER};border-radius:4px;\n                padding:2px 24px 2px 8px;}}\n            QComboBox:hover{{border-color:{_Cores.PRIMARY};}}\n            QComboBox::drop-down{{\n                subcontrol-origin:padding;subcontrol-position:top right;\n                width:22px;border-left:1px solid {_Cores.BORDER};\n                border-top-right-radius:4px;border-bottom-right-radius:4px;\n                background-color:#ecf0f1;}}\n            QComboBox::drop-down:hover{{background-color:#d5dbdb;}}\n            QComboBox::down-arrow{{\n                image:url({svg});width:10px;height:10px;}}\n            QComboBox QAbstractItemView{{background-color:{_Cores.BG_WHITE};\n                color:{_Cores.TEXT};border:1px solid {_Cores.BORDER};\n                selection-background-color:{_Cores.PRIMARY};\n                selection-color:{_Cores.WHITE};outline:none;}}\n        '
    def showEvent(self, ev):
        super().showEvent(ev)
        if not self._carregado:
            self._carregado = True
            self._carregar_modelos()
    def _carregar_modelos(self):
        marca = self.combo_marca.currentText()
        threading.Thread(target=self._load_thread, args=(marca,), daemon=True).start()
    def _load_thread(self, marca):
        try:
            try:
                from app.views.union_unlock.edl.edl_sync import get_sync
            except ImportError:
                from edl_sync import get_sync
        except Exception as e:
            _log(f'Erro ao carregar modelos {marca}: {e}')
        sync = get_sync()
        modelos = sync.listar_marca(marca)
        from PyQt5.QtCore import QMetaObject, Q_ARG
        QMetaObject.invokeMethod(self, '_popular', Qt.QueuedConnection, Q_ARG(list, modelos))
    @pyqtSlot(list)
    def _popular(self, modelos):
        self.lista.clear()
        self._modelos = modelos
        for m in modelos:
            item = QListWidgetItem(m['modelo'])
            item.setData(Qt.UserRole, m)
            self.lista.addItem(item)
        _log(f'{self.combo_marca.currentText()}: {len(modelos)} modelos')
    def _on_marca_changed(self, _):
        self._carregado = True
        self._carregar_modelos()
    def recarregar_marcas(self):
        try:
            try:
                from app.views.union_unlock.edl.edl_sync import get_sync
            except ImportError:
                from edl_sync import get_sync
        except Exception:
            return
        sync = get_sync()
        marcas_db = sync.listar_marcas_disponiveis()
        if not marcas_db:
            return
        marca_atual = self.combo_marca.currentText()
        self.combo_marca.blockSignals(True)
        self.combo_marca.clear()
        for marca in marcas_db:
            self.combo_marca.addItem(marca)
        idx = self.combo_marca.findText(marca_atual)
        if idx >= 0:
            self.combo_marca.setCurrentIndex(idx)
        self.combo_marca.blockSignals(False)
        _log(f'Partitions combo atualizado: {len(marcas_db)} marcas')
    def _filtrar(self, txt):
        txt = txt.lower()
        for i in range(self.lista.count()):
            it = self.lista.item(i)
            it.setHidden(txt not in it.text().lower())
    def _on_select(self, current, _):
        if not current:
            return
        m = current.data(Qt.UserRole)
        if not m:
            return
        srv_id = m.get('srv_id')
        memoria = m.get('memoria', 'emmc')
        requer_auth = m.get('requer_auth')
        vip_auth_id = m.get('vip_auth_id')
        _log(f'Modelo selecionado: {m['modelo']} (id={srv_id}, mem={memoria})')
        threading.Thread(target=self._download_loader, args=(srv_id, memoria, requer_auth, vip_auth_id), daemon=True).start()
    def _download_loader(self, srv_id, memoria, requer_auth=None, vip_auth_id=None):
        try:
            try:
                from app.views.union_unlock.edl.edl_sync import get_sync
            except ImportError:
                from edl_sync import get_sync
        except Exception as e:
            _log(f'Erro ao baixar dados do modelo: {e}')
        sync = get_sync()
        dados = sync.download_loader(srv_id)
        if not dados:
            _log(f'Dados nao disponiveis para id={srv_id}')
            return
        try:
            tmp_dir = Path(fhops._edl_tmp_base()) / 'part_loaders'
            tmp_dir.mkdir(exist_ok=True)
            dest = tmp_dir / f'.pl_{srv_id}.tmp'
            dest.write_bytes(dados)
            _log(f'Dados baixados: {dest} ({len(dados)} bytes)')
            self.ops_panel._requer_auth = requer_auth
            self.ops_panel._vip_auth_id = vip_auth_id
            from PyQt5.QtCore import QMetaObject, Q_ARG
            QMetaObject.invokeMethod(self.ops_panel, 'set_loader', Qt.QueuedConnection, Q_ARG(str, str(dest)), Q_ARG(str, memoria))
        except Exception as e:
            _log(f'Erro ao baixar dados do modelo: {e}')
class _ModeAutomatico(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._detected_info = None
        self._loader_path = None
        self._loader_matches = []
        self._requer_auth = None
        self._vip_auth_id = None
        self._etapa = 0
        self._setup_ui()
    def _setup_ui(self):
        self.setStyleSheet(f'background-color:{_Cores.BG};')
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(8)
        ctrl = QWidget()
        ctrl.setMinimumWidth(200)
        ctrl.setMaximumWidth(280)
        cl = QVBoxLayout(ctrl)
        cl.setContentsMargins(6, 6, 6, 6)
        cl.setSpacing(6)
        t = QLabel('Deteccao Automatica')
        t.setFont(QFont('Segoe UI', 14, QFont.Bold))
        t.setStyleSheet(f'color:{_Cores.PRIMARY};')
        cl.addWidget(t)
        s = QLabel('Detecta o dispositivo em EDL, identifica o chipset\ne busca a configuracao compativel automaticamente.')
        s.setFont(QFont('Segoe UI', 9))
        s.setStyleSheet(f'color:{_Cores.MUTED};')
        s.setWordWrap(True)
        cl.addWidget(s)
        cl.addSpacing(4)
        self.btn_detect = QPushButton('1. Detectar Dispositivo')
        self.btn_detect.setFixedHeight(38)
        self.btn_detect.setFont(QFont('Segoe UI', 11, QFont.Bold))
        self.btn_detect.setCursor(Qt.PointingHandCursor)
        self.btn_detect.setStyleSheet(f'\n            QPushButton{{background-color:{_Cores.PRIMARY};color:{_Cores.WHITE};\n                border:none;border-radius:6px;}}\n            QPushButton:hover{{background-color:{_Cores.PRI_HOV};}}\n            QPushButton:disabled{{background-color:{_Cores.BORDER};}}\n        ')
        self.btn_detect.clicked.connect(self._detectar)
        cl.addWidget(self.btn_detect)
        self.lbl_info = QLabel('Conecte um dispositivo em modo EDL')
        self.lbl_info.setFont(QFont('Segoe UI', 10))
        self.lbl_info.setStyleSheet(f'color:{_Cores.MUTED};')
        self.lbl_info.setWordWrap(True)
        cl.addWidget(self.lbl_info)
        cl.addSpacing(4)
        self.btn_reconectar = QPushButton('2. Reconectar e Carregar')
        self.btn_reconectar.setFixedHeight(38)
        self.btn_reconectar.setFont(QFont('Segoe UI', 11, QFont.Bold))
        self.btn_reconectar.setCursor(Qt.PointingHandCursor)
        self.btn_reconectar.setStyleSheet(f'\n            QPushButton{{background-color:{_Cores.SUCCESS};color:{_Cores.WHITE};\n                border:none;border-radius:6px;}}\n            QPushButton:hover{{background-color:#219a52;}}\n            QPushButton:disabled{{background-color:{_Cores.BORDER};}}\n        ')
        self.btn_reconectar.setEnabled(False)
        self.btn_reconectar.clicked.connect(self._reconectar)
        cl.addWidget(self.btn_reconectar)
        self.srv_frame = QFrame()
        self.srv_frame.setVisible(False)
        srv_lay = QVBoxLayout(self.srv_frame)
        srv_lay.setContentsMargins(0, 0, 0, 0)
        srv_lay.setSpacing(4)
        srv_lbl = QLabel('Servidor de origem:')
        srv_lbl.setFont(QFont('Segoe UI', 9))
        srv_lbl.setStyleSheet(f'color:{_Cores.MUTED};')
        srv_lay.addWidget(srv_lbl)
        self.combo_srv = QComboBox()
        self.combo_srv.setFixedHeight(32)
        self.combo_srv.setFont(QFont('Segoe UI', 10, QFont.Bold))
        _svg = SVG_SETA_DOWN.replace('\\', '/')
        self.combo_srv.setStyleSheet(f'\n            QComboBox{{background-color:{_Cores.BG_WHITE};color:{_Cores.PRIMARY};\n                border:1px solid {_Cores.BORDER};border-radius:6px;\n                padding:4px 24px 4px 8px;}}\n            QComboBox::drop-down{{\n                subcontrol-origin:padding;subcontrol-position:top right;\n                width:22px;border-left:1px solid {_Cores.BORDER};\n                border-top-right-radius:6px;border-bottom-right-radius:6px;\n                background-color:#ecf0f1;}}\n            QComboBox::drop-down:hover{{background-color:#d5dbdb;}}\n            QComboBox::down-arrow{{\n                image:url({_svg});width:10px;height:10px;}}\n            QComboBox QAbstractItemView{{background-color:{_Cores.BG_WHITE};\n                color:{_Cores.TEXT};selection-background-color:{_Cores.PRIMARY};\n                border:1px solid {_Cores.BORDER};}}\n        ')
        self.combo_srv.currentIndexChanged.connect(self._on_srv_changed)
        srv_lay.addWidget(self.combo_srv)
        cl.addWidget(self.srv_frame)
        self.lbl_etapa2 = QLabel('')
        self.lbl_etapa2.setFont(QFont('Segoe UI', 9))
        self.lbl_etapa2.setStyleSheet(f'color:{_Cores.MUTED};')
        self.lbl_etapa2.setWordWrap(True)
        cl.addWidget(self.lbl_etapa2)
        cl.addStretch()
        lay.addWidget(ctrl)
        self.ops_panel = _PartitionOpsPanel()
        lay.addWidget(self.ops_panel, stretch=1)
    def _detectar(self):
        self.btn_detect.setEnabled(False)
        self.btn_reconectar.setEnabled(False)
        self.srv_frame.setVisible(False)
        self.combo_srv.clear()
        self._loader_matches = []
        self.lbl_info.setText('Procurando dispositivo...')
        self.lbl_info.setStyleSheet(f'color:{_Cores.WARNING};')
        self.lbl_etapa2.setText('')
        threading.Thread(target=self._detect_thread, daemon=True).start()
    def _on_srv_changed(self, index):
        if index < 0 or index >= len(self._loader_matches):
            return
        match = self._loader_matches[index]
        self._loader_path = str(match['path'])
        _log(f'Loader alterado para {match['srv']} (id={match['id']})')
    def _detect_thread(self):
        try:
            porta = fhops.detectar_porta_com()
            if not porta:
                self._set_lbl(self.lbl_info, 'Dispositivo nao encontrado ÔÇö conecte em modo EDL', _Cores.ERROR)
                self._enable_btn(self.btn_detect, True)
                return
        except Exception as e:
            _log(f'Erro deteccao auto: {e}')
            self._set_lbl(self.lbl_info, 'Erro inesperado.\nReconecte o dispositivo e tente novamente.', _Cores.ERROR)
            self._enable_btn(self.btn_detect, True)
        try:
            try:
                from app.views.union_unlock.edl.auto import (_obter_info_dispositivo, _buscar_loaders_db, _obter_loader_dummy)
            except ImportError:
                from auto import (_obter_info_dispositivo, _buscar_loaders_db, _obter_loader_dummy)
        except Exception as e:
            _log(f'Erro deteccao auto: {e}')
            self._set_lbl(self.lbl_info, 'Erro inesperado.\nReconecte o dispositivo e tente novamente.', _Cores.ERROR)
            self._enable_btn(self.btn_detect, True)
        loader_dummy = _obter_loader_dummy()
        if not loader_dummy:
            self._set_lbl(self.lbl_info, 'Componente nao encontrado.\nVerifique a instalacao do programa.', _Cores.ERROR)
            self._enable_btn(self.btn_detect, True)
            return
        try:
            info = _obter_info_dispositivo(loader_dummy)
            if not info:
                self._set_lbl(self.lbl_info, 'Dispositivo nao respondeu.\nReconecte o aparelho em modo EDL e tente novamente.', _Cores.ERROR)
                self._enable_btn(self.btn_detect, True)
                return
            hwid = info.get('hwid', '')
            pkhash = info.get('pkhash', '')
            vendor = info.get('vendor', 'Desconhecido')
            chipset = info.get('chipset', '')
            memoria = info.get('memoria_auto', 'emmc')
            self._set_lbl(self.lbl_info, f'Fabricante: {vendor} | Chipset: {chipset}\nVerificando compatibilidade...', _Cores.SUCCESS)
            matches = _buscar_loaders_db(hwid, pkhash)
            loader_path = None
            requer_auth = None
            if matches:
                self._loader_matches = matches
                loader_path = matches[0]['path']
                memoria = matches[0].get('memoria', memoria)
                requer_auth = matches[0].get('requer_auth')
                if len(matches) > 1:
                    from PyQt5.QtCore import QMetaObject
                    QMetaObject.invokeMethod(self, '_popular_srv', Qt.QueuedConnection)
            else:
                self._loader_matches = []
            if loader_path:
                self._detected_info = info
                self._loader_path = str(loader_path)
                self._requer_auth = requer_auth
                loader_compativel = str(loader_dummy) == str(loader_path)
                if loader_compativel:
                    self._set_lbl(self.lbl_info, f'Fabricante: {vendor} | Chipset: {chipset}\nModelo suportado!', _Cores.SUCCESS)
                    self._set_lbl(self.lbl_etapa2, 'Dispositivo pronto ÔÇö carregando automaticamente...', _Cores.SUCCESS)
                    self.ops_panel._requer_auth = requer_auth
                    self.ops_panel._vip_auth_id = None
                    from PyQt5.QtCore import QMetaObject, Q_ARG
                    QMetaObject.invokeMethod(self.ops_panel, 'set_loader_skip_sahara', Qt.QueuedConnection, Q_ARG(str, str(loader_path)), Q_ARG(str, memoria), Q_ARG(bool, True))
                    self._enable_btn(self.btn_detect, True)
                    return
                self._set_lbl(self.lbl_info, f'Fabricante: {vendor} | Chipset: {chipset}\nModelo suportado!', _Cores.SUCCESS)
                self._set_lbl(self.lbl_etapa2, 'Reconecte o aparelho em modo EDL\n(desconecte e conecte de volta) e clique\nem "Reconectar e Carregar".', _Cores.WARNING)
                self._enable_btn(self.btn_detect, True)
                self._enable_btn(self.btn_reconectar, True)
                return
            self._set_lbl(self.lbl_info, f'Fabricante: {vendor} | Chipset: {chipset}\nModelo nao suportado ÔÇö use o modo Manual', _Cores.ERROR)
            self._enable_btn(self.btn_detect, True)
        except Exception as e:
            _log(f'Erro deteccao auto: {e}')
            self._set_lbl(self.lbl_info, 'Erro inesperado.\nReconecte o dispositivo e tente novamente.', _Cores.ERROR)
            self._enable_btn(self.btn_detect, True)
    @pyqtSlot()
    def _popular_srv(self):
        self.combo_srv.blockSignals(True)
        self.combo_srv.clear()
        for m in self._loader_matches:
            self.combo_srv.addItem(m['srv'])
        self.combo_srv.setCurrentIndex(0)
        self.combo_srv.blockSignals(False)
        self.srv_frame.setVisible(True)
    def _reconectar(self):
        if not self._loader_path:
            return
        self.btn_reconectar.setEnabled(False)
        self.btn_detect.setEnabled(False)
        self.lbl_etapa2.setText('Verificando conexao...')
        self.lbl_etapa2.setStyleSheet(f'color:{_Cores.WARNING};')
        threading.Thread(target=self._reconnect_thread, daemon=True).start()
    def _reconnect_thread(self):
        porta = fhops.detectar_porta_com()
        if not porta:
            self._set_lbl(self.lbl_etapa2, 'Dispositivo nao encontrado!\nReconecte o aparelho em modo EDL e tente novamente.', _Cores.ERROR)
            self._enable_btn(self.btn_reconectar, True)
            self._enable_btn(self.btn_detect, True)
            return
        self._set_lbl(self.lbl_etapa2, f'Dispositivo encontrado ({porta})\nLendo particoes automaticamente...', _Cores.SUCCESS)
        memoria = 'emmc'
        requer_auth = getattr(self, '_requer_auth', None)
        idx = self.combo_srv.currentIndex()
        if 0 <= idx < len(self._loader_matches):
            memoria = self._loader_matches[idx].get('memoria', 'emmc')
            requer_auth = self._loader_matches[idx].get('requer_auth', requer_auth)
        elif self._detected_info:
            memoria = self._detected_info.get('memoria_auto', 'emmc')
        self.ops_panel._requer_auth = requer_auth
        self.ops_panel._vip_auth_id = None
        self.ops_panel._auto_start_leitura = True
        from PyQt5.QtCore import QMetaObject, Q_ARG
        QMetaObject.invokeMethod(self.ops_panel, 'set_loader', Qt.QueuedConnection, Q_ARG(str, self._loader_path), Q_ARG(str, memoria))
        self._enable_btn(self.btn_detect, True)
    def _set_lbl(self, lbl, txt, cor):
        from PyQt5.QtCore import QMetaObject, Q_ARG
        QMetaObject.invokeMethod(lbl, 'setText', Qt.QueuedConnection, Q_ARG(str, txt))
        QMetaObject.invokeMethod(lbl, 'setStyleSheet', Qt.QueuedConnection, Q_ARG(str, f'color:{cor};'))
    def _enable_btn(self, btn, enabled):
        from PyQt5.QtCore import QMetaObject, Q_ARG
        QMetaObject.invokeMethod(btn, 'setEnabled', Qt.QueuedConnection, Q_ARG(bool, enabled))
class _ModeManual(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._analise_worker = None
        self._setup_ui()
    def _setup_ui(self):
        self.setStyleSheet(f'background-color:{_Cores.BG};')
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(8)
        ctrl = QWidget()
        ctrl.setMinimumWidth(200)
        ctrl.setMaximumWidth(280)
        cl = QVBoxLayout(ctrl)
        cl.setContentsMargins(6, 6, 6, 6)
        cl.setSpacing(6)
        cl.setAlignment(Qt.AlignTop)
        t = QLabel('Selecao Manual')
        t.setFont(QFont('Segoe UI', 14, QFont.Bold))
        t.setStyleSheet(f'color:{_Cores.PRIMARY};')
        cl.addWidget(t)
        s = QLabel('Selecione um arquivo de suporte\n(.elf / .mbn / .bin / .melf) do disco.\n\nO tipo de armazenamento (eMMC/UFS)\nsera detectado automaticamente.')
        s.setFont(QFont('Segoe UI', 9))
        s.setStyleSheet(f'color:{_Cores.MUTED};')
        s.setWordWrap(True)
        cl.addWidget(s)
        cl.addSpacing(6)
        self.btn_sel = QPushButton('Selecionar Arquivo')
        self.btn_sel.setFixedHeight(38)
        self.btn_sel.setFont(QFont('Segoe UI', 11, QFont.Bold))
        self.btn_sel.setCursor(Qt.PointingHandCursor)
        self.btn_sel.setStyleSheet(f'\n            QPushButton{{background-color:{_Cores.PRIMARY};color:{_Cores.WHITE};\n                border:none;border-radius:6px;}}\n            QPushButton:hover{{background-color:{_Cores.PRI_HOV};}}\n        ')
        self.btn_sel.clicked.connect(self._selecionar)
        cl.addWidget(self.btn_sel)
        self.lbl_arq = QLabel('Nenhum arquivo selecionado')
        self.lbl_arq.setFont(QFont('Segoe UI', 9))
        self.lbl_arq.setStyleSheet(f'color:{_Cores.MUTED};')
        self.lbl_arq.setWordWrap(True)
        cl.addWidget(self.lbl_arq)
        self.lbl_detect = QLabel('')
        self.lbl_detect.setFont(QFont('Segoe UI', 9))
        self.lbl_detect.setStyleSheet(f'color:{_Cores.MUTED};')
        self.lbl_detect.setWordWrap(True)
        cl.addWidget(self.lbl_detect)
        self._info_frame = QFrame()
        self._info_frame.setStyleSheet(f'QFrame {{ background-color: {_Cores.INFO_BG}; border: 1px solid {_Cores.INFO_BD}; border-radius: 8px; }}')
        self._info_frame.setVisible(False)
        info_lay = QVBoxLayout(self._info_frame)
        info_lay.setContentsMargins(10, 8, 10, 8)
        info_lay.setSpacing(2)
        self._lbl_info_titulo = QLabel('­ƒöì Analise do Arquivo')
        self._lbl_info_titulo.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self._lbl_info_titulo.setStyleSheet(f'color:{_Cores.PRIMARY};border:none;')
        info_lay.addWidget(self._lbl_info_titulo)
        self._lbl_fabricante = QLabel()
        self._lbl_fabricante.setFont(QFont('Segoe UI', 9))
        self._lbl_fabricante.setStyleSheet(f'color:{_Cores.TEXT};border:none;')
        info_lay.addWidget(self._lbl_fabricante)
        self._lbl_chipsets = QLabel()
        self._lbl_chipsets.setFont(QFont('Segoe UI', 9))
        self._lbl_chipsets.setStyleSheet(f'color:{_Cores.TEXT};border:none;')
        info_lay.addWidget(self._lbl_chipsets)
        self._lbl_integridade = QLabel()
        self._lbl_integridade.setFont(QFont('Segoe UI', 9))
        self._lbl_integridade.setStyleSheet(f'color:{_Cores.TEXT};border:none;')
        info_lay.addWidget(self._lbl_integridade)
        self._lbl_pkhash = QLabel()
        self._lbl_pkhash.setFont(QFont('Consolas', 8))
        self._lbl_pkhash.setStyleSheet(f'color:{_Cores.MUTED};border:none;')
        self._lbl_pkhash.setWordWrap(True)
        self._lbl_pkhash.setTextInteractionFlags(Qt.TextSelectableByMouse)
        info_lay.addWidget(self._lbl_pkhash)
        self._lbl_formato = QLabel()
        self._lbl_formato.setFont(QFont('Segoe UI', 9))
        self._lbl_formato.setStyleSheet(f'color:{_Cores.MUTED};border:none;')
        info_lay.addWidget(self._lbl_formato)
        cl.addWidget(self._info_frame)
        cl.addStretch()
        lay.addWidget(ctrl)
        self.ops_panel = _PartitionOpsPanel()
        lay.addWidget(self.ops_panel, stretch=1)
    def _selecionar(self):
        docs = str(Path.home() / 'Documents')
        if not os.path.isdir(docs):
            docs = str(Path.home())
        path, _ = QFileDialog.getOpenFileName(self, 'Selecionar Arquivo de Suporte', docs, 'Arquivos Qualcomm (*.elf *.mbn *.bin *.melf);;Todos (*.*)')
        if not path:
            return
        self.lbl_arq.setText(f'Arquivo: {os.path.basename(path)}')
        self.lbl_arq.setStyleSheet(f'color:{_Cores.SUCCESS};')
        mem = self._detectar_mem_do_loader(path)
        self.lbl_detect.setText(f'Tipo detectado pelo nome: {mem.upper()}\n(sera confirmado pelo dispositivo)')
        self.lbl_detect.setStyleSheet(f'color:{_Cores.MUTED};')
        self.ops_panel.set_loader(path, mem)
        self._info_frame.setVisible(False)
        self._analise_worker = _LoaderAnalyzerWorker(path)
        self._analise_worker.finished_signal.connect(self._on_analise)
        self._analise_worker.start()
    def _on_analise(self, info: dict):
        fab = info.get('fabricante', 'Desconhecido')
        total = info.get('chipsets_total', 0)
        integ = info.get('integridade', 'N/A')
        bits = info.get('bits', '')
        algo = info.get('hash_algo', '')
        pk = info.get('pk_hash', '')
        tam = info.get('tamanho_kb', 0)
        self._lbl_fabricante.setText(f'Fabricante: {fab}')
        if total > 0:
            self._lbl_chipsets.setText(f'Compativel com {total} processadores Qualcomm')
        else:
            self._lbl_chipsets.setText('Processadores: nao identificado')
        cor = _Cores.SUCCESS if integ.startswith('OK') else _Cores.ERROR if integ.startswith('FALHA') else _Cores.MUTED
        self._lbl_integridade.setText(f'Integridade: {integ}')
        self._lbl_integridade.setStyleSheet(f'color:{cor};border:none;')
        if pk:
            self._lbl_pkhash.setText(f'PK_HASH: {pk}')
            self._lbl_pkhash.setVisible(True)
        else:
            self._lbl_pkhash.setVisible(False)
        fmt_parts = []
        if bits:
            fmt_parts.append(f'{bits}-bit')
        if algo:
            fmt_parts.append(algo)
        if tam > 0:
            fmt_parts.append(f'{tam} KB')
        self._lbl_formato.setText(' | '.join(fmt_parts) if fmt_parts else '')
        self._info_frame.setVisible(True)
    def _detectar_mem_do_loader(self, path: str) -> str:
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
class PartitionManagerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"\n            QTabBar::tab{{\n                min-width:80px;padding:5px 10px;\n                font-size:11px;font-family:'Segoe UI';font-weight:bold;}}\n            QTabBar::tab:selected{{\n                color:{_Cores.PRIMARY};\n                border-bottom:2px solid {_Cores.PRIMARY};}}\n        ")
        self._marca_tab = _ModeMarcaModelo()
        self.tabs.addTab(self._marca_tab, 'Marca / Modelo')
        self._auto_tab = _ModeAutomatico()
        self.tabs.addTab(self._auto_tab, 'Automatico')
        self._manual_tab = _ModeManual()
        self.tabs.addTab(self._manual_tab, 'Manual')
        lay.addWidget(self.tabs)
    def pre_configurar_auth(self, tipo: str):
        for tab in self._marca_tab, self._auto_tab, self._manual_tab:
            panel = getattr(tab, 'ops_panel', None)
            if not panel:
                continue
            if hasattr(panel, '_auth_selector'):
                panel._auth_selector.set_auth_type(tipo)
    def carregar_loader_e_iniciar(self, loader_path: str, memoria: str='emmc', requer_auth: str=None):
        _log(f'Partitions: loader recebido ({loader_path}), mem={memoria}, auth={requer_auth}')
        auto_tab = self._auto_tab
        panel = getattr(auto_tab, 'ops_panel', None)
        if not panel:
            _log('Partitions: ops_panel nao encontrado na sub-aba Automatico')
            return
        self.tabs.setCurrentWidget(auto_tab)
        if hasattr(auto_tab, 'lbl_info'):
            auto_tab.lbl_info.setText('Dispositivo identificado!\nCarregando particoes automaticamente...')
            auto_tab.lbl_info.setStyleSheet(f'color:{_Cores.SUCCESS};')
        if hasattr(auto_tab, 'btn_detect'):
            auto_tab.btn_detect.setEnabled(False)
        if requer_auth:
            panel._requer_auth = requer_auth
            if hasattr(panel, '_auth_selector'):
                panel._auth_selector.set_auth_type(requer_auth)
        panel._auto_start_leitura = True
        from PyQt5.QtCore import QMetaObject, Q_ARG
        QMetaObject.invokeMethod(panel, 'set_loader', Qt.QueuedConnection, Q_ARG(str, loader_path), Q_ARG(str, memoria))
# WARNING: Decompyle incomplete
