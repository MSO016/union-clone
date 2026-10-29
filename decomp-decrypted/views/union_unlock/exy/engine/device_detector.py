import contextlib
import logging
import re
import subprocess
import time
from typing import (Callable, List, Optional)
from app.views.union_unlock.exy.models.device import DeviceInfo
from app.views.union_unlock.exy.engine import _cfg
_log = logging.getLogger(__name__)
LogCb = Optional[Callable[[str], None]]
def _emit(cb: LogCb, msg: str):
    if cb:
        cb(msg)
@contextlib.contextmanager
def _com_init():
    try:
        import pythoncom
        pythoncom.CoInitialize()
        yield None
    except Exception:
        try:
            import pythoncom
            pythoncom.CoUninitialize()
        except ImportError:
            yield None
        else:
            return
        finally:
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except Exception:
                pass
def detect_samsung_modem(log_cb: LogCb=None) -> Optional[DeviceInfo]:
    try:
        import wmi
    except ImportError:
        _emit(log_cb, 'Componente de deteccao indisponivel')
    _emit(log_cb, 'Buscando dispositivo Samsung...')
    try:
        with _com_init():
            c = wmi.WMI()
            for modem in c.Win32_POTSModem(Status='OK'):
                caption = (modem.Caption or '').lower()
                if 'samsung' not in caption:
                    continue
                port = modem.AttachedTo or ''
                device_id = modem.DeviceID or ''
                dev = DeviceInfo(model=modem.Caption or 'Samsung Device', com_port=port, unique_id=device_id, vendor='Samsung', mode='modem')
                _emit(log_cb, f'Dispositivo encontrado: {dev.model}')
                dev
                return
    except Exception as exc:
        _emit(log_cb, 'Erro na deteccao do dispositivo')
        _log.error('Erro WMI: %s', exc, exc_info=True)
    _emit(log_cb, 'Nenhum dispositivo Samsung encontrado')
def _open_serial(port: str, timeout: int=5):
    import serial
    return serial.Serial(port, baudrate=_cfg.SERIAL_BAUDRATE, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE, rtscts=True, dsrdtr=False, timeout=timeout, write_timeout=timeout)
def probe_serial_at(port: str, log_cb: LogCb=None) -> bool:
    try:
        import serial
    except ImportError:
        return False
    try:
        with serial.Serial(port, _cfg.SERIAL_BAUDRATE, timeout=3, write_timeout=3) as ser:
            ser.write(b'AT\r\n')
            time.sleep(0.5)
            resp = ser.read(256).decode('ascii', errors='ignore')
            if 'OK' in resp:
                _emit(log_cb, 'Dispositivo responde ÔÇö modo normal')
                return True
            _emit(log_cb, 'Sem resposta ÔÇö provavel Download Mode')
    except Exception as exc:
        _log.error('Verificacao serial: %s', exc)
        _emit(log_cb, 'Erro na verificacao do dispositivo')
    return False
def _send_at(ser, cmd: str, wait: float=1.0) -> str:
    try:
        if ser.in_waiting:
            ser.read(ser.in_waiting)
        ser.write(f'{cmd}\r\n'.encode('utf-8'))
        time.sleep(wait)
        raw = b''
        empty_rounds = 0
        while empty_rounds < 15:
            if ser.in_waiting:
                raw += ser.read(ser.in_waiting)
                empty_rounds = 0
                time.sleep(0.1)
            else:
                empty_rounds += 1
                time.sleep(0.1)
        text = raw.decode('ascii', errors='ignore')
        useful = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line == cmd:
                continue
            if line == 'OK':
                continue
            if 'ERROR' not in line:
                useful.append(line)
        return ' '.join(useful)
    except Exception:
        return ''
def _parse_devconinfo(raw: str) -> dict:
    import re
    info = {}
    for m in re.finditer('(\\w+)\\(([^)]*)\\)', raw):
        key, val = m.group(1).strip(), m.group(2).strip()
        if not key:
            continue
        if not val:
            continue
        if val not in ('NONE', 'UNKNOWN', ''):
            info[key] = val
    return info
