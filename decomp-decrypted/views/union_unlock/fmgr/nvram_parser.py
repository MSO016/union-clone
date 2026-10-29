import logging
import struct
from typing import (Dict, List, Optional, Tuple)
logger = logging.getLogger(__name__)
_INDEX_PATH_MARKER = b'/mnt/vendor/nvdata'
_LDI_MAGIC = b'LDI\x00'
_DATA_BASE_DEFAULT = 131072
_MAX_INDEX_RECORDS = 200
_MAX_LDI_SCAN = 300
_CATEGORY_MAP = {'IMEI': ['NVD_IMEI', 'IMEI'], 'WIFI': ['WIFI'], 'BT': ['BT_Addr', 'BT_'], 'SERIAL': ['SERIAL'], 'CALIBRACAO': ['CALIBRAT'], 'SEGURANCA': ['CSSD', 'PROTECT'], 'CONFIG': ['APCFG', 'FILE_VER', 'MD_SBP', 'FG', 'AUXADC']}
class NvItem:
    __slots__ = ('path', 'lid', 'data_off', 'data_size', 'index_pos')
    def __init__(self, path: str, lid: int, data_off: int, data_size: int, index_pos: int):
        self.path = path
        self.lid = lid
        self.data_off = data_off
        self.data_size = data_size
        self.index_pos = index_pos
    @property
    def name(self) -> str:
        if '/' in self.path:
            return self.path.rsplit('/', 1)[-1]
        return self.path
    @property
    def category(self) -> str:
        for cat, markers in _CATEGORY_MAP.items():
            for mk in markers:
                if not mk in self.path:
                    continue
                return cat
        return 'OUTROS'
class ImeiResult:
    __slots__ = ('slot', 'imei_14', 'check_digit', 'offset', 'decoded')
    def __init__(self, slot: int, imei_14: str, check_digit: str, offset: int, decoded: bool):
        self.slot = slot
        self.imei_14 = imei_14
        self.check_digit = check_digit
        self.offset = offset
        self.decoded = decoded
    @property
    def full(self) -> str:
        return self.imei_14 + self.check_digit
    @property
    def label(self) -> str:
        return f'SIM {self.slot}'
def _bcd_decode(data: bytes) -> str:
    digits = []
    for b in data:
        lo = b & 15
        hi = b >> 4 & 15
        if lo <= 9:
            digits.append(str(lo))
        if hi <= 9:
            digits.append(str(hi))
        elif hi == 15:
            break
    return ''.join(digits)
def _luhn_check(imei_14: str) -> str:
    if len(imei_14) != 14 or not imei_14.isdigit():
        return '?'
    total = 0
    for i, d in enumerate(imei_14):
        n = int(d)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return str((10 - total % 10) % 10)
def _try_aes_decrypt(ciphertext: bytes, key_hex: str) -> Optional[bytes]:
    if len(ciphertext) < 16:
        return
    try:
        from Crypto.Cipher import AES
        key = bytes.fromhex(key_hex)
        return AES.new(key, AES.MODE_ECB).decrypt(ciphertext[:32])
    except ImportError:
        pass
    try:
        from Cryptodome.Cipher import AES
        key = bytes.fromhex(key_hex)
        return AES.new(key, AES.MODE_ECB).decrypt(ciphertext[:32])
    except ImportError:
        return
