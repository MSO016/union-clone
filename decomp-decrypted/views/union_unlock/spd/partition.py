import os
import struct
import logging
from typing import (Optional, Callable, List)
from dataclasses import dataclass, field
from .constants import (PARTITION_MISC, PARTITION_USERDATA, PARTITION_PERSIST, SIZE_MISC_DEFAULT, SIZE_PERSIST_DEFAULT, PARTITION_CHUNK, COMMON_PARTITIONS, CRITICAL_PARTITIONS, SAFE_FRP_PARTITIONS)
from .protocol import SPDProtocol
log = logging.getLogger(__name__)
def str_to_size(s: str) -> int:
    s = s.upper().strip()
    units = {'K': 10, 'M': 20, 'G': 30}
    for suffix, shift in units.items():
        if s.endswith(suffix):
            return int(s[:-1]) << shift
    return int(s)
def size_to_str(n: int) -> str:
    if n == 0:
        return '0'
    count = 1
    while True:
        if str_to_size(f'{count}M') > n:
            if count > 1:
                return f'{count - 1}M'
            return '1M'
        count += 1
        if count > 1048576:
            return f'{n}'
def format_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return '0'
    if size_bytes >= 1073741824:
        return f'{size_bytes / 1073741824:.1f}GB'
    if size_bytes >= 1048576:
        return f'{size_bytes // 1048576}MB'
    if size_bytes >= 1024:
        return f'{size_bytes // 1024}KB'
    return f'{size_bytes}B'
def _classify_safety(name: str) -> str:
    n = name.lower()
    if n in CRITICAL_PARTITIONS:
        return 'critical'
    if n in SAFE_FRP_PARTITIONS:
        return 'safe'
    if any((x in n for x in ('system', 'vendor', 'product', 'super'))):
        return 'caution'
    return 'unknown'
def _infer_type(name: str) -> str:
    n = name.lower()
    if 'boot' in n:
        return 'boot'
    if any((x in n for x in ('system', 'vendor', 'product', 'super'))):
        return 'ext4'
    if 'userdata' in n:
        return 'f2fs'
    if 'vbmeta' in n or 'dtb' in n:
        return 'raw'
    return 'emmc'
@dataclass
class PartitionInfo:
    name: str
    size_bytes: int
    size_str: str = field(default='', init=True)
    type: str = field(default='', init=True)
    safety: str = field(default='unknown', init=True)
    def __post_init__(self):
        if not self.size_str:
            self.size_str = format_size(self.size_bytes)
        if not self.type:
            self.type = _infer_type(self.name)
        if self.safety == 'unknown':
            self.safety = _classify_safety(self.name)
