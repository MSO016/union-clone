import base64
import logging
import os
import time
from typing import (Callable, List, Optional, Tuple)
from . import _dmiti_partition_core as _pcore
from .dmiti_engine import DmitiEngine, DmitiClient
logger = logging.getLogger(__name__)
LogCb = Callable[[str], None]
ProgressCb = Callable[[int], None]
def _noop(msg):
    pass
def _noop_progress(val):
    pass
class DmitiPartitionEngine:
    def __init__(self):
        self._engine = DmitiEngine()
        self._client = None
        self._sessao_ativa = False
        self._cancelado = False
        self.device_info = {}
    @property
    def available(self) -> bool:
        return self._engine.available
    @property
    def session_active(self) -> bool:
        return self._sessao_ativa and self._client is not None and self._client._serial is not None and self._client._serial.is_open
    def cancel(self):
        self._cancelado = True
        if self._client:
            self._client.cancelar()
    def connect_and_list(self, log_cb: LogCb=None) -> Tuple[bool, str, list]:
        log = log_cb or _noop
        self._cancelado = False
        self.device_info = {}
        if self._sessao_ativa:
            self.disconnect(log_cb)
        ok, msg, porta_diag = self._engine.boot_diag(log_cb=log)
        if not ok:
            return False, msg, []
        if self._cancelado:
            return False, 'Operacao cancelada.', []
        client = DmitiClient()
        if not client.abrir(porta_diag, log_cb=log):
            return False, 'Falha ao conectar ao dispositivo.', []
        time.sleep(1.0)
        try:
            if client._serial:
                client._serial.reset_input_buffer()
        except Exception:
            pass
        if not client.init(log_cb=log):
            client.fechar()
            return False, 'Falha na comunicacao com o dispositivo.', []
        self._client = client
        self._sessao_ativa = True
        if self._cancelado:
            self.disconnect()
            return False, 'Operacao cancelada.', []
        self._read_device_info(log)
        log('Lendo tabela de particoes...')
        partitions = self._engine._parse_gpt(client, log)
        if not partitions:
            self.disconnect()
            return False, 'Falha ao ler tabela de particoes.', []
        log('%d particoes encontradas.' % len(partitions))
        return True, 'Conectado', partitions
    def disconnect(self, log_cb: LogCb=None):
        log = log_cb or _noop
        self._sessao_ativa = False
        if self._client:
            try:
                self._client.fechar()
            except Exception:
                pass
            self._client = None
        log('Sessao encerrada.')
    def partition_read(self, part: dict, filepath: str, log_cb: LogCb=None, progress_cb: ProgressCb=None) -> Tuple[bool, str]:
        log = log_cb or _noop
        progress = progress_cb or _noop_progress
        self._cancelado = False
        if not self._check_session(log):
            return (False, 'Sessao nao ativa. Reconecte o dispositivo.')
        name = part['name']
        start_lba = part['start_lba']
        size_bytes = part['size_sectors'] * 512
        chunk_size = _pcore.CHUNK_READ_BYTES
        log(f'Backup: {name!s} ({_pcore.format_size(part['size_mb'])!s})')
        total_chunks = (size_bytes + chunk_size - 1) // chunk_size
        data_total = bytearray()
        t0 = time.time()
        for i in range(total_chunks):
            if self._cancelado:
                return (False, 'Operacao cancelada.')
            byte_offset = start_lba * 512 + i * chunk_size
            chunk_data = self._read_chunk(byte_offset, chunk_size)
            if chunk_data is None:
                logger.debug('Read fail chunk %d/%d off=%d', i, total_chunks, byte_offset)
                return (False, 'Falha na leitura do dispositivo.')
            data_total.extend(chunk_data)
            pct = int((i + 1) / total_chunks * 100)
            progress(pct)
            if (i + 1) % 100 != 0:
                continue
            kb = len(data_total) // 1024
            elapsed = int(time.time() - t0)
            if pct > 0 and pct < 100:
                restante = int(elapsed * (100 - pct) / pct)
                rm = restante // 60
                rs = restante % 60
                log('  %d KB lidos... (%d%% | ~%dm%02ds restantes)' % (kb, pct, rm, rs))
                continue
            log('  %d KB lidos... (%d%%)' % (kb, pct))
            continue
        try:
            dir_path = os.path.dirname(filepath)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(data_total)
            log('Arquivo salvo: %s (%d bytes)' % (os.path.basename(filepath), len(data_total)))
        except Exception as e:
            logger.debug('Save error: %s', e)
            return (False, 'Falha ao salvar arquivo.')
        return True, 'Backup concluido (%d bytes).' % len(data_total)
    def partition_write(self, part: dict, filepath: str, log_cb: LogCb=None, progress_cb: ProgressCb=None) -> Tuple[bool, str]:
        log = log_cb or _noop
        progress = progress_cb or _noop_progress
        self._cancelado = False
        if not self._check_session(log):
            return (False, 'Sessao nao ativa. Reconecte o dispositivo.')
        name = part['name']
        start_lba = part['start_lba']
        max_bytes = part['size_sectors'] * 512
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
        except Exception as e:
            logger.debug('File read error: %s', e)
            return (False, 'Falha ao ler arquivo.')
        if len(data) > max_bytes:
            return (False, 'Arquivo maior que a particao.')
        log('Gravando: %s (%d bytes)' % (name, len(data)))
        log('Elevando privilegios...')
        try:
            self._client.privilege_elevate()
        except Exception:
            pass
        time.sleep(1.5)
        base_offset = start_lba * 512
        chunk_size = _pcore.CHUNK_WRITE_BYTES
        total_chunks = (len(data) + chunk_size - 1) // chunk_size
        t0 = time.time()
        for i in range(total_chunks):
            if self._cancelado:
                return (False, 'Operacao cancelada.')
            chunk = data[i * chunk_size:(i + 1) * chunk_size]
            chunk_b64 = base64.b64encode(chunk).decode('ascii')
            write_offset = base_offset + i * chunk_size
            cmd = "printf '%s' | base64 -d | dd of=/dev/block/mmcblk0 bs=1 seek=%d conv=notrunc 2>&1" % (chunk_b64, write_offset)
            ok = False
            for attempt in range(_pcore.MAX_RETRIES):
                try:
                    resp = self._client.shell(cmd, timeout_ms=15000)
                    if resp is not None:
                        ok = True
                        break
                except Exception:
                    pass
                time.sleep(0.3)
            if not ok:
                logger.debug('Write fail chunk %d/%d', i, total_chunks)
                return (False, 'Falha na gravacao.')
            pct = int((i + 1) / total_chunks * 100)
            progress(pct)
            if (i + 1) % 50 != 0:
                continue
            kb = (i + 1) * chunk_size // 1024
            elapsed = int(time.time() - t0)
            if pct > 0 and pct < 100:
                restante = int(elapsed * (100 - pct) / pct)
                rm = restante // 60
                rs = restante % 60
                log('  %d KB gravados... (%d%% | ~%dm%02ds restantes)' % (kb, pct, rm, rs))
                continue
            log('  %d KB gravados... (%d%%)' % (kb, pct))
            continue
        try:
            self._client.shell('sync', timeout_ms=5000)
        except Exception:
            pass
        log('Gravacao concluida.')
        return (True, 'Gravacao concluida.')
    def partition_erase(self, part: dict, log_cb: LogCb=None, progress_cb: ProgressCb=None) -> Tuple[bool, str]:
        log = log_cb or _noop
        progress = progress_cb or _noop_progress
        self._cancelado = False
        if not self._check_session(log):
            return (False, 'Sessao nao ativa. Reconecte o dispositivo.')
        name = part['name']
        start_lba = part['start_lba']
        size_sec = part['size_sectors']
        log(f'Zerando: {name!s} ({_pcore.format_size(part['size_mb'])!s})')
        log('Elevando privilegios...')
        try:
            self._client.privilege_elevate()
        except Exception:
            pass
        time.sleep(1.5)
        chunk_sectors = 2048
        total_chunks = (size_sec + chunk_sectors - 1) // chunk_sectors
        offset = 0
        t0 = time.time()
        for i in range(total_chunks):
            if self._cancelado:
                return (False, 'Operacao cancelada.')
            current_seek = start_lba + offset
            current_count = min(chunk_sectors, size_sec - offset)
            cmd = 'dd if=/dev/zero of=/dev/block/mmcblk0 bs=512 seek=%d count=%d 2>&1' % (current_seek, current_count)
            ok = False
            for attempt in range(_pcore.MAX_RETRIES):
                try:
                    resp = self._client.shell(cmd, timeout_ms=30000)
                    if resp is not None:
                        ok = True
                        break
                except Exception:
                    pass
                time.sleep(0.3)
            if not ok:
                logger.debug('Erase fail chunk %d/%d', i, total_chunks)
                return (False, 'Falha ao zerar particao.')
            offset += current_count
            pct = int((i + 1) / total_chunks * 100)
            progress(pct)
            if not total_chunks > 1:
                continue
            if (i + 1) % max(1, total_chunks // 5) != 0:
                continue
            elapsed = int(time.time() - t0)
            if not pct > 0:
                continue
            if not pct < 100:
                continue
            restante = int(elapsed * (100 - pct) / pct)
            rm = restante // 60
            rs = restante % 60
            log('  %d%% zerado... (~%dm%02ds restantes)' % (pct, rm, rs))
            continue
        try:
            self._client.shell('sync', timeout_ms=5000)
        except Exception:
            pass
        log('Particao zerada.')
        return (True, 'Operacao concluida.')
    def reboot(self, log_cb: LogCb=None) -> Tuple[bool, str]:
        log = log_cb or _noop
        if not self._sessao_ativa or not self._client:
            return (False, 'Sessao nao ativa.')
        log('Reiniciando dispositivo...')
        try:
            self._client.shell('sync; setprop sys.powerctl reboot 2>/dev/null; reboot 2>/dev/null', timeout_ms=5000)
        except Exception:
            pass
        self._sessao_ativa = False
        return (True, 'Dispositivo reiniciando.')
    def _read_device_info(self, log: LogCb):
        props = {'brand': 'ro.product.brand', 'model': 'ro.product.model', 'android': 'ro.build.version.release'}
        for key, prop in props.items():
            try:
                val = self._client.shell('getprop %s' % prop, timeout_ms=3000)
                if val:
                    if val.strip():
                        self.device_info[key] = val.strip()[:40]
            except Exception:
                continue
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
        if not self._sessao_ativa:
            return False
        if not self._client or not self._client._serial or not self._client._serial.is_open:
            log('Conexao perdida. Reconecte o dispositivo.')
            self._sessao_ativa = False
            return False
        return True
    def _read_chunk(self, skip_bytes: int, count_bytes: int) -> Optional[bytes]:
        cmd = "dd if=/dev/block/mmcblk0 bs=1 skip=%d count=%d 2>/dev/null | od -An -tx1 -v | tr -d ' \\n'" % (skip_bytes, count_bytes)
        for attempt in range(_pcore.MAX_RETRIES):
            try:
                resp = self._client.shell(cmd, timeout_ms=15000)
            except Exception:
                time.sleep(0.3)
                continue
            if not resp:
                time.sleep(0.3)
                continue
            hex_clean = ''.join((c for c in resp if c in '0123456789abcdef'))
            if len(hex_clean) >= 2:
                try:
                    pass
                except ValueError:
                    continue
                return bytes.fromhex(hex_clean)
