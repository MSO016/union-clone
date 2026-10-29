import time
import random
import hashlib
import logging
import subprocess
import re
from struct import pack
from binascii import unhexlify, hexlify
from pathlib import Path
from typing import Optional, Tuple
from Cryptodome.Cipher import AES
logger = logging.getLogger('edl_auth_oneplus')
DEVICE_CONFIG = {'16859': {'version': 1, 'cm': None, 'model': 'OnePlus 5'}, '17801': {'version': 1, 'cm': None, 'model': 'OnePlus 5T'}, '17819': {'version': 1, 'cm': None, 'model': 'OnePlus 6'}, '18801': {'version': 1, 'cm': None, 'model': 'OnePlus 6T'}, '18811': {'version': 1, 'cm': None, 'model': 'OnePlus 6T TMo'}, '18857': {'version': 1, 'cm': None, 'model': 'OnePlus 7'}, '18821': {'version': 1, 'cm': None, 'model': 'OnePlus 7 Pro'}, '18825': {'version': 1, 'cm': None, 'model': 'OnePlus 7 Pro 5G Sprint'}, '18827': {'version': 1, 'cm': None, 'model': 'OnePlus 7 Pro 5G EE'}, '18831': {'version': 1, 'cm': None, 'model': 'OnePlus 7 Pro TMo'}, '18865': {'version': 1, 'cm': None, 'model': 'OnePlus 7T'}, '19863': {'version': 1, 'cm': None, 'model': 'OnePlus 7T TMo'}, '19801': {'version': 1, 'cm': None, 'model': 'OnePlus 7T Pro'}, '19861': {'version': 1, 'cm': None, 'model': 'OnePlus 7T Pro 5G TMo'}, '20818': {'version': 1, 'cm': None, 'model': 'OnePlus dre8t'}, '2083C': {'version': 1, 'cm': None, 'model': 'OnePlus dre8m'}, '2083D': {'version': 1, 'cm': None, 'model': 'OnePlus dre9'}, '19821': {'version': 2, 'cm': '0cffee8a', 'model': 'OnePlus 8'}, '19855': {'version': 2, 'cm': '6d9215b4', 'model': 'OnePlus 8 TMo'}, '19867': {'version': 2, 'cm': '4107b2d4', 'model': 'OnePlus 8 Verizon'}, '19868': {'version': 2, 'cm': '178d8213', 'model': 'OnePlus 8 Visible'}, '19811': {'version': 2, 'cm': '40217c07', 'model': 'OnePlus 8 Pro'}, '19805': {'version': 2, 'cm': '1a5ec176', 'model': 'OnePlus 8T'}, '20809': {'version': 2, 'cm': 'd6bc8c36', 'model': 'OnePlus 8T TMo'}, '20801': {'version': 2, 'cm': 'eacf50e7', 'model': 'OnePlus Nord'}, '20813': {'version': 2, 'cm': '48ad7b61', 'model': 'OnePlus Nord CE'}, '19815': {'version': 2, 'cm': '9c151c7f', 'model': 'OnePlus 9 Pro'}, '20859': {'version': 2, 'cm': '9c151c7f', 'model': 'OnePlus 9 Pro'}, '20857': {'version': 2, 'cm': '9c151c7f', 'model': 'OnePlus 9 Pro'}, '19825': {'version': 2, 'cm': '0898dcd6', 'model': 'OnePlus 9'}, '20851': {'version': 2, 'cm': '0898dcd6', 'model': 'OnePlus 9'}, '20852': {'version': 2, 'cm': '0898dcd6', 'model': 'OnePlus 9'}, '20853': {'version': 2, 'cm': '0898dcd6', 'model': 'OnePlus 9'}, '20828': {'version': 2, 'cm': 'f498b60f', 'model': 'OnePlus 9R'}, '20838': {'version': 2, 'cm': 'f498b60f', 'model': 'OnePlus 9R'}, '20854': {'version': 2, 'cm': '16225d4e', 'model': 'OnePlus 9 TMo'}, '2085A': {'version': 2, 'cm': '7f19519a', 'model': 'OnePlus 9 Pro TMo'}, '20885': {'version': 3, 'cm': '3a403a71', 'model': 'OnePlus N10 5G Metro'}, '20886': {'version': 3, 'cm': 'b8bd9e39', 'model': 'OnePlus N10 5G Global'}, '20888': {'version': 3, 'cm': '142f1bd7', 'model': 'OnePlus N10 5G TMo'}, '20889': {'version': 3, 'cm': 'f2056ae1', 'model': 'OnePlus N10 5G EU'}, '20880': {'version': 3, 'cm': '6ccf5913', 'model': 'OnePlus N100 Metro'}, '20881': {'version': 3, 'cm': 'fa9ff378', 'model': 'OnePlus N100 Global'}, '20882': {'version': 3, 'cm': '4ca1e84e', 'model': 'OnePlus N100 TMo'}, '20883': {'version': 3, 'cm': 'ad9dba4a', 'model': 'OnePlus N100 EU'}}
_PRODKEY_GUACAMOLE = 'b2fad511325185e5'
_PRODKEY_DEFAULT = '7016147d58e8c038'
_V1_KEY_PREFIX = b'\x10Ec\x87\xe3~#q'
_V1_KEY_SUFFIX = b'\xa2\xd4\xa0t\x0f\xd3(\x96'
_V1_IV = b'\x9daJ\x1e\xac\x81\xc9\xb2\xd3v\xd7I1\x03cy'
_V1_DEM_KEY_PREFIX = b'\x01c\xa0\xd1\xfd\xe2g\x11'
_V1_DEM_KEY_SUFFIX = b"H'\xc2\x08\xfb\xb0\xe6\xf0"
_V1_DEM_IV = b'\x96\xe0y\x0c\xae+\xb4\xafhL6\xcb\x0b\xecI\xce'
_V2_KEY_PREFIX = b'F\xa5\x970\xbb\rA\xe8'
_V2_IV = b'\xdc\x91\r\x88\xe3\xc6\xeee\xf0\xc7D\xb4\x020\xce@'
def _aes_cbc_encrypt(key: bytes, iv: bytes, data: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(data)
def _aes_cbc_decrypt(key: bytes, iv: bytes, data: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.decrypt(data)
def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()
def _sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest().upper()
def _generate_random_pk() -> str:
    charset = b'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    return ''.join((chr(charset[random.randint(0, 255) % len(charset)]) for _ in range(16)))
def _get_prodkey(projid: str) -> str:
    if projid in ('18825', '18801'):
        return _PRODKEY_GUACAMOLE
    return _PRODKEY_DEFAULT
def _v1_encrypt_token(data: str, pk: str) -> str:
    key = _V1_KEY_PREFIX + pk.encode('utf-8') + _V1_KEY_SUFFIX
    padded = data.encode('utf-8').ljust(256, b'\x00')
    encrypted = _aes_cbc_encrypt(key, _V1_IV, padded)
    return hexlify(encrypted).decode('utf-8').upper()
def _v1_generate_demacia(pk: str, serial: str) -> str:
    sn = serial.zfill(10)
    hash_input = '2e7006834dafe8ad' + sn + 'a6674c6b039707ff'
    payload = b'907heavyworkload' + _sha256(hash_input.encode('utf-8'))
    key = _V1_DEM_KEY_PREFIX + pk.encode('utf-8') + _V1_DEM_KEY_SUFFIX
    padded = payload.ljust(256, b'\x00')
    encrypted = _aes_cbc_encrypt(key, _V1_DEM_IV, padded)
    return hexlify(encrypted).decode('utf-8').upper()
def _v1_generate_setprojmodel(projid: str, serial: str, pk: str) -> str:
    prodkey = _get_prodkey(projid)
    timestamp = str(int(time.time()))
    random_postfix = '0iyFR00pPnoqjVNL'
    version = 'guacamoles_21_O.22_191107'
    cf = '0'
    h1 = prodkey + projid + random_postfix
    verify_hash = _sha256_hex(h1)
    h2 = 'c4b95538c57df231' + projid + cf + serial + version + timestamp + verify_hash + '5b0217457e49381b'
    secret = _sha256_hex(h2)
    items = [projid, random_postfix, verify_hash, version, cf, serial, timestamp, secret]
    payload = ','.join(items)
    return _v1_encrypt_token(payload, pk)
def _v2_encrypt_token(data: str, pk: str, device_timestamp: int) -> str:
    key = _V2_KEY_PREFIX + pk.encode('utf-8') + pack('<Q', device_timestamp)
    padded = data.encode('utf-8').ljust(512, b'\x00')
    encrypted = _aes_cbc_encrypt(key, _V2_IV, padded)
    return hexlify(encrypted).decode('utf-8').upper()
def _v2_generate_setswprojmodel(cm: str, serial: str, pk: str, device_timestamp: int) -> str:
    prodkey = _PRODKEY_DEFAULT
    timestamp = str(int(time.time()))
    random_postfix = 'c75oVnz8yUgLZObh'
    version = 'billie8_14_E.01_201028'
    device_id = str(int(cm, 16))
    h1 = prodkey + cm + random_postfix
    verify_hash = _sha256_hex(h1)
    h2 = prodkey + cm + serial + version + timestamp + verify_hash + '8f7359c8a2951e8c'
    secret = _sha256_hex(h2)
    items = [cm, random_postfix, verify_hash, '0', '0', version, serial, device_id, timestamp, secret]
    payload = ','.join(items)
    return _v2_encrypt_token(payload, pk, device_timestamp)
def gerar_xml_demacia(projid: str, serial: str='123456') -> str:
    pk = _generate_random_pk()
    token = _v1_generate_demacia(pk, serial)
    return f'<?xml version="1.0" ?>\n<data>\n<demacia token="{token}" pk="{pk}" />\n</data>'
def gerar_xml_setprojmodel(projid: str, serial: str='123456') -> str:
    pk = _generate_random_pk()
    token = _v1_generate_setprojmodel(projid, serial, pk)
    return f'<?xml version="1.0" ?>\n<data>\n<setprojmodel token="{token}" pk="{pk}" />\n</data>'
def gerar_xml_setprocstart() -> str:
    return '<?xml version="1.0" ?>\n<data>\n<setprocstart />\n</data>'
def gerar_xml_setswprojmodel(cm: str, serial: str, device_timestamp: int) -> str:
    pk = _generate_random_pk()
    token = _v2_generate_setswprojmodel(cm, serial, pk, device_timestamp)
    return f'<?xml version="1.0" ?>\n<data>\n<setswprojmodel token="{token}" pk="{pk}" />\n</data>'
def get_auth_version(projid: str) -> Optional[int]:
    cfg = DEVICE_CONFIG.get(projid)
    if cfg:
        return cfg['version']
def get_model_name(projid: str) -> str:
    cfg = DEVICE_CONFIG.get(projid)
    if cfg:
        return cfg['model']
    return f'OnePlus (projid={projid})'
def is_supported(projid: str) -> bool:
    return projid in DEVICE_CONFIG
def listar_modelos_suportados() -> list:
    result = []
    for projid, cfg in DEVICE_CONFIG.items():
        result.append({'projid': projid, 'version': cfg['version'], 'model': cfg['model'], 'cm': cfg.get('cm')})
    return result
def aplicar_auth_oneplus_via_fh(fh_loader_exe: str, porta_com: str, loader_path: str, projid: str, serial: str='123456', log_callback=None) -> bool:
    def _log(msg):
        if log_callback:
            log_callback(msg)
        logger.info(msg)
    cfg = DEVICE_CONFIG.get(projid)
    if not cfg:
        logger.warning(f'projid {projid} nao suportado')
        return False
    version = cfg['version']
    cm = cfg.get('cm')
    logger.info(f'Modelo: {cfg['model']} | Auth v{version}')
    fh_exe = Path(fh_loader_exe)
    if not fh_exe.exists():
        logger.error(f'fh_loader nao encontrado: {fh_exe}')
        return False
    try:
        from app.views.union_unlock.edl.firehose_ops import _edl_mkdtemp
        tmp_dir = Path(_edl_mkdtemp(prefix='auth_op_'))
    except ImportError:
        import tempfile
        import sys as _sys
        _base = os.environ.get('LOCALAPPDATA', tempfile.gettempdir()) if _sys.platform == 'win32' else tempfile.gettempdir()
        tmp_dir = Path(_base) / '.union_edl' / 'auth_op'
        tmp_dir.mkdir(parents=True, exist_ok=True)
    def _send_xml(xml_content: str, desc: str) -> Optional[str]:
        xml_file = tmp_dir / f'auth_{desc}.xml'
        xml_file.write_text(xml_content, encoding='utf-8')
        cmd = [str(fh_exe), f'--port=\\\\.\\{porta_com}', f'--sendxml={xml_file}', '--noprompt', '--showpercentagecomplete', '--zlpawarehost=1', '--memoryname=ufs']
        logger.info(f'Enviando {desc}...')
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
            output = result.stdout + result.stderr
            logger.info(f'{desc} retorno: {result.returncode}')
            return output
        except subprocess.TimeoutExpired:
            logger.warning(f'Timeout em {desc}')
        except Exception as e:
            logger.error(f'Erro em {desc}: {e}')
    if version == 1:
        xml_dem = gerar_xml_demacia(projid, serial)
        out_dem = _send_xml(xml_dem, 'demacia')
        if out_dem and 'verify_res="0"' in out_dem:
            logger.info('Etapa 1 OK')
        else:
            logger.info('Etapa 1 nao aplicavel, prosseguindo...')
        xml_proj = gerar_xml_setprojmodel(projid, serial)
        out_proj = _send_xml(xml_proj, 'setprojmodel')
        if out_proj and 'model_check="0"' in out_proj and 'auth_token_verify="0"' in out_proj:
            logger.info('Autenticacao v1 concluida!')
            _log('Autenticacao concluida com sucesso!')
            return True
        logger.warning('Autenticacao v1 falhou')
        if out_proj:
            logger.debug(f'Resposta: {out_proj[:500]}')
        _log('Falha na autenticacao. Reconecte o dispositivo e tente novamente.')
        return False
    if version in (2, 3):
        if not cm:
            logger.error(f'Configuracao incompleta para projid {projid}')
            _log('Configuracao de autenticacao incompleta para este modelo.')
            return False
        xml_start = gerar_xml_setprocstart()
        out_start = _send_xml(xml_start, 'setprocstart')
        if not out_start or 'device_timestamp' not in out_start:
            logger.warning('Etapa inicial falhou')
            if out_start:
                logger.debug(f'Resposta: {out_start[:500]}')
            _log('Dispositivo nao respondeu a autenticacao.\nReconecte e tente novamente.')
            return False
        ts_match = re.search('device_timestamp="(\\d+)"', out_start)
        if not ts_match:
            logger.warning('Nao foi possivel extrair dados do dispositivo')
            _log('Falha ao obter dados do dispositivo para autenticacao.')
            return False
        device_timestamp = int(ts_match.group(1))
        logger.info(f'device_timestamp={device_timestamp}')
        xml_sw = gerar_xml_setswprojmodel(cm, serial, device_timestamp)
        out_sw = _send_xml(xml_sw, 'setswprojmodel')
        if out_sw and 'model_check="0"' in out_sw and 'auth_token_verify="0"' in out_sw:
            logger.info(f'Autenticacao v{version} concluida!')
            _log('Autenticacao concluida com sucesso!')
            return True
        logger.warning(f'Autenticacao v{version} falhou')
        if out_sw:
            logger.debug(f'Resposta: {out_sw[:500]}')
        _log('Falha na autenticacao. Reconecte o dispositivo e tente novamente.')
        return False
    logger.error(f'Versao de auth {version} nao implementada')
    _log('Este modelo nao e suportado para autenticacao nesta versao.')
    return False
def detectar_projid_via_param(fh_loader_exe: str, porta_com: str, loader_path: str, memoria: str='ufs', log_callback=None) -> Optional[str]:
    def _log(msg):
        if log_callback:
            log_callback(msg)
    try:
        from app.views.union_unlock.edl.firehose_ops import _edl_mkdtemp
        tmp_dir = Path(_edl_mkdtemp(prefix='auth_op_'))
    except ImportError:
        import tempfile
        import sys as _sys
        _base = os.environ.get('LOCALAPPDATA', tempfile.gettempdir()) if _sys.platform == 'win32' else tempfile.gettempdir()
        tmp_dir = Path(_base) / '.union_edl' / 'auth_op'
        tmp_dir.mkdir(parents=True, exist_ok=True)
    param_out = tmp_dir / 'param_read.bin'
    xml_content = f'<?xml version="1.0" ?>\n<data>\n<read SECTOR_SIZE_IN_BYTES="4096" filename="{param_out}" num_partition_sectors="1" physical_partition_number="0" start_sector="param" />\n</data>'
    xml_file = tmp_dir / 'read_param.xml'
    xml_file.write_text(xml_content, encoding='utf-8')
    cmd = [str(fh_loader_exe), f'--port=\\\\.\\{porta_com}', f'--sendxml={xml_file}', '--noprompt', f'--memoryname={memoria}']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
        if param_out.exists():
            data = param_out.read_bytes()
            if len(data) >= 29:
                projid_bytes = data[24:29]
                try:
                    try:
                        projid = projid_bytes.decode('utf-8').strip('\x00')
                        int(projid, 16)
                        _log('Modelo detectado automaticamente')
                    except (ValueError, UnicodeDecodeError):
                        return
                except Exception as e:
                    _log('Falha na deteccao automatica do modelo')
                return projid
    except Exception as e:
        _log('Falha na deteccao automatica do modelo')
