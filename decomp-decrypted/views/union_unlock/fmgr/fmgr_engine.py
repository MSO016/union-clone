import logging
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from typing import (Callable, Dict, List, Optional, Tuple)
from ._fmgr_core import (BIN_EXT4_DLL, BIN_EXT4_EXE, FS_EXT4, FS_EROFS, FS_NVRAM, FS_RAW, FS_SPARSE, FS_NAMES, detect_filesystem, find_winfsp_bin, format_size, octal_permissions, resolve_bin)
logger = logging.getLogger(__name__)
_CREATE_NO_WINDOW = 134217728 if sys.platform == 'win32' else 0
class EntryInfo:
    __slots__ = ('name', 'path', 'is_dir', 'size', 'mode', 'uid', 'gid', 'mtime', 'inode', 'ftype')
    def __init__(self, name='', path='/', is_dir=False, size=0, mode=0, uid=0, gid=0, mtime=0, inode=0, ftype=1):
        self.name = name
        self.path = path
        self.is_dir = is_dir
        self.size = size
        self.mode = mode
        self.uid = uid
        self.gid = gid
        self.mtime = mtime
        self.inode = inode
        self.ftype = ftype
    @property
    def permissions(self) -> str:
        try:
            return stat.filemode(self.mode)
        except Exception:
            return octal_permissions(self.mode)
    @property
    def size_str(self) -> str:
        return format_size(self.size)
    @property
    def mtime_str(self) -> str:
        if self.mtime <= 0:
            return '-'
        try:
            return datetime.fromtimestamp(self.mtime).strftime('%Y-%m-%d %H:%M')
        except Exception:
            return '-'
class Ext4Reader:
    def __init__(self, img_path: str):
        self._path = img_path
        self._fh = None
        self._vol = None
    def open(self) -> bool:
        try:
            import ext4 as ext4lib
            self._fh = open(self._path, 'rb')
            self._vol = ext4lib.Volume(self._fh)
            return True
        except Exception as e:
            logger.error('Falha ao abrir imagem')
            return False
    def close(self):
        if self._fh:
            try:
                self._fh.close()
            except Exception:
                pass
            self._fh = None
            self._vol = None
    def list_dir(self, dir_path: str='/') -> List[EntryInfo]:
        if not self._vol:
            return []
        entries = []
        try:
            inode = self._vol.root if dir_path == '/' else self._vol.inode_at(dir_path)
            for de, ft in inode.opendir():
                pass
            try:
                name = de.name_bytes.decode('utf-8', errors='replace')
            except Exception:
                name = de.name
                if isinstance(name, bytes):
                    name = name.decode('utf-8', errors='replace')
            else:
                name = name.rstrip('\x00')
                if name in ('.', '..'):
                    pass
                child_path = dir_path.rstrip('/') + '/' + name
                is_dir = ft == 2
                size = 0
                mode = 0
                uid = gid = mtime = inode_num = 0
        except Exception as e:
            logger.error('Falha ao listar diretorio')
        return entries
    def read_file(self, file_path: str) -> bytes:
        if not self._vol:
            return b''
        try:
            inode = self._vol.inode_at(file_path)
            reader = inode._open('rb')
            data = reader.read()
            reader.close()
            return data
        except Exception as e:
            logger.error('Falha ao ler arquivo')
            return b''
    def get_info(self, path: str) -> Optional[EntryInfo]:
        if not self._vol:
            return
        try:
            inode = self._vol.inode_at(path)
            name = path.rsplit('/', 1)[-1] or '/'
            is_dir = bool(getattr(inode, 'i_mode', 0) & 16384)
            return EntryInfo(name=name, path=path, is_dir=is_dir, size=getattr(inode, 'i_size_lo', 0), mode=getattr(inode, 'i_mode', 0), uid=getattr(inode, 'i_uid', 0), gid=getattr(inode, 'i_gid', 0), mtime=getattr(inode, 'i_mtime', 0))
        except Exception:
            return
    def volume_info(self) -> Dict[str, str]:
        if not self._vol:
            return {}
        info = {}
        try:
            sb = self._vol.superblock
            vol_name = getattr(sb, 's_volume_name', None)
            if vol_name is not None:
                pass
            try:
                info['label'] = bytes(vol_name).decode('utf-8', errors='replace').rstrip('\x00') or '(sem label)'
            except Exception:
                info['label'] = '(sem label)'
            else:
                uuid_obj = getattr(self._vol, 'uuid', None)
                if uuid_obj:
                    info['uuid'] = str(uuid_obj)
                else:
                    uuid_raw = getattr(sb, 's_uuid', None)
                    if uuid_raw:
                        info['uuid'] = bytes(uuid_raw).hex()
                log_bs = getattr(sb, 's_log_block_size', 0)
                bs = 1024 << log_bs
                info['block_size'] = str(bs)
                total = getattr(sb, 's_blocks_count_lo', 0)
                free = getattr(sb, 's_free_blocks_count_lo', 0)
                info['total'] = format_size(total * bs)
                info['free'] = format_size(free * bs)
                info['used'] = format_size((total - free) * bs)
                last_mount = getattr(sb, 's_last_mounted', None)
                if last_mount:
                    pass
        except Exception as e:
            logger.error('Falha ao ler informacoes do volume')
        return info