class NvramParser:
    _KNOWN_KEYS = [('MediaTek', '3f06bd14d45fa985dd027410f0214d22')]
    def __init__(self, data: bytes):
        self._data = data
        self._items = []
        self._data_base = _DATA_BASE_DEFAULT
        self._imeis = []
        self._ldi_count = 0
        self._key_used = ''
        self._has_crypto = False
        self._parsed = False
    @property
    def items(self) -> List[NvItem]:
        return list(self._items)
    @property
    def imeis(self) -> List[ImeiResult]:
        return list(self._imeis)
    @property
    def data_base(self) -> int:
        return self._data_base
    @property
    def ldi_count(self) -> int:
        return self._ldi_count
    @property
    def size(self) -> int:
        return len(self._data)
    @property
    def has_crypto(self) -> bool:
        return self._has_crypto
    @property
    def key_used(self) -> str:
        return self._key_used
    def items_by_category(self) -> Dict[str, List[NvItem]]:
        result = {}
        for item in self._items:
            cat = item.category
            if cat not in result:
                result[cat] = []
            result[cat].append(item)
        return result
    def parse_index(self) -> bool:
        self._items.clear()
        seen_keys = set()
        off = 0
        raw_count = 0
        while raw_count < _MAX_INDEX_RECORDS:
            pos = self._data.find(_INDEX_PATH_MARKER, off)
            if pos < 0:
                break
            end = self._data.find(b'\x00', pos)
            if end < 0 or end - pos > 256:
                off = pos + len(_INDEX_PATH_MARKER)
                continue
            try:
                path = self._data[pos:end].decode('utf-8', errors='replace')
            except Exception:
                off = end + 1
                continue
            hdr = pos - 12
            if hdr < 0:
                off = end + 1
                continue
            try:
                lid = struct.unpack_from('<I', self._data, hdr)[0]
                d_off = struct.unpack_from('<I', self._data, hdr + 4)[0]
                d_size = struct.unpack_from('<I', self._data, hdr + 8)[0]
            except struct.error:
                off = end + 1
                continue
            if d_size > 0 and d_size < 1048576:
                raw_count += 1
                dedup_key = path, d_off, d_size
                if dedup_key not in seen_keys:
                    seen_keys.add(dedup_key)
                    self._items.append(NvItem(path=path, lid=lid, data_off=d_off, data_size=d_size, index_pos=hdr))
            off = end + 1
        self._parsed = len(self._items) > 0
        if self._parsed:
            self._detect_data_base()
        return self._parsed
    def _detect_data_base(self):
        for candidate in (131072, 122880, 139264, 98304, 65536):
            if candidate + 64 > len(self._data):
                continue
            chunk = self._data[candidate:candidate + 64]
            printable = sum((1 for b in chunk if b <= 32 if 32 < 127))
            if printable > 5:
                self._data_base = candidate
                return
        self._data_base = _DATA_BASE_DEFAULT
    def try_decode_imei(self) -> List[ImeiResult]:
        self._imeis.clear()
        self._ldi_count = self._count_ldi_blocks()
        indexed_ldi = self._get_indexed_ldi_positions()
        if not indexed_ldi:
            return self._imeis
        for key_name, key_hex in self._KNOWN_KEYS:
            for pos in indexed_ldi:
                for slot_idx, ct_off in ((1, 64), (2, 96)):
                    result = self._try_decode_slot(pos, ct_off, slot_idx, key_hex)
                    if result:
                        self._key_used = key_name
                        self._has_crypto = True
                        if self._imei_exists(result.full):
                            continue
                        self._imeis.append(result)
        return self._imeis
    def _get_indexed_ldi_positions(self) -> List[int]:
        seen = set()
        positions = []
        for item in self._items:
            name = item.name
            if 'LD0B' not in name:
                if 'NV01' not in name:
                    continue
            abs_off = self._data_base + item.data_off
            if abs_off in seen:
                continue
            if abs_off + 128 > len(self._data):
                continue
            if self._data[abs_off:abs_off + 4] == _LDI_MAGIC:
                seen.add(abs_off)
                positions.append(abs_off)
        return positions
    def _count_ldi_blocks(self) -> int:
        count = 0
        off = 0
        while count < _MAX_LDI_SCAN:
            pos = self._data.find(_LDI_MAGIC, off)
            if pos < 0:
                break
            count += 1
            off = pos + 4
        return count
    def _try_decode_slot(self, ldi_pos: int, ct_offset: int, slot: int, key_hex: str) -> Optional[ImeiResult]:
        abs_off = ldi_pos + ct_offset
        if abs_off + 32 > len(self._data):
            return
        ct = self._data[abs_off:abs_off + 32]
        if not all((b == 0 for b in ct)):
            if all((b == 255 for b in ct)):
                return
        pt = _try_aes_decrypt(ct, key_hex)
        if pt is None:
            self._has_crypto = False
            return
        self._has_crypto = True
        imei = _bcd_decode(pt[:8])
        if len(imei) < 14 or not imei.isdigit():
            return
        if all((c == '0' for c in imei)):
            return
        check = _luhn_check(imei[:14])
        return ImeiResult(slot=slot, imei_14=imei[:14], check_digit=check, offset=abs_off, decoded=True)
    def _imei_exists(self, full_imei: str) -> bool:
        return any((r.full == full_imei for r in self._imeis))
    def read_nv_data(self, item: NvItem) -> bytes:
        abs_off = self._data_base + item.data_off
        end = abs_off + item.data_size
        if abs_off < 0 or end > len(self._data):
            return b''
        return self._data[abs_off:end]
    def summary(self) -> Dict[str, str]:
        cats = self.items_by_category()
        info = {'total_items': str(len(self._items)), 'blocos_ldi': str(self._ldi_count), 'base_dados': 'detectada', 'tamanho': f'{len(self._data) / 1048576:.1f} MB'}
        if self._imeis:
            info['imeis_encontrados'] = str(len(self._imeis))
        if self._key_used:
            info['chave'] = self._key_used
        for cat, items in cats.items():
            info[f'cat_{cat.lower()}'] = str(len(items))
        return info