def read_device_info_at(port: str, log_cb: LogCb=None) -> dict:
    try:
        import serial
    except ImportError:
        return {}
    info = {}
    try:
        with serial.Serial(port, _cfg.SERIAL_BAUDRATE, timeout=3, write_timeout=3) as ser:
            resp = _send_at(ser, 'AT+DEVCONINFO', 2.0)
            if resp and '(' in resp:
                parsed = _parse_devconinfo(resp)
                info.update(parsed)
            if 'MODEL' not in info:
                val = _send_at(ser, 'AT+GMM')
                if val:
                    info['MODEL'] = val
            if 'IMEI' not in info:
                val = _send_at(ser, 'AT+CGSN')
                if val and val.isdigit():
                    info['IMEI'] = val
            if not info.get('VER'):
                val = _send_at(ser, 'AT+GMR')
                if val:
                    info['VER'] = val
        _AT_LABEL = {'MODEL': 'Modelo', 'IMEI': 'IMEI', 'SN': 'Serial', 'SALES': 'Codigo regional', 'VER': 'Firmware', 'LOCK': 'Status'}
        for key in ('MODEL', 'IMEI', 'SN', 'SALES', 'VER', 'LOCK'):
            val = info.get(key)
            if val:
                label = _AT_LABEL.get(key, key)
                _emit(log_cb, f'{label}: {val}')
    except Exception as exc:
        _log.error('read_device_info_at %s: %s', port, exc)
    return info
_DVIF_LABEL = {'MODEL': 'Modelo', 'UN': 'Numero unico', 'PN': 'Produto', 'VND': 'Fabricante', 'SALES': 'Codigo regional', 'VER': 'Firmware', 'FWVER': 'Versao FW', 'DID': 'DID', 'CAPA': 'Capacidade'}
def _parse_dvif(raw: str) -> dict:
    import re
    info = {}
    clean = raw.replace('#', '').replace('@', '')
    for m in re.finditer('(\\w+)\\(([^)]*)\\)', clean):
        key, val = m.group(1).strip(), m.group(2).strip()
        if '/' in val:
            val = val.split('/')[0]
        if not key:
            continue
        if val:
            info[key] = val
    if not info:
        for item in clean.split(';'):
            item = item.strip()
            if '=' in item:
                key, _, val = item.partition('=')
                key, val = key.strip(), val.strip()
                if not key:
                    continue
                if val:
                    info[key] = val
    return info
def read_device_info_odin(port: str, log_cb: LogCb=None) -> dict:
    try:
        import serial
    except ImportError:
        return {}
    info = {}
    try:
        ser = _open_serial(port, timeout=10)
    except Exception as exc:
        _emit(log_cb, 'Erro ao ler informacoes do dispositivo')
        _log.error('read_device_info: %s: %s', port, exc)
        return info
    try:
        ser.write(b'DVIF')
        time.sleep(0.4)
        raw = ser.read(4096).decode('ascii', errors='ignore')
        ser.close()
        if raw:
            info = _parse_dvif(raw)
            for key in ('MODEL', 'UN', 'PN', 'SALES', 'VER', 'DID'):
                val = info.get(key)
                if val:
                    label = _DVIF_LABEL.get(key, key)
                    _emit(log_cb, f'{label}: {val}')
    finally:
        try:
            ser.close()
        except Exception:
            return info
    return info