class Ext4Writer:
    _SENSITIVE_TERMS = ['ext4_x64.dll', 'ext4.exe', '.dll', '.exe', 'DLL', 'CDLL', 'ctypes', 'winfsp', 'WinFsp', 'subprocess', 'worker', 'mount']
    def __init__(self, img_path: str):
        self._path = img_path
    @classmethod
    def _sanitize_error(cls, msg: str) -> str:
        sanitized = msg
        for term in cls._SENSITIVE_TERMS:
            if term in sanitized:
                sanitized = sanitized.replace(term, '***')
        if len(sanitized) > 120:
            sanitized = sanitized[:120]
        return sanitized or 'Operacao falhou'
    def write_file(self, dest_path: str, data: bytes) -> Tuple[bool, str]:
        ok, msg = self._write_via_dll(dest_path, data)
        if ok:
            return True, msg
        logger.warning('Tentando via alternativo...')
        return self._write_via_mount(dest_path, data)
    def delete_file(self, file_path: str, is_dir: bool=False) -> Tuple[bool, str]:
        ok, msg = self._delete_via_dll(file_path, is_dir=is_dir)
        if ok:
            return True, msg
        return self._delete_via_mount(file_path)
    def mkdir(self, dir_path: str) -> Tuple[bool, str]:
        ok, msg = self._mkdir_via_dll(dir_path)
        if ok:
            return True, msg
        return self._mkdir_via_mount(dir_path)
    def rename(self, old_path: str, new_path: str) -> Tuple[bool, str]:
        ok, msg = self._rename_via_dll(old_path, new_path)
        if ok:
            return True, msg
        return self._rename_via_mount(old_path, new_path)
    def chmod(self, path: str, mode: int) -> Tuple[bool, str]:
        return self._run_dll_worker('chmod', target_path=path, mode=mode)
    def chown(self, path: str, uid: int, gid: int) -> Tuple[bool, str]:
        return self._run_dll_worker('chown', target_path=path, uid=uid, gid=gid)
    def _run_dll_worker(self, operation: str, **kwargs) -> Tuple[bool, str]:
        dll = resolve_bin(BIN_EXT4_DLL)
        if not os.path.isfile(dll):
            return (False, 'Motor de escrita nao encontrado. Acesse Configuracoes > Dependencias para instalar.')
        worker_code = self._build_worker(operation, **kwargs)
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8')
        tmp.write(worker_code)
        tmp.close()
        try:
            result = subprocess.run([sys.executable, tmp.name], capture_output=True, text=True, timeout=30, creationflags=_CREATE_NO_WINDOW)
            if result.returncode == 0:
                pass
            try:
                os.unlink(tmp.name)
            except Exception:
                return (True, 'OK')
            else:
                return (True, 'OK')
        except subprocess.TimeoutExpired:
            try:
                os.unlink(tmp.name)
                return (False, 'Timeout na operacao')
            except Exception:
                return (False, 'Timeout na operacao')
        try:
            os.unlink(tmp.name)
            return False, self._sanitize_error(result.stderr.strip() or f'codigo={result.returncode}')
        except Exception:
            return
        try:
            os.unlink(tmp.name)
            return (False, 'Timeout na operacao')
        except Exception:
            return (False, 'Timeout na operacao')
    def _build_worker(self, operation: str, **kw) -> str:
        dll_path = resolve_bin(BIN_EXT4_DLL).replace('\\', '\\\\')
        img_path = self._path.replace('\\', '\\\\')
        if operation == 'write':
            data_hex = kw['data'].hex()
            dest = kw['dest_path']
            return f'\nimport ctypes, ctypes.wintypes as wt, os, sys, struct\n\n_fh = None\n_bs = 512\n\ndef _open_cb(bdev): return 0\ndef _close_cb(bdev): return 0\ndef _lock_cb(bdev): return 0\n\ndef _bread_cb(bdev, buf, blk_id, blk_cnt):\n    global _fh, _bs\n    _fh.seek(blk_id * _bs)\n    data = _fh.read(blk_cnt * _bs)\n    ctypes.memmove(buf, data, len(data))\n    return 0\n\ndef _bwrite_cb(bdev, buf, blk_id, blk_cnt):\n    global _fh, _bs\n    _fh.seek(blk_id * _bs)\n    data = (ctypes.c_uint8 * (blk_cnt * _bs)).from_address(buf)\n    _fh.write(bytes(data))\n    _fh.flush()\n    return 0\n\nOPEN_T = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p)\nBREAD_T = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint64, ctypes.c_uint32)\nBWRITE_T = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint64, ctypes.c_uint32)\nCLOSE_T = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p)\nLOCK_T = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p)\n\nclass Iface(ctypes.Structure):\n    _fields_ = [\n        ("open", OPEN_T), ("bread", BREAD_T), ("bwrite", BWRITE_T),\n        ("close", CLOSE_T), ("lock", LOCK_T), ("unlock", LOCK_T),\n        ("ph_bsize", ctypes.c_uint32), ("ph_bcnt", ctypes.c_uint64),\n        ("ph_bbuf", ctypes.c_void_p), ("ph_refctr", ctypes.c_uint32),\n        ("bread_ctr", ctypes.c_uint32), ("bwrite_ctr", ctypes.c_uint32),\n        ("p_user", ctypes.c_void_p),\n    ]\n\nclass BDev(ctypes.Structure):\n    _fields_ = [\n        ("bdif", ctypes.POINTER(Iface)), ("part_offset", ctypes.c_uint64),\n        ("part_size", ctypes.c_uint64), ("bc", ctypes.c_void_p),\n        ("lg_bsize", ctypes.c_uint32), ("lg_bcnt", ctypes.c_uint64),\n        ("cache_write_back", ctypes.c_uint32), ("fs_type", ctypes.c_uint32),\n        ("journal", ctypes.c_void_p), ("flags", ctypes.c_uint32),\n    ]\n\nclass EF(ctypes.Structure):\n    _fields_ = [("mp", ctypes.c_char * 32), ("inode", ctypes.c_uint32),\n                ("flags", ctypes.c_uint32), ("fsize", ctypes.c_uint64),\n                ("fpos", ctypes.c_uint64)]\n\ncb_open = OPEN_T(_open_cb)\ncb_bread = BREAD_T(_bread_cb)\ncb_bwrite = BWRITE_T(_bwrite_cb)\ncb_close = CLOSE_T(_close_cb)\ncb_lock = LOCK_T(_lock_cb)\n\niface = Iface()\niface.open = cb_open\niface.bread = cb_bread\niface.bwrite = cb_bwrite\niface.close = cb_close\niface.lock = cb_lock\niface.unlock = cb_lock\n\n_fh = open(r"{img_path}", "r+b")\nfs = os.path.getsize(r"{img_path}")\niface.ph_bsize = _bs\niface.ph_bcnt = fs // _bs\n\nbdev = BDev()\nbdev.bdif = ctypes.pointer(iface)\nbdev.part_size = fs\n\ndll = ctypes.CDLL(r"{dll_path}")\ndev_name = b"ext4_dev"\nmp = b"/mp/"\n\ndll.ext4_device_register.argtypes = [ctypes.POINTER(BDev), ctypes.c_char_p]\ndll.ext4_device_register.restype = ctypes.c_int\ndll.ext4_mount.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_bool]\ndll.ext4_mount.restype = ctypes.c_int\ndll.ext4_umount.argtypes = [ctypes.c_char_p]\ndll.ext4_umount.restype = ctypes.c_int\ndll.ext4_recover.argtypes = [ctypes.c_char_p]\ndll.ext4_recover.restype = ctypes.c_int\ndll.ext4_journal_start.argtypes = [ctypes.c_char_p]\ndll.ext4_journal_start.restype = ctypes.c_int\ndll.ext4_journal_stop.argtypes = [ctypes.c_char_p]\ndll.ext4_journal_stop.restype = ctypes.c_int\ndll.ext4_fopen.argtypes = [ctypes.POINTER(EF), ctypes.c_char_p, ctypes.c_char_p]\ndll.ext4_fopen.restype = ctypes.c_int\ndll.ext4_fwrite.argtypes = [ctypes.POINTER(EF), ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]\ndll.ext4_fwrite.restype = ctypes.c_int\ndll.ext4_fclose.argtypes = [ctypes.POINTER(EF)]\ndll.ext4_fclose.restype = ctypes.c_int\ndll.ext4_fremove.argtypes = [ctypes.c_char_p]\ndll.ext4_fremove.restype = ctypes.c_int\ndll.ext4_dir_mk.argtypes = [ctypes.c_char_p]\ndll.ext4_dir_mk.restype = ctypes.c_int\ndll.ext4_dir_rm.argtypes = [ctypes.c_char_p]\ndll.ext4_dir_rm.restype = ctypes.c_int\ndll.ext4_frename.argtypes = [ctypes.c_char_p, ctypes.c_char_p]\ndll.ext4_frename.restype = ctypes.c_int\n\nrc = dll.ext4_device_register(ctypes.pointer(bdev), dev_name)\nif rc != 0: print(f"register err {{rc}}", file=sys.stderr); os._exit(1)\n\nrc = dll.ext4_mount(dev_name, mp, False)\nif rc != 0: print(f"mount err {{rc}}", file=sys.stderr); os._exit(1)\n\ndll.ext4_recover(mp)\ndll.ext4_journal_start(mp)\n\nfull = mp + b"{dest.lstrip('/').encode().decode()}"\nef = EF()\nrc = dll.ext4_fopen(ctypes.pointer(ef), full, b"wb")\nif rc != 0: print(f"fopen err {{rc}}", file=sys.stderr); os._exit(1)\n\npayload = bytes.fromhex("{data_hex}")\nwritten = ctypes.c_size_t(0)\nrc = dll.ext4_fwrite(ctypes.pointer(ef), payload, len(payload), ctypes.pointer(written))\nif rc != 0: print(f"fwrite err {{rc}}", file=sys.stderr); os._exit(1)\n\ndll.ext4_fclose(ctypes.pointer(ef))\ndll.ext4_journal_stop(mp)\ndll.ext4_umount(mp)\n_fh.close()\nprint(f"OK written={{written.value}}")\nos._exit(0)\n'
        if operation == 'delete':
            target = kw['target_path']
            is_dir = kw.get('is_dir', False)
            func = 'ext4_dir_rm' if is_dir else 'ext4_fremove'
            return self._build_simple_op(func, target)
        if operation == 'mkdir':
            return self._build_simple_op('ext4_dir_mk', kw['dir_path'])
        if operation == 'rename':
            old = kw['old_path']
            new = kw['new_path']
            return f'\nimport ctypes, ctypes.wintypes as wt, os, sys, struct\n{self._worker_common_code()}\ndll.ext4_frename.argtypes = [ctypes.c_char_p, ctypes.c_char_p]\ndll.ext4_frename.restype = ctypes.c_int\nfull_old = mp + b"{old.lstrip('/')}"\nfull_new = mp + b"{new.lstrip('/')}"\nrc = dll.ext4_frename(full_old, full_new)\nif rc != 0: print(f"rename err {{rc}}", file=sys.stderr); os._exit(1)\ndll.ext4_journal_stop(mp)\ndll.ext4_umount(mp)\n_fh.close()\nprint("OK renamed")\nos._exit(0)\n'
        if operation == 'chmod':
            target = kw['target_path']
            mode = kw['mode']
            return f'\nimport ctypes, ctypes.wintypes as wt, os, sys, struct\n{self._worker_common_code()}\ndll.ext4_mode_set.argtypes = [ctypes.c_char_p, ctypes.c_uint32]\ndll.ext4_mode_set.restype = ctypes.c_int\nfull = mp + b"{target.lstrip('/')}"\nrc = dll.ext4_mode_set(full, {mode})\nif rc != 0: print(f"chmod err {{rc}}", file=sys.stderr); os._exit(1)\ndll.ext4_journal_stop(mp)\ndll.ext4_umount(mp)\n_fh.close()\nprint("OK chmod")\nos._exit(0)\n'
        if operation == 'chown':
            target = kw['target_path']
            uid = kw['uid']
            gid = kw['gid']
            return f'\nimport ctypes, ctypes.wintypes as wt, os, sys, struct\n{self._worker_common_code()}\ndll.ext4_owner_set.argtypes = [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_uint32]\ndll.ext4_owner_set.restype = ctypes.c_int\nfull = mp + b"{target.lstrip('/')}"\nrc = dll.ext4_owner_set(full, {uid}, {gid})\nif rc != 0: print(f"chown err {{rc}}", file=sys.stderr); os._exit(1)\ndll.ext4_journal_stop(mp)\ndll.ext4_umount(mp)\n_fh.close()\nprint("OK chown")\nos._exit(0)\n'
        return ''
    def _build_simple_op(self, func_name: str, target_path: str) -> str:
        dll_path = resolve_bin(BIN_EXT4_DLL).replace('\\', '\\\\')
        img_path = self._path.replace('\\', '\\\\')
        return f'\nimport ctypes, ctypes.wintypes as wt, os, sys, struct\n{self._worker_common_code()}\ndll.{func_name}.argtypes = [ctypes.c_char_p]\ndll.{func_name}.restype = ctypes.c_int\nfull = mp + b"{target_path.lstrip('/')}"\nrc = dll.{func_name}(full)\nif rc != 0: print(f"{func_name} err {{rc}}", file=sys.stderr); os._exit(1)\ndll.ext4_journal_stop(mp)\ndll.ext4_umount(mp)\n_fh.close()\nprint("OK {func_name}")\nos._exit(0)\n'
    def _worker_common_code(self) -> str:
        dll_path = resolve_bin(BIN_EXT4_DLL).replace('\\', '\\\\')
        img_path = self._path.replace('\\', '\\\\')
        return f'\n_fh = None; _bs = 512\ndef _open_cb(bdev): return 0\ndef _close_cb(bdev): return 0\ndef _lock_cb(bdev): return 0\ndef _bread_cb(bdev, buf, blk_id, blk_cnt):\n    global _fh, _bs\n    _fh.seek(blk_id * _bs); data = _fh.read(blk_cnt * _bs)\n    ctypes.memmove(buf, data, len(data)); return 0\ndef _bwrite_cb(bdev, buf, blk_id, blk_cnt):\n    global _fh, _bs\n    _fh.seek(blk_id * _bs)\n    data = (ctypes.c_uint8 * (blk_cnt * _bs)).from_address(buf)\n    _fh.write(bytes(data)); _fh.flush(); return 0\nOPEN_T = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p)\nBREAD_T = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint64, ctypes.c_uint32)\nBWRITE_T = BREAD_T; CLOSE_T = OPEN_T; LOCK_T = OPEN_T\nclass Iface(ctypes.Structure):\n    _fields_ = [("open", OPEN_T), ("bread", BREAD_T), ("bwrite", BWRITE_T),\n        ("close", CLOSE_T), ("lock", LOCK_T), ("unlock", LOCK_T),\n        ("ph_bsize", ctypes.c_uint32), ("ph_bcnt", ctypes.c_uint64),\n        ("ph_bbuf", ctypes.c_void_p), ("ph_refctr", ctypes.c_uint32),\n        ("bread_ctr", ctypes.c_uint32), ("bwrite_ctr", ctypes.c_uint32),\n        ("p_user", ctypes.c_void_p)]\nclass BDev(ctypes.Structure):\n    _fields_ = [("bdif", ctypes.POINTER(Iface)), ("part_offset", ctypes.c_uint64),\n        ("part_size", ctypes.c_uint64), ("bc", ctypes.c_void_p),\n        ("lg_bsize", ctypes.c_uint32), ("lg_bcnt", ctypes.c_uint64),\n        ("cache_write_back", ctypes.c_uint32), ("fs_type", ctypes.c_uint32),\n        ("journal", ctypes.c_void_p), ("flags", ctypes.c_uint32)]\ncb_open = OPEN_T(_open_cb); cb_bread = BREAD_T(_bread_cb)\ncb_bwrite = BWRITE_T(_bwrite_cb); cb_close = CLOSE_T(_close_cb)\ncb_lock = LOCK_T(_lock_cb)\niface = Iface()\niface.open = cb_open; iface.bread = cb_bread; iface.bwrite = cb_bwrite\niface.close = cb_close; iface.lock = cb_lock; iface.unlock = cb_lock\n_fh = open(r"{img_path}", "r+b")\nfs = os.path.getsize(r"{img_path}")\niface.ph_bsize = _bs; iface.ph_bcnt = fs // _bs\nbdev = BDev(); bdev.bdif = ctypes.pointer(iface); bdev.part_size = fs\ndll = ctypes.CDLL(r"{dll_path}")\ndev_name = b"ext4_dev"; mp = b"/mp/"\ndll.ext4_device_register.argtypes = [ctypes.POINTER(BDev), ctypes.c_char_p]\ndll.ext4_device_register.restype = ctypes.c_int\ndll.ext4_mount.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_bool]\ndll.ext4_mount.restype = ctypes.c_int\ndll.ext4_umount.argtypes = [ctypes.c_char_p]; dll.ext4_umount.restype = ctypes.c_int\ndll.ext4_recover.argtypes = [ctypes.c_char_p]; dll.ext4_recover.restype = ctypes.c_int\ndll.ext4_journal_start.argtypes = [ctypes.c_char_p]; dll.ext4_journal_start.restype = ctypes.c_int\ndll.ext4_journal_stop.argtypes = [ctypes.c_char_p]; dll.ext4_journal_stop.restype = ctypes.c_int\nrc = dll.ext4_device_register(ctypes.pointer(bdev), dev_name)\nif rc != 0: print(f"register err {{rc}}", file=sys.stderr); os._exit(1)\nrc = dll.ext4_mount(dev_name, mp, False)\nif rc != 0: print(f"mount err {{rc}}", file=sys.stderr); os._exit(1)\ndll.ext4_recover(mp); dll.ext4_journal_start(mp)\n'
    def _write_via_dll(self, dest_path: str, data: bytes) -> Tuple[bool, str]:
        return self._run_dll_worker('write', dest_path=dest_path, data=data)
    def _delete_via_dll(self, path: str, is_dir: bool=False) -> Tuple[bool, str]:
        return self._run_dll_worker('delete', target_path=path, is_dir=is_dir)
    def _mkdir_via_dll(self, path: str) -> Tuple[bool, str]:
        return self._run_dll_worker('mkdir', dir_path=path)
    def _rename_via_dll(self, old: str, new: str) -> Tuple[bool, str]:
        return self._run_dll_worker('rename', old_path=old, new_path=new)
    def _mount_and_do(self, callback) -> Tuple[bool, str]:
        ext4_exe = resolve_bin(BIN_EXT4_EXE)
        if not os.path.isfile(ext4_exe):
            return (False, 'Servico de escrita indisponivel. Acesse Configuracoes > Dependencias para instalar.')
        winfsp = find_winfsp_bin()
        if not winfsp:
            return (False, 'Componente auxiliar necessario para escrita nao encontrado. Acesse Configuracoes > Dependencias para instalar.')
        env = os.environ.copy()
        env['PATH'] = f'{winfsp};{env.get('PATH', '')}'
        letters = [f'{chr(c)}:' for c in range(ord('Z'), ord('M'), -1)]
        drive = None
        for l in letters:
            if os.path.exists(l + '\\'):
                continue
            drive = l
            break
        if not drive:
            return (False, 'Recurso de sistema indisponivel. Feche outros programas.')
        proc = subprocess.Popen([ext4_exe, 'mount', self._path, '--drive', drive], env=env, creationflags=_CREATE_NO_WINDOW)
        try:
            for _ in range(100):
                if os.path.exists(drive + '\\'):
                    break
                time.sleep(0.1)
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
                return (False, 'Tempo limite excedido. Tente novamente.')
            else:
                return (False, 'Tempo limite excedido. Tente novamente.')
        except Exception as e:
            pass
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
            return
        return callback(drive)
    def _write_via_mount(self, dest_path: str, data: bytes) -> Tuple[bool, str]:
        def _do(drive):
            target = os.path.join(drive + '\\', dest_path.lstrip('/'))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, 'wb') as fh:
                fh.write(data)
            return (True, 'OK')
        return self._mount_and_do(_do)
    def _delete_via_mount(self, path: str) -> Tuple[bool, str]:
        def _do(drive):
            target = os.path.join(drive + '\\', path.lstrip('/'))
            if os.path.isdir(target):
                shutil.rmtree(target)
                return (True, 'OK')
            if os.path.isfile(target):
                os.remove(target)
            return (True, 'OK')
        return self._mount_and_do(_do)
    def _mkdir_via_mount(self, path: str) -> Tuple[bool, str]:
        def _do(drive):
            target = os.path.join(drive + '\\', path.lstrip('/'))
            os.makedirs(target, exist_ok=True)
            return (True, 'OK')
        return self._mount_and_do(_do)
    def _rename_via_mount(self, old: str, new: str) -> Tuple[bool, str]:
        def _do(drive):
            src = os.path.join(drive + '\\', old.lstrip('/'))
            dst = os.path.join(drive + '\\', new.lstrip('/'))
            os.rename(src, dst)
            return (True, 'OK')
        return self._mount_and_do(_do)
