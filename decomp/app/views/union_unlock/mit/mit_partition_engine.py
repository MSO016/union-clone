'''
Engine do gerenciador de particoes META ÔÇö composicao via MitEngine.
Ref: administrativo/documentacao/29-07-2026-ANALISE-MTK-BOOT-META - V2/
'''
import base64
import logging
import os
import time
from typing import (Callable, List, Optional, Tuple)
from . import _mit_partition_core as _pcore
from .mit_engine import MitEngine
logger = logging.getLogger(__name__)
LogCb = Callable[[str], None]
ProgressCb = Callable[[int], None]
def _noop(msg):
    pass
def _noop_progress(val):
    pass
class MitPartitionEngine:
    '''Engine de particoes ÔÇö sessao persistente com reuso do MitEngine.'''
    def __init__(self):
        self._engine = MitEngine()
        self._porta = ''
        self._sessao_ativa = False
        self._cancelado = False
    @property
    def available(self) -> bool:
        return self._engine.available
    @property
    def session_active(self) -> bool:
        return self._sessao_ativa and self._engine._ser is not None
    def cancel(self):
        '''Cancela operacao em andamento.'''
        self._cancelado = True
        self._engine.cancel()
    def connect_and_list(self, log_cb: LogCb=None) -> Tuple[bool, str, list]:
        '''Boot META + sessao + parse GPT completo.
        Retorna (ok, msg, lista_particoes).'''
        log = log_cb or _noop
        self._cancelado = False
        self.device_info = {}
        if self._sessao_ativa:
            self.disconnect(log_cb)
        ok, msg, porta = self._engine.boot_meta(log_cb=log)
        if not ok:
            return False, msg, []
        self._porta = porta
        if self._cancelado:
            return False, 'Operacao cancelada.', []
        try:
            self._engine._open_session(porta, log_cb=log)
        except Exception:
            return False, 'Falha ao estabelecer sessao.', []
        self._sessao_ativa = True
        if self._cancelado:
            self.disconnect()
            return False, 'Operacao cancelada.', []
        self._read_device_info(log)
        log('Lendo tabela de particoes...')
        partitions = self._parse_gpt_full(log)
        if not partitions:
            self.disconnect()
            return False, 'Falha ao ler tabela de particoes.', []
        log('%d particoes encontradas.' % len(partitions))
        return True, 'Conectado', partitions
    def disconnect(self, log_cb: LogCb=None):
        '''Encerra sessao limpa.'''
        log = log_cb or _noop
        self._sessao_ativa = False
        try:
            self._engine._close_serial()
        except Exception:
            pass
        self._porta = ''
        log('Sessao encerrada.')
    def partition_read(self, part: dict, filepath: str, log_cb: LogCb=None, progress_cb: ProgressCb=None) -> Tuple[bool, str]:
        '''Le particao inteira para arquivo .bin.'''
        log = log_cb or _noop
        progress = progress_cb or _noop_progress
        self._cancelado = False
        if not self._check_session(log):
            return (False, 'Sessao nao ativa.')
        name = part['name']
        start_lba = part['start_lba']
        size_bytes = part['size_sectors'] * 512
        base_offset = start_lba * 512
        chunk_size = _pcore.CHUNK_READ_BYTES
        log(f'Backup: {name!s} ({_pcore.format_size(part['size_mb'])!s})')
        total_chunks = (size_bytes + chunk_size - 1) // chunk_size
        data_total = bytearray()
        for i in range(total_chunks):
            if self._cancelado:
                return (False, 'Operacao cancelada.')
            current_offset = base_offset + i * chunk_size
            remaining = size_bytes - i * chunk_size
            current_size = min(chunk_size, remaining)
            chunk_data = self._read_chunk(current_offset, current_size)
            if chunk_data is None:
                return False, 'Falha na leitura (bloco %d/%d).' % (i + 1, total_chunks)
            data_total.extend(chunk_data)
            progress(int((i + 1) / total_chunks * 100))
            if (i + 1) % 50 == 0:
                log('  %d KB lidos...' % (len(data_total) // 1024))
        try:
            dir_path = os.path.dirname(filepath)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(data_total)
            log('Arquivo salvo: %s (%d bytes)' % (os.path.basename(filepath), len(data_total)))
        except Exception:
            return (False, 'Falha ao salvar arquivo.')
        return True, 'Backup concluido (%d bytes).' % len(data_total)
    def partition_write(self, part: dict, filepath: str, log_cb: LogCb=None, progress_cb: ProgressCb=None) -> Tuple[bool, str]:
        '''Grava arquivo .bin na particao.'''
        log = log_cb or _noop
        progress = progress_cb or _noop_progress
        self._cancelado = False
        if not self._check_session(log):
            return (False, 'Sessao nao ativa.')
        name = part['name']
        start_lba = part['start_lba']
        max_bytes = part['size_sectors'] * 512
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
        except Exception:
            return (False, 'Falha ao ler arquivo.')
        if len(data) > max_bytes:
            return (False, 'Arquivo maior que a particao.')
        log('Gravando: %s (%d bytes)' % (name, len(data)))
        self._backup_gpt(log)
        base_offset = start_lba * 512
        chunk_size = _pcore.CHUNK_WRITE_BYTES
        total_chunks = (len(data) + chunk_size - 1) // chunk_size
        for i in range(total_chunks):
            if self._cancelado:
                return (False, 'Operacao cancelada.')
            chunk = data[i * chunk_size:(i + 1) * chunk_size]
            chunk_b64 = base64.b64encode(chunk).decode('ascii')
            write_offset = base_offset + i * chunk_size
            cmd = "printf 'S0F:'; printf '%s' | base64 -d | dd of=/dev/block/mmcblk0 bs=1 seek=%d conv=notrunc 2>&1; printf ':E0F'" % (chunk_b64, write_offset)
            for attempt in range(_pcore.MAX_RETRIES):
                resp = self._shell(cmd, timeout=15.0)
                if resp is not None:
                    break
                time.sleep(0.3)
            progress(int((i + 1) / total_chunks * 100))
            if (i + 1) % 50 == 0:
                log('  %d KB gravados...' % ((i + 1) * chunk_size // 1024))
        self._shell("printf 'S0F:'; sync; printf ':E0F'", timeout=5.0)
        log('Gravacao concluida.')
        return (True, 'Gravacao concluida.')
    def partition_erase(self, part: dict, log_cb: LogCb=None, progress_cb: ProgressCb=None) -> Tuple[bool, str]:
        '''Preenche particao com zeros.'''
        log = log_cb or _noop
        progress = progress_cb or _noop_progress
        self._cancelado = False
        if not self._check_session(log):
            return (False, 'Sessao nao ativa.')
        name = part['name']
        start_lba = part['start_lba']
        size_sec = part['size_sectors']
        log(f'Zerando: {name!s} ({_pcore.format_size(part['size_mb'])!s})')
        self._backup_gpt(log)
        chunk_sectors = 2048
        total_chunks = (size_sec + chunk_sectors - 1) // chunk_sectors
        offset = 0
        for i in range(total_chunks):
            if self._cancelado:
                return (False, 'Operacao cancelada.')
            current_seek = start_lba + offset
            current_count = min(chunk_sectors, size_sec - offset)
            cmd = "printf 'S0F:'; dd if=/dev/zero of=/dev/block/mmcblk0 bs=512 seek=%d count=%d 2>&1; printf ':E0F'" % (current_seek, current_count)
            for attempt in range(_pcore.MAX_RETRIES):
                resp = self._shell(cmd, timeout=30.0)
                if resp is not None:
                    break
                time.sleep(0.3)
            offset += current_count
            progress(int((i + 1) / total_chunks * 100))
        self._shell("printf 'S0F:'; sync; printf ':E0F'", timeout=5.0)
        log('Particao zerada.')
        return (True, 'Operacao concluida.')
    def reboot(self, log_cb: LogCb=None) -> Tuple[bool, str]:
        '''Reinicia dispositivo e encerra sessao.'''
        log = log_cb or _noop
        if not self._sessao_ativa:
            return (False, 'Sessao nao ativa.')
        log('Reiniciando dispositivo...')
        try:
            self._engine.reboot(self._porta, log_cb=log)
        except Exception:
            pass
        self._sessao_ativa = False
        self._porta = ''
        return (True, 'Dispositivo reiniciando.')
    def _read_device_info(self, log: LogCb):
        '''Le info basica do dispositivo via getprop.'''
        props = {'brand': 'ro.product.brand', 'model': 'ro.product.model', 'android': 'ro.build.version.release', 'chip': 'ro.product.board'}
        for key, prop in props.items():
            cmd = "printf 'S0F:'; getprop %s 2>/dev/null; printf ':E0F'" % prop
            val = self._shell(cmd, timeout=3.0)
            if val:
                self.device_info[key] = val.strip()
        info_parts = []
        if self.device_info.get('brand'):
            info_parts.append(self.device_info['brand'])
        if self.device_info.get('model'):
            info_parts.append(self.device_info['model'])
        if self.device_info.get('android'):
            info_parts.append('Android %s' % self.device_info['android'])
        if info_parts:
            log('Dispositivo: %s' % ' | '.join(info_parts))
    def _check_session(self, log: LogCb) -> bool:
        '''Verifica se sessao esta ativa e serial responsiva.'''
        if not self._sessao_ativa:
            return False
        if not self._engine._ser or not self._engine._ser.is_open:
            log('Conexao perdida. Reconecte o dispositivo.')
            self._sessao_ativa = False
            return False
        return True
    def _shell(self, cmd: str, timeout: float=10.0) -> Optional[str]:
        '''Executa shell via engine (com marcadores S0F/E0F).'''
        try:
            return self._engine._exec_shell(cmd, timeout=timeout)
        except Exception:
            return
    def _backup_gpt(self, log: LogCb=None):
        '''Backup preventivo dos primeiros 34 setores.'''
        log = log or _noop
        cmd = "printf 'S0F:'; dd if=/dev/block/mmcblk0 bs=512 count=%d of=/dev/block/by-name/para 2>/dev/null && echo OK; printf ':E0F'" % _pcore.GPT_BACKUP_SECTORS
        resp = self._shell(cmd, timeout=10.0)
        if resp:
            if 'OK' in resp:
                logger.debug('GPT backup OK')
    def _read_chunk(self, skip_bytes: int, count_bytes: int) -> Optional[bytes]:
        '''Le chunk via dd + xxd.'''
        cmd = "printf 'S0F:'; dd if=/dev/block/mmcblk0 bs=1 skip=%d count=%d 2>/dev/null | xxd -p -l %d; printf ':E0F'" % (skip_bytes, count_bytes, count_bytes)
        for attempt in range(_pcore.MAX_RETRIES):
            resp = self._shell(cmd, timeout=15.0)
            if not resp:
                time.sleep(0.3)
                continue
            hex_clean = ''.join((c for c in resp if c in '0123456789abcdef'))
            if len(hex_clean) < 2:
                time.sleep(0.3)
                continue
            try:
                pass
            except ValueError:
                continue
            return bytes.fromhex(hex_clean)
    def _parse_gpt_full(self, log: LogCb=None) -> List[dict]:
        '''Parse completo da tabela GPT via shell.'''
        log = log or _noop
        partitions = []
        header_hex = self._read_sector_hex(_pcore.GPT_HEADER_OFFSET, 128)
        if not header_hex:
            return []
        try:
            header_raw = bytes.fromhex(header_hex)
        except ValueError:
            return []
        parsed = _pcore.parse_gpt_header(header_raw)
        if not parsed:
            return []
        num_entries, entry_size = parsed
        empty_streak = 0
        for i in range(min(num_entries, _pcore.GPT_MAX_ENTRIES)):
            if self._cancelado:
                return partitions
            offset = _pcore.GPT_ENTRY_START + i * entry_size
            entry_hex = self._read_sector_hex(offset, entry_size)
            if entry_hex:
                try:
                    entry_raw = bytes.fromhex(entry_hex)
                except ValueError:
                    continue
                entry = _pcore.parse_gpt_entry(entry_raw)
                if entry is None:
                    empty_streak += 1
                    if empty_streak >= 3:
                        return partitions
                    continue
                empty_streak = 0
                partitions.append(entry)
                if len(partitions) % 15 == 0:
                    log('Lendo particoes... (%d)' % len(partitions))
        return partitions
    def _read_sector_hex(self, offset: int, count: int=128) -> str:
        '''Le bloco e retorna hex limpo.'''
        cmd = "printf 'S0F:'; dd if=/dev/block/mmcblk0 bs=1 skip=%d count=%d 2>/dev/null | od -An -tx1 -v | tr -d ' \\n'; printf ':E0F'" % (offset, count)
        resp = self._shell(cmd, timeout=5.0)
        if not resp:
            return ''
        return ''.join((c for c in resp if c in '0123456789abcdef'))
