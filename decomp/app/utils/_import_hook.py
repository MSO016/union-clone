import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import marshal
import os
import sys
import types
_h0 = False
_S0 = ('_', 'importlib', 'os', 'sys', 'io', 'abc', 'codecs', 'encodings', 'zipimport', 'marshal', 'types', 'struct', 'PyQt5', 'PyQt6', 'numpy', 'PIL', 'cv2', 'cryptography', 'flask', 'waitress', 'jinja2', 'werkzeug', 'sqlalchemy', 'psutil', 'win32', 'comtypes', 'ctypes', 'email', 'http', 'urllib', 'ssl', 'socket', 'json', 'logging', 'threading', 'multiprocessing', 'concurrent', 'asyncio', 'collections', 'functools', 'itertools', 'operator', 'pathlib', 'shutil', 'tempfile', 'glob', 'fnmatch', 're', 'string', 'textwrap', 'unicodedata', 'locale', 'decimal', 'fractions', 'random', 'statistics', 'math', 'datetime', 'time', 'calendar', 'hashlib', 'hmac', 'base64', 'binascii', 'zlib', 'gzip', 'bz2', 'lzma', 'zipfile', 'tarfile', 'csv', 'configparser', 'argparse', 'getpass', 'platform', 'uuid', 'copy', 'pprint', 'traceback', 'warnings', 'contextlib', 'dataclasses', 'enum', 'typing', 'inspect', 'dis', 'tokenize', 'ast', 'subprocess', 'signal', 'select', 'selectors', 'mmap', 'pickle', 'shelve', 'dbm', 'sqlite3', 'xml', 'html', 'webbrowser', 'cgi', 'ftplib', 'imaplib', 'smtplib', 'mysql', 'pymysql', 'boto3', 'botocore', 'requests', 'certifi', 'charset_normalizer', 'idna', 'socks', 'pkg_resources', 'setuptools', 'pip', 'wheel', 'pydantic', 'attr', 'click', 'colorama', 'tqdm', 'serial', 'usb', 'hid', 'wmi', 'pythoncom', 'qrcode', 'reportlab', 'openpyxl', 'xlsxwriter')
def _r0():
    try:
        _m = __import__('app.utils._security_crypto', fromlist=['_'])
        _n1 = bytes([100, 101, 99, 114, 121, 112, 116, 95, 112, 121, 99]).decode()
        _n2 = bytes([105, 115, 95, 112, 121, 99, 95, 101, 110, 99, 114, 121, 112, 116, 101, 100]).decode()
        return getattr(_m, _n1), getattr(_m, _n2)
    except Exception:
        return (None, None)
class _F0(importlib.abc.MetaPathFinder):
    def __init__(self, bp):
        self._b = bp
    def find_spec(self, fullname, path, target=None):
        t = fullname.split('.')[0]
        if t in _S0 or fullname.startswith(_S0):
            return
        _d, _v = _r0()
        if _d is None:
            return
        p = fullname.split('.')
        rp = os.path.join(*p[:-1]) if len(p) > 1 else ''
        mn = p[-1]
        sd = []
        if path:
            sd = list(path)
        sd.append(os.path.join(self._b, rp))
        for d in sd:
            if not os.path.isdir(d):
                continue
            fp = os.path.join(d, mn + '.pyc')
            if not os.path.isfile(fp):
                pi = os.path.join(d, mn, '__init__.pyc')
                if os.path.isfile(pi):
                    fp = pi
                else:
                    continue
            try:
                with open(fp, 'rb') as f:
                    hd = f.read(4)
            except (IOError, OSError):
                continue
            if not _v(hd):
                continue
            ip = fp.endswith('__init__.pyc')
            ld = _L0(fp)
            sp = importlib.machinery.ModuleSpec(fullname, ld, origin=fp, is_package=ip)
            if ip:
                sp.submodule_search_locations = [os.path.dirname(fp)]
            return sp
class _L0(importlib.abc.Loader):
    def __init__(self, p):
        self._p = p
    def create_module(self, spec):
        pass
    def exec_module(self, module):
        _d, _ = _r0()
        if _d is None:
            raise ImportError(self._p)
        try:
            with open(self._p, 'rb') as f:
                ed = f.read()
        except (IOError, OSError):
            raise ImportError(self._p)
        rd = _d(ed)
        if rd is None:
            raise ImportError(self._p)
        _hs = 16
        if len(rd) <= _hs:
            raise ImportError(self._p)
        bc = rd[_hs:]
        try:
            co = marshal.loads(bc)
        except Exception:
            raise ImportError(self._p)
        module.__file__ = self._p
        module.__loader__ = self
        if hasattr(module, '__path__'):
            pass
        exec(co, module.__dict__)
def activate():
    global _h0
    if _h0:
        return True
    try:
        _bp = None
        if getattr(sys, 'frozen', False):
            _bp = os.path.join(sys._MEIPASS)
        else:
            _bp = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if not os.path.isdir(os.path.join(_bp, 'app')):
            return False
        sys.meta_path.insert(0, _F0(_bp))
        _h0 = True
        return True
    except Exception:
        return False