class Ext4Auditor:
    @staticmethod
    def audit(img_path: str) -> Dict[str, str]:
        exe = resolve_bin(BIN_EXT4_EXE)
        if not os.path.isfile(exe):
            return {'error': 'Servico indisponivel. Reinstale o sistema.'}
        try:
            r = subprocess.run([exe, 'audit', img_path], capture_output=True, text=True, timeout=60, creationflags=_CREATE_NO_WINDOW)
            result = {}
            for line in r.stdout.strip().splitlines():
                if ':' in line:
                    k, v = line.split(':', 1)
                    result[k.strip()] = v.strip()
            result['clean'] = 'clean' in r.stdout
            return result
        except Exception:
            return {'error': 'Falha na verificacao. Tente novamente.'}
    @staticmethod
    def info(img_path: str) -> Dict[str, str]:
        exe = resolve_bin(BIN_EXT4_EXE)
        if not os.path.isfile(exe):
            return {}
        try:
            r = subprocess.run([exe, 'info', img_path], capture_output=True, text=True, timeout=30, creationflags=_CREATE_NO_WINDOW)
            result = {}
            for line in r.stdout.strip().splitlines():
                if ':' in line:
                    k, v = line.split(':', 1)
                    result[k.strip()] = v.strip()
            return result
        except Exception:
            return {}
    @staticmethod
    def tree(img_path: str) -> str:
        exe = resolve_bin(BIN_EXT4_EXE)
        if not os.path.isfile(exe):
            return ''
        try:
            r = subprocess.run([exe, 'tree', img_path], capture_output=True, text=True, timeout=60, creationflags=_CREATE_NO_WINDOW)
        except Exception:
            return ''
        return r.stdout
