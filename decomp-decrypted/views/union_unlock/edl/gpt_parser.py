import struct
from pathlib import Path
from typing import (List, Dict, Optional)
_GPT_SIGNATURE = b'EFI PART'
_GPT_HEADER_FMT = '<8sIIIIQQQQ16sQIII'
_GPT_HEADER_SIZE = struct.calcsize(_GPT_HEADER_FMT)
_ENTRY_FMT = '<16s16sQQQ72s'
_ENTRY_SIZE = struct.calcsize(_ENTRY_FMT)
_PARTITIONS_UNSAFE = frozenset({'tz', 'aop', 'hyp', 'rpm', 'xbl', 'pmic', 'sbl1', 'sbl2', 'sbl3', 'shrm', 'uefi', 'aboot', 'qupfw', 'cmnlib', 'devcfg', 'imagefv', 'cmnlib64', 'keymaster', 'uefisecapp', 'xbl_config', 'multiimgoem'})
_PARTITIONS_SAFE_ERASE = frozenset({'frp', 'config', 'persistent'})
_PARTITIONS_CAUTION_ERASE = frozenset({'misc', 'cache', 'userdata'})
def _decode_utf16le_name(raw: bytes) -> str:
    try:
        name = raw.decode('utf-16-le').rstrip('\x00').strip()
    except UnicodeDecodeError:
        name = ''
    return name
    return name
def parse_gpt(data: bytes, sector_size: int=512) -> Dict:
    result = {'header': {}, 'partitions': [], 'sector_size': sector_size, 'error': None}
    if sector_size < 512:
        _fallback = 512
        if len(data) >= _fallback + _GPT_HEADER_SIZE and data[_fallback:_fallback + 8] == _GPT_SIGNATURE:
            sector_size = _fallback
            result['sector_size'] = _fallback
        if sector_size < 512:
            _fallback = 4096
            if len(data) >= _fallback + _GPT_HEADER_SIZE and data[_fallback:_fallback + 8] == _GPT_SIGNATURE:
                sector_size = _fallback
                result['sector_size'] = _fallback
    if len(data) < sector_size * 2:
        result['error'] = 'Arquivo muito pequeno para conter GPT'
        return result
    gpt_offset = sector_size
    if len(data) < gpt_offset + _GPT_HEADER_SIZE:
        result['error'] = 'Dados insuficientes para header GPT'
        return result
    hdr_data = data[gpt_offset:gpt_offset + _GPT_HEADER_SIZE]
    try:
        hdr = struct.unpack(_GPT_HEADER_FMT, hdr_data)
    except struct.error as e:
        result['error'] = f'Erro ao parsear header: {e}'
        return result
    signature = hdr[0]
    if signature != _GPT_SIGNATURE:
        result['error'] = f'Assinatura GPT invalida: {signature!r} (esperado: {_GPT_SIGNATURE!r})'
        return result
    revision = hdr[1]
    header_size = hdr[2]
    current_lba = hdr[5]
    backup_lba = hdr[6]
    first_usable = hdr[7]
    last_usable = hdr[8]
    disk_guid = hdr[9]
    entry_start_lba = hdr[10]
    num_entries = hdr[11]
    entry_size = hdr[12]
    result['header'] = {'revision': revision, 'header_size': header_size, 'current_lba': current_lba, 'backup_lba': backup_lba, 'first_usable_lba': first_usable, 'last_usable_lba': last_usable, 'entry_start_lba': entry_start_lba, 'num_entries': num_entries, 'entry_size': entry_size}
    entry_offset = entry_start_lba * sector_size
    actual_entry_size = max(entry_size, _ENTRY_SIZE)
    for i in range(num_entries):
        ofs = entry_offset + i * actual_entry_size
        if ofs + _ENTRY_SIZE > len(data):
            return result
        entry_data = data[ofs:ofs + _ENTRY_SIZE]
        try:
            entry = struct.unpack(_ENTRY_FMT, entry_data)
        except struct.error:
            continue
        first_lba = entry[2]
        last_lba = entry[3]
        if first_lba == 0:
            if last_lba == 0:
                continue
        name = _decode_utf16le_name(entry[5])
        if name:
            num_sectors = last_lba - first_lba + 1
            size_bytes = num_sectors * sector_size
            name_lower = name.lower()
            if name_lower in _PARTITIONS_UNSAFE:
                safety = 'critical'
            elif name_lower in _PARTITIONS_SAFE_ERASE:
                safety = 'safe'
            elif name_lower in _PARTITIONS_CAUTION_ERASE:
                safety = 'caution'
            else:
                safety = 'unknown'
            result['partitions'].append({'name': name, 'start_lba': first_lba, 'end_lba': last_lba, 'num_sectors': num_sectors, 'size_bytes': size_bytes, 'size_human': _human_size(size_bytes), 'safety': safety})
    return result
def _human_size(nbytes: int) -> str:
    if nbytes < 1024:
        return f'{nbytes} B'
    if nbytes < 1048576:
        return f'{nbytes / 1024:.1f} KB'
    if nbytes < 1073741824:
        return f'{nbytes / 1048576:.1f} MB'
    return f'{nbytes / 1073741824:.2f} GB'
def parse_gpt_file(filepath: str, sector_size: int=512) -> Dict:
    p = Path(filepath)
    if not p.exists():
        return {'header': {}, 'partitions': [], 'sector_size': sector_size, 'error': f'Arquivo nao encontrado: {filepath}'}
    data = p.read_bytes()
    return parse_gpt(data, sector_size)
def is_safe_to_erase(partition_name: str) -> bool:
    return partition_name.lower() in _PARTITIONS_SAFE_ERASE
def is_critical(partition_name: str) -> bool:
    return partition_name.lower() in _PARTITIONS_UNSAFE