class PartitionManager:
    def __init__(self, proto: SPDProtocol, progress_cb: Optional[Callable[[int, int], None]]=None, log_cb: Optional[Callable[[str, bool], None]]=None):
        self.proto = proto
        self.progress_cb = progress_cb
        self.log_cb = log_cb
    def _log(self, msg: str, ok: bool=True) -> None:
        log.info(f'[Partition] {msg}')
        if self.log_cb:
            self.log_cb(msg, ok)
    def _progress(self, current: int, total: int) -> None:
        if self.progress_cb:
            self.progress_cb(current, total)
    def list_partitions(self) -> List[PartitionInfo]:
        self._log('Listando particoes...')
        payload = self.proto.send_read_partition_table()
        if payload:
            partitions = self._parse_partition_table(payload)
            if partitions:
                self._log(f'{len(partitions)} particoes encontradas (CMD direto)')
                return partitions
        partitions = self._list_by_gpt_read()
        if partitions:
            return partitions
        return self._list_by_traverse()
    def _parse_partition_table(self, data: bytes) -> List[PartitionInfo]:
        ENTRY_SIZE = 76
        NAME_SIZE = 72
        partitions = []
        if not data or len(data) < ENTRY_SIZE:
            return partitions
        count = len(data) // ENTRY_SIZE
        for i in range(count):
            offset = i * ENTRY_SIZE
            name_raw = data[offset:offset + NAME_SIZE]
            size_raw = data[offset + NAME_SIZE:offset + ENTRY_SIZE]
            name = name_raw.decode('utf-16-le', errors='ignore').rstrip('\x00')
            if name:
                size_bytes = struct.unpack('<I', size_raw)[0]
                partitions.append(PartitionInfo(name=name, size_bytes=size_bytes))
        return partitions
    def _list_by_gpt_read(self) -> List[PartitionInfo]:
        self._log("Tentando ler GPT via 'user_partition'...")
        try:
            ok = self.proto.send_read_start('user_partition', '32K', mode64=False)
            if not ok:
                self._log('READ_START user_partition falhou')
                return []
            gpt_data = b''
            offset = 0
            chunk = 4096
            for _ in range(8):
                read_ok = self.proto.send_read_midst(chunk, offset)
                if not read_ok:
                    break
                resp = self.proto.last_read_data
                if not resp:
                    break
                gpt_data += resp
                offset += chunk
            self.proto._try_read_end()
            if len(gpt_data) < 1024:
                self._log('GPT: dados insuficientes')
                return []
        except Exception as e:
            self._log(f'GPT read falhou: {e}')
            try:
                self.proto._try_read_end()
            except Exception:
                pass
        return self._parse_gpt_entries(gpt_data)
    def _parse_gpt_entries(self, data: bytes) -> List[PartitionInfo]:
        GPT_HEADER_OFFSET = 512
        GPT_SIGNATURE = b'EFI PART'
        GPT_ENTRY_OFFSET = 1024
        GPT_ENTRY_SIZE = 128
        if len(data) < GPT_ENTRY_OFFSET:
            return []
        header = data[GPT_HEADER_OFFSET:GPT_HEADER_OFFSET + 8]
        if header != GPT_SIGNATURE:
            self._log(f'GPT: assinatura invalida: {header!r}')
            return []
        partitions = []
        sector_size = 512
        pos = GPT_ENTRY_OFFSET
        while pos + GPT_ENTRY_SIZE <= len(data):
            entry = data[pos:pos + GPT_ENTRY_SIZE]
            type_guid = entry[:16]
            if type_guid == b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00':
                break
            start_lba = struct.unpack('<Q', entry[32:40])[0]
            end_lba = struct.unpack('<Q', entry[40:48])[0]
            name_raw = entry[56:128]
            try:
                name = name_raw.decode('utf-16-le').rstrip('\x00')
            except Exception:
                name = f'partition_{len(partitions)}'
            if name:
                size_bytes = (end_lba - start_lba + 1) * sector_size
                partitions.append(PartitionInfo(name=name, size_bytes=size_bytes))
            pos += GPT_ENTRY_SIZE
        if partitions:
            self._log(f'{len(partitions)} particoes GPT encontradas')
        return partitions
    def _list_by_traverse(self) -> List[PartitionInfo]:
        self._log('Traverse de particoes comuns...')
        partitions = []
        not_found_streak = 0
        max_streak = 5
        for name in COMMON_PARTITIONS:
            try:
                exists = self.proto.check_partition_exists(name)
                if exists:
                    partitions.append(PartitionInfo(name=name, size_bytes=0))
                    self._log(f'  + {name}')
                    not_found_streak = 0
                else:
                    not_found_streak += 1
            except Exception:
                not_found_streak += 1
            if not not_found_streak >= max_streak:
                continue
            if partitions:
                continue
            self._log('Traverse abortado ÔÇö FDL2 nao suporta READ_START. Use Auth-1.', ok=False)
        self._log(f'Traverse encontrou {len(partitions)} particoes')
        return partitions
    def erase_partition(self, partition: str, size: str='1M') -> bool:
        self._log(f'Apagando: {partition} ({size})')
        ok = self.proto.send_erase_partition(partition, size)
        if not ok:
            self._log(f'Erase falhou: {partition}', ok=False)
        return ok
    def flash_partition(self, partition: str, file_path: str) -> bool:
        if not os.path.exists(file_path):
            self._log(f'Arquivo nao encontrado: {file_path}', ok=False)
            return False
        raw = open(file_path, 'rb').read()
        if len(raw) == 0:
            self._log('Arquivo vazio', ok=False)
            return False
        one_m = str_to_size('1M')
        if len(raw) < one_m:
            data = raw
        else:
            trunc = str_to_size(size_to_str(len(raw)))
            data = raw[:trunc] if trunc > 0 else raw
        self._log(f'Gravando: {partition} ({len(data)} bytes)')
        if not self.proto.send_write_partition_start(partition, len(data)):
            self._log(f'Write START rejeitado: {partition}', ok=False)
            return False
        written = 0
        remaining = len(data)
        while remaining > 0:
            chunk_size = min(PARTITION_CHUNK, remaining)
            chunk = data[written:written + chunk_size]
            if not self.proto.send_midst_data(chunk):
                self._log(f'Write MIDST falhou no offset {written}', ok=False)
                return False
            written += chunk_size
            remaining -= chunk_size
            self._progress(written, len(data))
        if not self.proto.send_end_data():
            self._log(f'Write END rejeitado: {partition}', ok=False)
            return False
        self._log(f'Gravacao OK: {partition}')
        return True
    def read_partition(self, partition: str, size: str, out_path: str) -> bool:
        size_bytes = str_to_size(size)
        self._log(f'Lendo: {partition} ({size})')
        if not self.proto.send_read_start(partition, size):
            self._log(f'Read START rejeitado: {partition}', ok=False)
            return False
        chunk_read = 4096
        with open(out_path, 'wb') as f:
            offset = 0
            while offset < size_bytes:
                to_read = min(chunk_read, size_bytes - offset)
                self.proto.send_read_midst(to_read, offset)
                buf = self.proto.read_buffer
                if buf:
                    f.write(buf)
                    offset += len(buf)
                    self._progress(offset, size_bytes)
                else:
                    break
        self.proto.send_read_end()
        self._log(f'Leitura OK: {partition} ÔåÆ {out_path}')
        return True
    def erase_frp(self) -> bool:
        return self.erase_partition(PARTITION_PERSIST, SIZE_PERSIST_DEFAULT)
    def recovery_command(self, misc_file_path: str) -> bool:
        self.erase_partition(PARTITION_MISC, SIZE_MISC_DEFAULT)
        return self.flash_partition(PARTITION_MISC, misc_file_path)
    def get_partition_size(self, partition: str) -> str:
        if partition != PARTITION_USERDATA:
            ud_size = str_to_size(self.check_partition_size(PARTITION_USERDATA))
            pt_size = str_to_size(self.check_partition_size(partition))
            if ud_size > pt_size:
                return size_to_str(pt_size)
            return '0'
        return self.check_partition_size(PARTITION_USERDATA)
    def check_partition_size(self, partition: str) -> str:
        self._log(f'Detectando tamanho: {partition}')
        if not self.proto.send_read_start(partition, '256G', mode64=True):
            return '0'
        offset = 0
        for i in range(47, 19, -1):
            n64 = offset + ((1 << i) - 1048576)
            self.proto.send_read_midst(4, n64 & 4294967295, n64 >> 32)
            if self.proto.is_read_flash:
                offset = n64 + 1048576
        self.proto.send_read_end()
        result = size_to_str(offset)
        self._log(f"Tamanho de '{partition}': {result}")
        return result