def reboot_to_download(port: str, log_cb: LogCb=None) -> bool:
    try:
        import serial
    except ImportError:
        _emit(log_cb, 'Componente de comunicacao indisponivel')
        return False
    _emit(log_cb, 'Enviando comando de reboot para Download Mode...')
    try:
        ser = serial.Serial(port, _cfg.SERIAL_BAUDRATE, timeout=5, write_timeout=5)
    except Exception as exc:
        _log.error('Conexao serial: %s', exc)
        _emit(log_cb, 'Nao foi possivel conectar ao dispositivo')
        return False
    try:
        ser.write(b'AT+FUS?\r\n')
        start = time.monotonic()
        response = ''
        while time.monotonic() - start < 5.0:
            time.sleep(0.05)
        try:
            waiting = ser.in_waiting
            if waiting > 0:
                chunk = ser.read(waiting)
                if chunk:
                    response += chunk.decode('ascii', errors='ignore')
        except Exception:
            _emit(log_cb, 'Conexao interrompida (dispositivo reiniciando)')
    except Exception as exc:
        _emit(log_cb, 'Erro ao enviar comando de reboot')
        _log.error('reboot_to_download %s: %s', port, exc)
    try:
        _emit(log_cb, 'Comando de reboot enviado')
    except Exception as exc:
        _emit(log_cb, 'Erro ao enviar comando de reboot')
        _log.error('reboot_to_download %s: %s', port, exc)
    try:
        ser.close()
    except Exception:
        pass
    return True
def wait_download_mode(timeout_s: int=30, log_cb: LogCb=None, cancel_event=None, old_port: str='') -> Optional[DeviceInfo]:
    _emit(log_cb, 'Aguardando dispositivo reiniciar...')
    time.sleep(3.0)
    start = time.monotonic()
    check_interval = 3.0
    while time.monotonic() - start < timeout_s:
        if cancel_event and cancel_event.is_set():
            _emit(log_cb, 'Cancelado')
            return
        dev = detect_samsung_modem(log_cb=None)
        if dev:
            new_port = dev.com_port
            if old_port and new_port != old_port:
                _emit(log_cb, 'Dispositivo reconectado')
            _emit(log_cb, f'Dispositivo reapareceu: {dev.model}')
            dev.mode = 'download'
            return dev
        elapsed = int(time.monotonic() - start)
        _emit(log_cb, f'Aguardando... ({elapsed}s/{timeout_s}s)')
        time.sleep(check_interval)
    _emit(log_cb, f'Timeout ({timeout_s}s) ÔÇö dispositivo nao reapareceu')
def detect_adb_devices(log_cb: LogCb=None) -> List[dict]:
    adb = str(_cfg.get_adb_path())
    devices = []
    try:
        result = subprocess.run([adb, 'devices'], capture_output=True, text=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
        for line in result.stdout.splitlines():
            line = line.strip()
            if line:
                if line.startswith('List') or line.startswith('*'):
                    continue
                parts = line.split('\t')
                if len(parts) >= 2:
                    devices.append({'serial': parts[0], 'state': parts[1]})
    except FileNotFoundError:
        _emit(log_cb, 'ADB nao encontrado')
    except subprocess.TimeoutExpired:
        _emit(log_cb, 'ADB timeout')
    except Exception as exc:
        _log.error('ADB detect: %s', exc)
        _emit(log_cb, 'Erro na deteccao ADB')
    if devices:
        _emit(log_cb, f'ADB: {len(devices)} dispositivo(s)')
    return devices
def auto_detect(log_cb: LogCb=None) -> Optional[DeviceInfo]:
    dev = detect_samsung_modem(log_cb)
    if dev and dev.com_port:
        at_ok = probe_serial_at(dev.com_port, log_cb)
        if at_ok:
            dev.mode = 'normal'
            _emit(log_cb, "Use 'REBOOT TO DOWNLOAD' para entrar em Download Mode")
            return dev
        dev.mode = 'download'
        _emit(log_cb, 'OK')
        dvif = read_device_info_odin(dev.com_port, log_cb)
        if dvif.get('MODEL'):
            dev.model = dvif['MODEL']
        if dvif.get('UN'):
            dev.unique_id = dvif['UN']
        return dev
    adb_devs = detect_adb_devices(log_cb)
    if adb_devs:
        first = adb_devs[0]
        dev = DeviceInfo(model=first['serial'], unique_id=first['serial'], vendor='Samsung', mode='adb' if first['state'] == 'device' else first['state'])
        _emit(log_cb, f'Dispositivo ADB: {dev.model} [{dev.mode}]')
        return dev
    _emit(log_cb, 'Nenhum dispositivo Samsung detectado')
# WARNING: Decompyle incomplete