class FmgrEngine:
    def __init__(self):
        self._reader = None
        self._writer = None
        self._img_path = ''
        self._fs_type = 0
        self._raw_data = None
        self._nvram_parser = None
        self._is_readonly = False
    @property
    def is_open(self) -> bool:
        return self._reader is not None or self._raw_data is not None
    @property
    def img_path(self) -> str:
        return self._img_path
    @property
    def fs_type(self) -> int:
        return self._fs_type
    @property
    def fs_type_name(self) -> str:
        return FS_NAMES.get(self._fs_type, 'Desconhecido')
    @property
    def is_readonly(self) -> bool:
        return self._is_readonly
    @property
    def is_nvram(self) -> bool:
        return self._nvram_parser is not None
    @property
    def is_raw(self) -> bool:
        return self._raw_data is not None and self._nvram_parser is None
    @property
    def nvram_parser(self):
        return self._nvram_parser
    @property
    def raw_data(self) -> Optional[bytes]:
        return self._raw_data
    def open_image(self, path: str) -> Tuple[bool, str]:
        self.close()
        self._fs_type = detect_filesystem(path)
        if self._fs_type == FS_SPARSE:
            return (False, 'Formato de imagem comprimido. Utilize uma imagem descompactada.')
        if self._fs_type == FS_EXT4:
            return self._open_ext4(path)
        if self._fs_type == FS_NVRAM:
            return self._open_nvram(path)
        if self._fs_type in (FS_RAW, FS_EROFS):
            if self._fs_type == FS_EROFS:
                return self._open_raw(path, 'EROFS (somente leitura)', readonly=True)
            return self._open_raw(path)
        return (False, 'Formato nao reconhecido.')
    def _open_ext4(self, path: str) -> Tuple[bool, str]:
        self._reader = Ext4Reader(path)
        if not self._reader.open():
            self._reader = None
            return (False, 'Falha ao abrir imagem. Verifique se o arquivo e valido.')
        self._writer = Ext4Writer(path)
        self._img_path = path
        self._is_readonly = False
        return (True, 'Imagem aberta com sucesso')
    def _open_nvram(self, path: str) -> Tuple[bool, str]:
        try:
            file_size = os.path.getsize(path)
            if file_size > 268435456:
                return (False, 'Arquivo muito grande para analise. Tamanho maximo: 256 MB.')
            with open(path, 'rb') as f:
                self._raw_data = f.read()
        except (OSError, IOError):
            return (False, 'Falha ao ler arquivo.')
        try:
            from .nvram_parser import NvramParser
            parser = NvramParser(self._raw_data)
            if parser.parse_index():
                self._nvram_parser = parser
                parser.try_decode_imei()
        except Exception:
            logger.debug('Fallback: NVRAM sem parser')
        self._img_path = path
        self._is_readonly = True
        return (True, 'NVRAM aberta (somente leitura)')
    def _open_raw(self, path: str, label: str='Raw', readonly: bool=False) -> Tuple[bool, str]:
        try:
            file_size = os.path.getsize(path)
            if file_size > 268435456:
                return (False, 'Arquivo muito grande para analise. Tamanho maximo: 256 MB.')
            with open(path, 'rb') as f:
                self._raw_data = f.read()
        except (OSError, IOError):
            return (False, 'Falha ao ler arquivo.')
        self._img_path = path
        self._is_readonly = readonly
        if readonly:
            return True, f'{label} aberto (somente leitura)'
        return True, f'{label} aberto'
    def write_raw_data(self, new_data: bytes) -> Tuple[bool, str]:
        if self._is_readonly:
            return (False, 'Arquivo aberto em modo somente leitura.')
        if not self._img_path:
            return (False, 'Nenhum arquivo aberto.')
        if self._raw_data is None:
            return (False, 'Nenhum dado carregado.')
        try:
            with open(self._img_path, 'wb') as f:
                f.write(new_data)
            self._raw_data = new_data
        except (OSError, IOError):
            return (False, 'Falha ao salvar. Verifique permissoes do arquivo.')
        return (True, 'Salvo com sucesso.')
    def close(self):
        if self._reader:
            self._reader.close()
            self._reader = None
        self._writer = None
        self._raw_data = None
        self._nvram_parser = None
        self._img_path = ''
        self._is_readonly = False
    def list_dir(self, path: str='/') -> List[EntryInfo]:
        if not self._reader:
            return []
        return self._reader.list_dir(path)
    def read_file(self, path: str) -> bytes:
        if not self._reader:
            return b''
        return self._reader.read_file(path)
    def get_info(self, path: str) -> Optional[EntryInfo]:
        if not self._reader:
            return
        return self._reader.get_info(path)
    def volume_info(self) -> Dict[str, str]:
        if not self._reader:
            return {}
        return self._reader.volume_info()
    def write_file(self, dest_path: str, data: bytes, log_cb: Optional[Callable]=None) -> Tuple[bool, str]:
        if not self._writer:
            return (False, 'Imagem nao aberta')
        if log_cb:
            log_cb(f'Escrevendo {format_size(len(data))}...')
        ok, msg = self._writer.write_file(dest_path, data)
        if ok and log_cb:
            log_cb('Escrita concluida')
        self._reopen()
        return ok, msg
    def delete(self, path: str, is_dir: bool=False, log_cb: Optional[Callable]=None) -> Tuple[bool, str]:
        if not self._writer:
            return (False, 'Imagem nao aberta')
        if log_cb:
            log_cb(f'Removendo {'pasta' if is_dir else 'arquivo'}...')
        ok, msg = self._writer.delete_file(path, is_dir=is_dir)
        self._reopen()
        return ok, msg
    def mkdir(self, path: str, log_cb: Optional[Callable]=None) -> Tuple[bool, str]:
        if not self._writer:
            return (False, 'Imagem nao aberta')
        if log_cb:
            log_cb('Criando pasta...')
        ok, msg = self._writer.mkdir(path)
        self._reopen()
        return ok, msg
    def rename(self, old_path: str, new_path: str, log_cb: Optional[Callable]=None) -> Tuple[bool, str]:
        if not self._writer:
            return (False, 'Imagem nao aberta')
        if log_cb:
            log_cb('Renomeando...')
        ok, msg = self._writer.rename(old_path, new_path)
        self._reopen()
        return ok, msg
    def chmod(self, path: str, mode: int, log_cb: Optional[Callable]=None) -> Tuple[bool, str]:
        if not self._writer:
            return (False, 'Imagem nao aberta')
        if log_cb:
            log_cb('Alterando permissoes...')
        ok, msg = self._writer.chmod(path, mode)
        self._reopen()
        return ok, msg
    def chown(self, path: str, uid: int, gid: int, log_cb: Optional[Callable]=None) -> Tuple[bool, str]:
        if not self._writer:
            return (False, 'Imagem nao aberta')
        if log_cb:
            log_cb('Alterando proprietario...')
        ok, msg = self._writer.chown(path, uid, gid)
        self._reopen()
        return ok, msg
    def audit(self) -> Dict[str, str]:
        if not self._img_path:
            return {}
        return Ext4Auditor.audit(self._img_path)
    def partition_info(self) -> Dict[str, str]:
        if not self._img_path:
            return {}
        return Ext4Auditor.info(self._img_path)
    def partition_tree(self) -> str:
        if not self._img_path:
            return ''
        return Ext4Auditor.tree(self._img_path)
    def export_file(self, src_path: str, dest_local: str, log_cb: Optional[Callable]=None) -> Tuple[bool, str]:
        data = self.read_file(src_path)
        if not data:
            if src_path != '/':
                return (False, 'Arquivo vazio ou nao encontrado')
        try:
            os.makedirs(os.path.dirname(dest_local), exist_ok=True)
            with open(dest_local, 'wb') as fh:
                fh.write(data)
            if log_cb:
                log_cb(f'Exportado ({format_size(len(data))})')
        except Exception:
            return (False, 'Falha ao exportar. Verifique o destino.')
        return True, f'Exportado ({format_size(len(data))})'
    def import_file(self, local_path: str, dest_img_path: str, log_cb: Optional[Callable]=None) -> Tuple[bool, str]:
        try:
            with open(local_path, 'rb') as fh:
                data = fh.read()
        except Exception:
            return (False, 'Falha ao ler arquivo. Verifique as permissoes.')
        return self.write_file(dest_img_path, data, log_cb)
    def _reopen(self):
        if self._img_path:
            if self._reader:
                self._reader.close()
                self._reader = Ext4Reader(self._img_path)
                self._reader.open()
