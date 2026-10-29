'''
Orquestrador de particoes (engine nativo desativado por padrao).
Ver: alan/documentacao/16-08-2026-ARQUITETURA-SPD-INTERNA/01_MAPA_REFERENCIAS_INTERNAS.md
'''
import glob
import os
import time
import logging
import threading
from typing import (List, Optional, Callable, Tuple)
from .constants import (FDL_CHUNK_SIZE, FDL2_CHUNK_SIZE, CRITICAL_PARTITIONS, SAFE_FRP_PARTITIONS)
from .checksum import Checksum
from .transport import SerialTransport
from .protocol import SPDProtocol
from .partition import (PartitionManager, PartitionInfo, str_to_size, size_to_str)
log = logging.getLogger(__name__)
class SPDPartitionManager:
    '''
    Gerenciador de parti├º├Áes SPD usando protocolo nativo Python.
    Fluxo:
    1. connect() ÔåÆ detecta porta, boot FDL1+FDL2
    2. list_partitions() ÔåÆ BSL_CMD_READ_PARTITION ou traverse
    3. read/write/erase_partition()
    4. reset()
    '''
    ''
    ''
    ''
    ''
    ''
    ''
    def __init__(self, fdl1_path: str, fdl2_path: str, fdl1_addr: int=1694500864, fdl2_addr: int=2667576832, exec_addr: int=1694588680, custom_exec_path: Optional[str]=None, log_cb: Optional[Callable[[str, str], None]]=None, progress_cb: Optional[Callable[[int], None]]=None):
        self.fdl1_path = fdl1_path
        self.fdl2_path = fdl2_path
        self.fdl1_addr = fdl1_addr
        self.fdl2_addr = fdl2_addr
        self.exec_addr = exec_addr
        self.custom_exec_path = custom_exec_path
        self._log_cb = log_cb
        self._progress_cb = progress_cb
        self._transport = None
        self._proto = None
        self._partition_mgr = None
        self._connected = False
        self._partitions = []
        self._cancel = threading.Event()
    @property
    def connected(self) -> bool:
        return self._connected
    @property
    def partitions(self) -> List[PartitionInfo]:
        return list(self._partitions)
    def _log(self, msg: str, level: str='INFO'):
        log.debug(f'[SPD-PART] [{level}] {msg}')
        if self._log_cb:
            self._log_cb(msg, level)
    def _progress(self, value: int):
        if self._progress_cb:
            self._progress_cb(min(100, max(0, value)))
    def _log_bridge(self, msg: str, ok: bool) -> None:
        if ok:
            self._log(msg, 'OK')
            return
        None(None, 'ERROR')
    def _progress_bridge(self, current: int, total: int) -> None:
        if total > 0:
            self._progress(int(current * 100 / total))
    def connect(self, port: str=None, wait_timeout: int=60) -> bool:
        '''
        Conecta via protocolo nativo: detect ÔåÆ FDL1(CRC16) ÔåÆ FDL2(ADD) ÔåÆ enable_flash.
        '''
        self._cancel.clear()
        if self._connected:
            self._log('Ja conectado', 'WARN')
            return True
        self._log(f'FDL1: {self.fdl1_path}')
        self._log(f'FDL2: {self.fdl2_path}')
        self._log(f'Addrs: FDL1=0x{self.fdl1_addr:08X} FDL2=0x{self.fdl2_addr:08X} EXEC=0x{self.exec_addr:08X}')
        if not os.path.exists(self.fdl1_path):
            self._log(f'FDL1 nao encontrado: {self.fdl1_path}', 'ERROR')
            return False
        if not os.path.exists(self.fdl2_path):
            self._log(f'FDL2 nao encontrado: {self.fdl2_path}', 'ERROR')
            return False
        fdl1_sz = os.path.getsize(self.fdl1_path)
        fdl2_sz = os.path.getsize(self.fdl2_path)
        self._log(f'FDL1: {fdl1_sz} bytes | FDL2: {fdl2_sz} bytes')
        self._progress(5)
        if self._cancel.is_set():
            self._log('Cancelado antes da detecao', 'WARN')
            return False
        if port:
            self._log(f'Usando porta: {port}')
        else:
            self._log('Aguardando dispositivo SPD...')
            port = self._detect_port(wait_timeout)
            if not port:
                if self._cancel.is_set():
                    self._log('Cancelado pelo usuario', 'WARN')
                    return False
                self._log('Dispositivo nao encontrado (timeout)', 'ERROR')
                return False
        self._log(f'Abrindo porta serial {port}...')
        self._transport = SerialTransport()
        if not self._transport.connect(port):
            self._log(f'Falha ao abrir porta serial {port}', 'ERROR')
            return False
        self._log(f'Porta {port} aberta com sucesso', 'OK')
        self._progress(10)
        self._proto = SPDProtocol(self._transport)
        try:
            self._boot_fdl()
        except RuntimeError as e:
            self._log(f'Falha boot FDL: {e}', 'ERROR')
            self.disconnect()
            return False
        except Exception as e:
            self._log(f'Erro inesperado no boot FDL: {type(e).__name__}: {e}', 'ERROR')
            log.exception('Boot FDL traceback')
            self.disconnect()
            return False
        self._partition_mgr = PartitionManager(self._proto, progress_cb=self._progress_bridge, log_cb=self._log_bridge)
        self._connected = True
        self._progress(30)
        self._log('Conectado ÔÇö protocolo nativo ativo', 'OK')
        return True
    def _detect_port(self, timeout_s: float) -> Optional[str]:
        '''Detecta porta COM do dispositivo SPD, respeitando _cancel.'''
        try:
            from .device_detect import DeviceDetector
            import time as _time
            detector = DeviceDetector()
            start = _time.time()
            while _time.time() - start < timeout_s:
                if self._cancel.is_set():
                    self._log('Detecao cancelada pelo usuario', 'WARN')
                    return
                device = detector.find_one()
                if device:
                    self._log(f'Dispositivo: {device.port} ({device.name})', 'OK')
                    return device.port
                _time.sleep(0.5)
            self._log(f'Timeout de {timeout_s}s atingido na detecao')
            return
        except Exception as e:
            self._log(f'Erro na detecao: {e}', 'ERROR')
    def _boot_fdl(self) -> None:
        '''
Boot sequence completo:
CRC16: checkbaud ÔåÆ connect ÔåÆ upload FDL1 ÔåÆ exec FDL1
ADD:   checkbaud FDL1 ÔåÆ connect FDL1 ÔåÆ keep_charge ÔåÆ
       upload FDL2 ÔåÆ exec FDL2 ÔåÆ enable_flash
Ponto critico: checksum DEVE trocar de CRC16 para ADD
imediatamente apos EXEC FDL1, ANTES do checkbaud FDL1.
'''
        proto = self._proto
        proto.checksum.set_type('crc16')
        self._log('[1/9] CHECK_BAUD bootrom...')
        ok = proto.send_checkbaud()
        self._log(f'  CHECK_BAUD resultado: {ok}')
        time.sleep(0.05)
        self._log('[2/9] CONNECT bootrom...')
        if not proto.send_connect():
            raise RuntimeError('CONNECT rejeitado pelo bootrom')
        self._log('  CONNECT bootrom: OK')
        if self.custom_exec_path and os.path.isfile(self.custom_exec_path):
            with open(self.custom_exec_path, 'rb') as f:
                exploit_data = f.read()
            self._log(f'  CVE exploit: {len(exploit_data)}B -> 0x{self.exec_addr:08X} ({os.path.basename(self.custom_exec_path)})')
            if not proto.send_start_data(self.exec_addr, len(exploit_data)):
                raise RuntimeError('START_DATA rejeitado (custom_exec)')
            if not proto.send_file_chunks(exploit_data, chunk_size=FDL_CHUNK_SIZE):
                raise RuntimeError('MIDST_DATA falhou (custom_exec)')
            if not proto.send_end_data():
                raise RuntimeError('END_DATA rejeitado (custom_exec)')
            if not proto.send_exec_data():
                raise RuntimeError('EXEC_DATA rejeitado (custom_exec)')
            self._log('  CVE exploit: OK ÔÇö Secure Boot bypass ativo', 'OK')
            time.sleep(0.1)
        elif self.exec_addr:
            self._log('  AVISO: exec_addr definido mas custom_exec nao encontrado ÔÇö Secure Boot pode rejeitar FDL1', 'WARN')
        with open(self.fdl1_path, 'rb') as f:
            fdl1 = f.read()
        self._log(f'[3/9] START_DATA FDL1 ({len(fdl1)} bytes) -> 0x{self.fdl1_addr:08X}')
        if not proto.send_start_data(self.fdl1_addr, len(fdl1)):
            raise RuntimeError('START_DATA rejeitado (FDL1)')
        self._log('  START_DATA FDL1: ACK')
        if self._cancel.is_set():
            raise RuntimeError('Cancelado')
        self._log(f'[4/9] Enviando chunks FDL1 (chunk={FDL_CHUNK_SIZE}B)...')
        if not proto.send_file_chunks(fdl1, chunk_size=FDL_CHUNK_SIZE):
            raise RuntimeError('MIDST_DATA falhou (FDL1)')
        self._log('  FDL1 chunks: OK')
        self._log('[5/9] END_DATA FDL1...')
        if not proto.send_end_data():
            raise RuntimeError('END_DATA rejeitado (FDL1)')
        self._log('  END_DATA FDL1: ACK')
        self._log('[6/9] EXEC_DATA FDL1...')
        if not proto.send_exec_data():
            raise RuntimeError('EXEC_DATA rejeitado (FDL1)')
        self._log('  EXEC FDL1: OK ÔÇö aguardando re-enumeracao USB...', 'OK')
        self._progress(15)
        proto.checksum.set_type('add')
        self._log('  Checksum: CRC16 -> ADD (modo FDL1)')
        time.sleep(1.0)
        fdl1_found = False
        for attempt in range(20):
            if self._cancel.is_set():
                raise RuntimeError('Cancelado durante retry checkbaud')
            try:
                if proto.send_checkbaud():
                    self._log(f'  CHECK_BAUD FDL1 OK (tentativa {attempt + 1})')
                    fdl1_found = True
                    break
            except Exception as e:
                if attempt % 5 == 4:
                    self._log(f'  CHECK_BAUD tentativa {attempt + 1}: {e}')
            time.sleep(0.3)
        if not fdl1_found:
            raise RuntimeError('CHECK_BAUD falhou apos EXEC FDL1 (20 tentativas)')
        self._log('[7/9] CONNECT FDL1...')
        if not proto.send_connect():
            raise RuntimeError('CONNECT rejeitado pelo FDL1')
        self._log('  CONNECT FDL1: OK')
        try:
            proto.send_keepcharge()
            self._log('  KEEP_CHARGE: OK')
        except Exception as e:
            self._log(f'  KEEP_CHARGE: ignorado ({e})', 'WARN')
        with open(self.fdl2_path, 'rb') as f:
            fdl2 = f.read()
        self._log(f'[8/9] START_DATA FDL2 ({len(fdl2)} bytes) -> 0x{self.fdl2_addr:08X}')
        if not proto.send_start_data(self.fdl2_addr, len(fdl2)):
            raise RuntimeError('START_DATA rejeitado (FDL2)')
        self._log('  START_DATA FDL2: ACK')
        if self._cancel.is_set():
            raise RuntimeError('Cancelado antes do envio FDL2')
        total_chunks = (len(fdl2) + FDL2_CHUNK_SIZE - 1) // FDL2_CHUNK_SIZE
        self._log(f'  Enviando FDL2: {total_chunks} chunks de {FDL2_CHUNK_SIZE}B...')
        if not proto.send_file_chunks(fdl2, chunk_size=FDL2_CHUNK_SIZE):
            raise RuntimeError('MIDST_DATA falhou (FDL2)')
        self._log('  FDL2 chunks: OK')
        self._log('  END_DATA FDL2...')
        if not proto.send_end_data():
            raise RuntimeError('END_DATA rejeitado (FDL2)')
        self._log('[9/9] EXEC_DATA FDL2...')
        if not proto.send_exec_data():
            raise RuntimeError('EXEC_DATA rejeitado (FDL2)')
        self._log('  EXEC FDL2: OK', 'OK')
        self._progress(25)
        time.sleep(0.2)
        self._log('Lendo info da flash...')
        try:
            proto.send_read_flash_info()
            self._log('  READ_FLASH_INFO: OK')
        except Exception as e:
            self._log(f'  READ_FLASH_INFO: nao suportado ({e})', 'WARN')
        time.sleep(0.3)
        self._log('Enviando DISABLE_TRANSCODE...')
        try:
            if proto.send_disable_transcode():
                self._log('  DISABLE_TRANSCODE: OK ÔÇö non-transcode ativo', 'OK')
                return
            self._log('  DISABLE_TRANSCODE: rejeitado ÔÇö mantendo HDLC', 'WARN')
        except Exception as e:
            self._log(f'  DISABLE_TRANSCODE: erro ({e})', 'WARN')
    def disconnect(self):
        if self._transport:
            try:
                self._transport.disconnect()
            except Exception:
                pass
        self._transport = None
        self._proto = None
        self._partition_mgr = None
        self._connected = False
        self._log('Desconectado')
    def list_partitions(self) -> List[PartitionInfo]:
        if not self._connected:
            self._log('Nao conectado', 'ERROR')
            return []
        self._log('Listando particoes...')
        self._progress(40)
        partitions = self._partition_mgr.list_partitions()
        self._partitions = partitions
        self._progress(60)
        self._log(f'{len(partitions)} particoes encontradas', 'OK')
        return partitions
    def read_partition(self, name: str, output_path: str, size_str: Optional[str]=None) -> Tuple[bool, str]:
        if not self._connected:
            return (False, 'Nao conectado')
        self._log(f"Lendo particao '{name}'...")
        self._progress(10)
        if not size_str:
            part = self._find_partition(name)
            if part and part.size_bytes > 0:
                size_str = part.size_str
            else:
                size_str = self._partition_mgr.check_partition_size(name)
                if size_str == '0':
                    return False, f"Particao '{name}' nao encontrada ou tamanho 0"
        try:
            ok = self._partition_mgr.read_partition(name, size_str, output_path)
            if ok:
                self._log(f"Backup de '{name}': {output_path}", 'OK')
                self._progress(100)
                return True, output_path
        except Exception as e:
            self._log(f"Erro ao ler '{name}': {e}", 'ERROR')
            return False, str(e)
        return (False, 'Falha na leitura')
    def write_partition(self, name: str, input_path: str) -> Tuple[bool, str]:
        if not self._connected:
            return (False, 'Nao conectado')
        if name.lower() in CRITICAL_PARTITIONS:
            msg = f"BLOQUEADO: '{name}' e particao critica"
            self._log(msg, 'ERROR')
            return False, msg
        if not os.path.exists(input_path):
            return False, f'Arquivo nao encontrado: {input_path}'
        self._log(f"Gravando '{name}'...")
        self._progress(10)
        try:
            ok = self._partition_mgr.flash_partition(name, input_path)
            if ok:
                self._log(f"Gravacao de '{name}' concluida", 'OK')
                self._progress(100)
                return (True, 'OK')
        except Exception as e:
            self._log(f"Erro ao gravar '{name}': {e}", 'ERROR')
            return False, str(e)
        return (False, 'Falha na gravacao')
    def erase_partition(self, name: str) -> Tuple[bool, str]:
        if not self._connected:
            return (False, 'Nao conectado')
        if name.lower() in CRITICAL_PARTITIONS:
            msg = f"BLOQUEADO: '{name}' e particao critica"
            self._log(msg, 'ERROR')
            return False, msg
        self._log(f"Apagando '{name}'...")
        self._progress(20)
        try:
            size_str = '2M'
            part = self._find_partition(name)
            if part and part.size_bytes > 0:
                computed = size_to_str(part.size_bytes)
                if computed != '0':
                    size_str = computed
            ok = self._partition_mgr.erase_partition(name, size_str)
            if ok:
                self._log(f"'{name}' apagada", 'OK')
                self._progress(100)
                return (True, 'OK')
        except Exception as e:
            self._log(f"Erro ao apagar '{name}': {e}", 'ERROR')
            return False, str(e)
        return (False, 'Falha no erase')
    def reset(self) -> Tuple[bool, str]:
        if not self._connected:
            return (False, 'Nao conectado')
        self._log('Reiniciando dispositivo...')
        try:
            self._proto.send_reset()
            self._connected = False
            self._log('Dispositivo reiniciado', 'OK')
            return (True, 'OK')
        except Exception as e:
            return False, str(e)
    def _find_partition(self, name: str) -> Optional[PartitionInfo]:
        for p in self._partitions:
            if not p.name.lower() == name.lower():
                continue
            return p
    def cancel(self) -> None:
        self._cancel.set()
    @classmethod
    def from_model_config(cls, model_txt_path: str, model_dir: str, log_cb=None, progress_cb=None) -> 'SPDPartitionManager':
        '''
        Factory: cria instancia a partir do .txt de modelo.
        Busca FDLs em model_dir primeiro. Se nao encontrar, tenta
        subdiretorio baseado no nome do modelo (Models/BRAND/MODEL/).
        '''
        fdl1_addr = 1694500864
        fdl2_addr = 2667576832
        exec_addr = 1694588680
        fdl1_file = 'fdl1-sign.bin'
        fdl2_file = 'fdl2-sign.bin'
        with open(model_txt_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('FDL1Address'):
                    fdl1_addr = int(line.split(':')[-1].strip(), 16)
                    continue
                if line.startswith('FDL2Address'):
                    fdl2_addr = int(line.split(':')[-1].strip(), 16)
                    continue
                if line.startswith('ExecAddress'):
                    exec_addr = int(line.split(':')[-1].strip(), 16)
                    continue
                if line.startswith('FDL1File'):
                    fdl1_file = line.split(':')[-1].strip()
                    continue
                if not line.startswith('FDL2File'):
                    continue
                fdl2_file = line.split(':')[-1].strip()
                continue
        fdl1 = os.path.join(model_dir, fdl1_file)
        fdl2 = os.path.join(model_dir, fdl2_file)
        fdl1_dl = os.path.join(model_dir, 'fdl1-dl.bin')
        fdl2_dl = os.path.join(model_dir, 'fdl2-dl.bin')
        if os.path.isfile(fdl1_dl):
            fdl1 = fdl1_dl
            log.info(f'Usando fdl1-dl.bin (preferencia sobre {fdl1_file})')
        if os.path.isfile(fdl2_dl):
            fdl2 = fdl2_dl
            log.info(f'Usando fdl2-dl.bin (preferencia sobre {fdl2_file})')
        if not os.path.isfile(fdl1):
            model_name = os.path.splitext(os.path.basename(model_txt_path))[0]
            sub_dir = os.path.join(os.path.dirname(model_txt_path), model_name)
            alt_fdl1 = os.path.join(sub_dir, fdl1_file)
            alt_fdl1_dl = os.path.join(sub_dir, 'fdl1-dl.bin')
            if os.path.isfile(alt_fdl1_dl):
                log.info(f'FDL1-dl encontrado em subdiretorio: {sub_dir}')
                model_dir = sub_dir
                fdl1 = alt_fdl1_dl
                fdl2 = os.path.join(sub_dir, 'fdl2-dl.bin')
                if not os.path.isfile(fdl2):
                    fdl2 = os.path.join(sub_dir, fdl2_file)
            elif os.path.isfile(alt_fdl1):
                log.info(f'FDL1 encontrado em subdiretorio: {sub_dir}')
                model_dir = sub_dir
                fdl1 = alt_fdl1
                fdl2 = os.path.join(sub_dir, fdl2_file)
        custom_exec_path = None
        candidates = glob.glob(os.path.join(model_dir, 'custom_exec_no_verify_*.bin'))
        if candidates:
            custom_exec_path = candidates[0]
            log.info(f'Custom exec encontrado: {os.path.basename(custom_exec_path)}')
        else:
            model_name = os.path.splitext(os.path.basename(model_txt_path))[0]
            sub_dir = os.path.join(os.path.dirname(model_txt_path), model_name)
            sub_candidates = glob.glob(os.path.join(sub_dir, 'custom_exec_no_verify_*.bin'))
            if sub_candidates:
                custom_exec_path = sub_candidates[0]
                log.info(f'Custom exec (subdir): {os.path.basename(custom_exec_path)}')
        return cls(fdl1_path=fdl1, fdl2_path=fdl2, fdl1_addr=fdl1_addr, fdl2_addr=fdl2_addr, exec_addr=exec_addr, custom_exec_path=custom_exec_path, log_cb=log_cb, progress_cb=progress_cb)
# WARNING: Decompyle incomplete
