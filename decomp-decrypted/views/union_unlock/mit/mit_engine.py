import base64
import hashlib
import logging
import os
import posixpath
import subprocess
import struct
import time
from typing import (Callable, Dict, List, Optional, Tuple)
from . import _mit_core as _core
logger = logging.getLogger(__name__)
_CW = 134217728
_SI = None
if os.name == 'nt':
    _SI = subprocess.STARTUPINFO()
    _SI.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    _SI.wShowWindow = subprocess.SW_HIDE
try:
    import serial
    import serial.tools.list_ports
    _HAS_SERIAL = True
except ImportError:
    _HAS_SERIAL = False
    logger.warning('pyserial nao disponivel')
LogCb = Callable[[str], None]
def _noop_log(msg):
    pass
def _resolver_mit_dir() -> Optional[str]:
    try:
        from app.utils.unlock_tools_manager import get_unlock_tools_manager
        mgr = get_unlock_tools_manager()
        tools_dir = mgr.get_tools_dir()
        mit_dir = os.path.join(tools_dir, _core.BIN_SUBDIR)
        if os.path.isdir(mit_dir):
            return mit_dir
    except Exception:
        pass
    try:
        base = os.path.dirname(os.path.abspath(__file__))
        parent = os.path.dirname(base)
        fallback = os.path.join(parent, 'tools', _core.BIN_SUBDIR)
        if os.path.isdir(fallback):
            return fallback
    except Exception:
        pass
def _resolver_binario(nome: str) -> Optional[str]:
    mit_dir = _resolver_mit_dir()
    if not mit_dir:
        return
    caminho = os.path.join(mit_dir, nome)
    if not os.path.isfile(caminho):
        return
    expected = _core.BIN_HASHES.get(nome)
    if expected:
        try:
            sha = hashlib.sha256()
            with open(caminho, 'rb') as f:
                for bloco in iter((lambda: f.read(8192)), b''):
                    sha.update(bloco)
            if not sha.hexdigest().upper().startswith(expected):
                logger.error('Integridade falhou: %s', nome)
                return
        except Exception:
            return
        return caminho
    return caminho
def list_mtk_ports(meta_only=False):
    if not _HAS_SERIAL:
        return []
    out = []
    for p in serial.tools.list_ports.comports():
        if p.vid != _core.VID:
            continue
        mode = 'META' if p.pid in _core.PIDS_META else 'PRELOADER' if p.pid in _core.PIDS_PRELOADER else 'OTHER'
        if meta_only:
            if mode != 'META':
                continue
        out.append({'port': p.device, 'vid': p.vid, 'pid': p.pid, 'mode': mode})
    return out
def snapshot_ports():
    if not _HAS_SERIAL:
        return set()
    return {p.device for p in serial.tools.list_ports.comports() if p.vid == _core.VID}
def wait_vcom_after_boot(log_cb=None, before_ports=None, timeout=20.0, settle_s=0.3):
    if not _HAS_SERIAL:
        return
    log = log_cb or _noop_log
    before = before_ports or set()
    log('Aguardando dispositivo...')
    time.sleep(0.5)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        time.sleep(0.1)
        current = set()
        for p in serial.tools.list_ports.comports():
            if p.vid != _core.VID:
                continue
            if p.pid in _core.PIDS_META:
                current.add(p.device)
        new_ports = current - before
        if new_ports:
            port = sorted(new_ports)[0]
            log('Dispositivo detectado: %s' % port)
            time.sleep(settle_s)
            return port
        if not before:
            metas = list_mtk_ports(meta_only=True)
            if metas:
                port = metas[0]['port']
                log('Dispositivo detectado: %s' % port)
                time.sleep(settle_s)
                return port
class MitEngine:
    def __init__(self):
        self._ser = None
        self._seq = 1
        self._process = None
        self._cancelado = False
    @property
    def available(self) -> bool:
        return _HAS_SERIAL
    def cancel(self):
        self._cancelado = True
        self._kill_process_tree()
        self._close_serial()
    def _kill_process_tree(self):
        proc = self._process
        self._process = None
        if not proc:
            return
        if proc.poll() is not None:
            return
        pid = proc.pid
        if os.name == 'nt':
            try:
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], capture_output=True, timeout=5, creationflags=_CW, startupinfo=_SI)
            except Exception:
                pass
        try:
            proc.kill()
        except Exception:
            pass
        try:
            proc.wait(timeout=5)
        except Exception:
            return
    def _kill_stale_binaries(self):
        if os.name != 'nt':
            return
        try:
            subprocess.run(['taskkill', '/F', '/IM', _core.BIN_BOOT_EXE], capture_output=True, timeout=5, creationflags=_CW, startupinfo=_SI)
            return
        except Exception:
            return
    def boot_meta(self, log_cb=None) -> Tuple[bool, str, str]:
        log = log_cb or _noop_log
        self._cancelado = False
        self._kill_stale_binaries()
        self._close_serial()
        exe = _resolver_binario(_core.BIN_BOOT_EXE)
        if not exe:
            return (False, 'Modulo nao disponivel', '')
        try:
            subprocess.run(['adb', 'kill-server'], capture_output=True, timeout=5, creationflags=_CW, startupinfo=_SI)
        except Exception:
            pass
        before = snapshot_ports()
        mit_dir = os.path.dirname(exe)
        approaches = [('S', 'Tentando conexao segura...'), ('ALL', 'Tentando conexao alternativa...')]
        for approach, msg_inicio in approaches:
            if self._cancelado:
                return (False, 'Operacao cancelada.', '')
            log(msg_inicio)
            try:
                self._process = subprocess.Popen([exe, 'DETECT', 'META', '120', approach], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=mit_dir, creationflags=_CW if os.name == 'nt' else 0, startupinfo=_SI)
                rc = -1
                stdout = ''
                try:
                    raw_out, _ = self._process.communicate(timeout=120)
                    stdout = raw_out.decode('utf-8', errors='replace')
                    rc = self._process.returncode
                except subprocess.TimeoutExpired:
                    self._kill_process_tree()
                    log('Tempo esgotado, tentando alternativa...')
                else:
                    self._process = None
                    if self._cancelado:
                        pass
            except Exception:
                self._process = None
            try:
                if rc == 0 or 'SUCCESS' in stdout:
                    log('Dispositivo conectado.')
                    port = wait_vcom_after_boot(log_cb=log, before_ports=before, timeout=20.0, settle_s=0.3)
                    if port:
                        return True, 'Conectado', port
                    return (False, 'Verifique o driver USB.', '')
            except Exception:
                self._process = None
            try:
                logger.debug('Approach %s falhou (rc=%d)', approach, rc)
            except Exception:
                self._process = None
            continue
        return (False, 'Falha na conexao. Reconecte o dispositivo.', '')
    def _open_serial(self, port, baud=115200):
        if not _HAS_SERIAL:
            raise RuntimeError('Modulo nao disponivel')
        path = '\\\\.\\%s' % port if os.name == 'nt' else port
        self._ser = serial.Serial(port=path, baudrate=baud, timeout=5.0, write_timeout=3.0, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, dsrdtr=False, rtscts=False)
        self._ser.rts = True
        self._ser.dtr = True
        self._win32_flush()
        return True
    def _win32_flush(self):
        if os.name != 'nt' or not self._ser:
            return
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            handle = ctypes.c_void_p(int(self._ser._port_handle))
            k32.ClearCommBreak(handle)
            k32.EscapeCommFunction(handle, 3)
            k32.EscapeCommFunction(handle, 5)
            k32.PurgeComm(handle, 15)
            k32.FlushFileBuffers(handle)
            return
        except Exception:
            return
    def _close_serial(self):
        if self._ser and self._ser.is_open:
            try:
                self._ser.close()
            except Exception:
                pass
        self._ser = None
    def _read_until_quiet(self, timeout=2.0, poll=0.2):
        if not self._ser:
            return b''
        buf = bytearray()
        start = time.monotonic()
        last_data = start
        while time.monotonic() - start < timeout:
            waiting = self._ser.in_waiting
            if waiting > 0:
                buf.extend(self._ser.read(waiting))
                last_data = time.monotonic()
            elif buf and time.monotonic() - last_data >= poll:
                break
            time.sleep(0.02)
        return bytes(buf)
    def _exchange(self, frame, timeout=2.0):
        if not self._ser:
            return b''
        try:
            self._ser.reset_input_buffer()
        except Exception:
            pass
        self._ser.write(frame)
        self._ser.flush()
        try:
            import ctypes
            ctypes.windll.kernel32.FlushFileBuffers(ctypes.c_void_p(int(self._ser._port_handle)))
        except Exception:
            pass
        return self._read_until_quiet(timeout=timeout, poll=0.2)
    def _next_seq(self):
        s = self._seq
        self._seq += 1
        return s & 65535
    @staticmethod
    def _xor_checksum(data):
        result = 0
        for b in data:
            result ^= b
        return result
    def _frame_with_seq(self, template):
        if len(template) < 12:
            return template
        body = bytearray(template[:-1])
        struct.pack_into('<H', body, 8, self._next_seq())
        return bytes(body) + bytes([self._xor_checksum(bytes(body))])
    @staticmethod
    def _contains_meta_response(data):
        if not data or len(data) < 4:
            return False
        if data[0] == 85:
            return True
        return b'U\x00' in data
    MAGIC = bytes([172, 219, 207, 229])
    _CMD_INIT = 8
    _CMD_GET_INFO = 133
    _CMD_PREPARE = 143
    _CMD_READ_PROP = 137
    _CMD_NEGOTIATE = 159
    _CMD_SETUP = 123
    _CMD_CONTROL = 10
    def _build_meta_packet(self, sub_cmd, data=None, data_payload_size=0):
        data = data or b''
        payload_len = 4 + len(data)
        total_size = payload_len + 4
        packet = bytes([85])
        packet += struct.pack('>H', total_size)
        packet += bytes([102])
        if data_payload_size > 0:
            header_size = payload_len - data_payload_size
            packet += struct.pack('<HH', header_size, data_payload_size)
        else:
            packet += struct.pack('<I', payload_len)
        packet += struct.pack('<H', self._next_seq())
        packet += bytes([sub_cmd, 0])
        packet += data
        return packet + bytes([self._xor_checksum(packet)])
    def _init_session(self, log_cb=None):
        log = log_cb or _noop_log
        if not self._ser:
            raise RuntimeError('Porta nao aberta')
        try:
            self._ser.reset_input_buffer()
        except Exception:
            pass
        self._ser.write(self.MAGIC)
        self._ser.write(self.MAGIC)
        self._ser.flush()
        rx = self._exchange(self._build_meta_packet(self._CMD_INIT, b'\x00\x00\x00\x00'), timeout=3.0)
        if not self._contains_meta_response(rx):
            time.sleep(0.1)
            rx = self._exchange(self._build_meta_packet(self._CMD_INIT, b'\x00\x00\x00\x00'), timeout=3.0)
            if not self._contains_meta_response(rx):
                raise RuntimeError('Falha na inicializacao')
        logger.debug('INIT: rx %dB', len(rx))
        rx = self._exchange(self._build_meta_packet(self._CMD_NEGOTIATE, b'\x01\x00\x08\x00'), timeout=1.5)
        logger.debug('NEGOTIATE: rx %dB', len(rx))
        rx = self._exchange(self._build_meta_packet(self._CMD_SETUP, b'\x00\x00\x00\x00'), timeout=1.5)
        logger.debug('SETUP: rx %dB', len(rx))
        rx = self._exchange(self._build_meta_packet(self._CMD_GET_INFO), timeout=3.0)
        if not rx:
            raise RuntimeError('Falha na inicializacao')
        logger.debug('START: rx %dB', len(rx))
        log('Sessao estabelecida.')
        return rx
    def _open_session(self, port, log_cb=None):
        log = log_cb or _noop_log
        if self._cancelado:
            raise RuntimeError('Operacao cancelada')
        self._close_serial()
        log('Estabelecendo conexao...')
        self._cancelado = False
        self._seq = 1
        for baud in (115200, 921600):
            if self._cancelado:
                raise RuntimeError('Operacao cancelada')
            try:
                if self._ser and self._ser.is_open:
                    self._ser.close()
                self._open_serial(port, baud)
                self._read_until_quiet(timeout=0.2, poll=0.1)
                self._init_session(log_cb=log)
            except Exception as e:
                logger.debug('Sessao falhou @ %d: %s', baud, e)
                if self._ser and self._ser.is_open:
                    try:
                        self._ser.close()
                    except Exception:
                        pass
                self._ser = None
                self._seq = 1
                time.sleep(0.1)
            return
        raise RuntimeError('Falha ao estabelecer sessao')
        self._ser = None
        self._seq = 1
        time.sleep(0.1)
        e = None
        del e, e
        e = None
    def _build_read_prop(self, idx, prop_name):
        payload_len = 68
        size = payload_len + 4
        prop_padded = prop_name.encode('ascii')[:64].ljust(64, b'\x00')
        packet = bytes([85])
        packet += struct.pack('>H', size)
        packet += bytes([102])
        packet += struct.pack('<I', payload_len)
        packet += struct.pack('<H', idx)
        packet += bytes([137, 0])
        packet += prop_padded
        return packet + bytes([self._xor_checksum(packet)])
    def _parse_prop_value(self, data):
        if len(data) < 15:
            return ''
        marker = bytes([85, 0, 141, 96])
        idx = data.find(marker)
        if idx < 0:
            return ''
        raw = data[idx + 12:]
        nul = raw.find(b'\x00')
        if nul > 0:
            raw = raw[:nul]
        try:
            return raw.decode('ascii', errors='replace').strip()
        except Exception:
            return ''
    def read_info(self, port, log_cb=None) -> dict:
        log = log_cb or _noop_log
        try:
            self._open_session(port, log_cb)
            self._exchange(self._build_meta_packet(self._CMD_GET_INFO), timeout=3.0)
            props = {}
            for idx, prop_name in enumerate(_core.PROPS_READ_INFO, start=2):
                pkt = self._build_read_prop(idx, prop_name)
                resp = self._exchange(pkt, timeout=1.5)
                val = self._parse_prop_value(resp)
                if not val:
                    continue
                if val != 'unknown':
                    props[prop_name] = val
                    short = prop_name.split('.')[-1]
                    log(f'{short!s}: {val!s}')
            if not props:
                log('Nenhuma propriedade lida.')
        except Exception as e:
            logger.debug('read_info error: %s', e)
            log('Falha na leitura.')
            self._close_serial()
            return {}
        finally:
            self._close_serial()
        return props
    def diagnostics(self, port, log_cb=None) -> dict:
        log = log_cb or _noop_log
        try:
            self._open_session(port, log_cb)
            result = {}
            log('Verificando armazenamento...')
            emmc_items = [('emmc_name', '/sys/class/mmc_host/mmc0/mmc0:0001/name'), ('emmc_manfid', '/sys/class/mmc_host/mmc0/mmc0:0001/manfid'), ('emmc_life_time', '/sys/class/mmc_host/mmc0/mmc0:0001/life_time'), ('emmc_pre_eol', '/sys/class/mmc_host/mmc0/mmc0:0001/pre_eol_info'), ('emmc_date', '/sys/class/mmc_host/mmc0/mmc0:0001/date'), ('emmc_serial', '/sys/class/mmc_host/mmc0/mmc0:0001/serial'), ('emmc_cid', '/sys/class/mmc_host/mmc0/mmc0:0001/cid')]
            for key, path in emmc_items:
                val = self._shell_cat(path)
                if val:
                    result[key] = val
            if 'emmc_manfid' in result:
                result['emmc_fabricante'] = _core.decode_emmc_manufacturer(result['emmc_manfid'])
                log(f'eMMC: {result['emmc_fabricante']!s} {result.get('emmc_name', '')!s}')
            if 'emmc_life_time' in result:
                result['emmc_saude'] = _core.interpret_life_time(result['emmc_life_time'])
                log('Vida util: %s' % result['emmc_saude'])
            if 'emmc_pre_eol' in result:
                result['emmc_eol'] = _core.interpret_pre_eol(result['emmc_pre_eol'])
                log('Status EOL: %s' % result['emmc_eol'])
            log('Verificando bateria...')
            batt_items = [('bat_status', '/sys/class/power_supply/battery/status'), ('bat_capacity', '/sys/class/power_supply/battery/capacity'), ('bat_voltage', '/sys/class/power_supply/battery/voltage_now'), ('bat_current', '/sys/class/power_supply/battery/current_now'), ('bat_temp', '/sys/class/power_supply/battery/temp'), ('bat_health', '/sys/class/power_supply/battery/health'), ('bat_tech', '/sys/class/power_supply/battery/technology'), ('bat_full', '/sys/class/power_supply/battery/charge_full'), ('bat_design', '/sys/class/power_supply/battery/charge_full_design')]
            for key, path in batt_items:
                val = self._shell_cat(path)
                if val:
                    result[key] = val
            if 'bat_voltage' in result and result['bat_voltage'].isdigit():
                v = int(result['bat_voltage']) / 1000000
                result['bat_voltage_v'] = '%.3f' % v
            if 'bat_temp' in result and result['bat_temp'].lstrip('-').isdigit():
                t = int(result['bat_temp']) / 10
                result['bat_temp_c'] = '%.1f' % t
            if 'bat_current' in result and result['bat_current'].lstrip('-').isdigit():
                ma = int(result['bat_current']) / 1000
                result['bat_current_ma'] = '%.1f' % ma
            if 'bat_full' in result and result['bat_full'].isdigit():
                mah = int(result['bat_full']) / 1000
                result['bat_mah'] = '%.0f' % mah
            bat_parts = []
            if 'bat_capacity' in result:
                bat_parts.append('%s%%' % result['bat_capacity'])
            if 'bat_voltage_v' in result:
                bat_parts.append('%sV' % result['bat_voltage_v'])
            if 'bat_temp_c' in result:
                bat_parts.append('%sC' % result['bat_temp_c'])
            if 'bat_health' in result:
                bat_parts.append(result['bat_health'])
            if 'bat_mah' in result:
                bat_parts.append('%s mAh' % result['bat_mah'])
            if bat_parts:
                log('Bateria: %s' % ' | '.join(bat_parts))
            log('Verificando processador...')
            cores = self._shell_cmd("grep -c '^processor' /proc/cpuinfo")
            if cores and cores.isdigit():
                result['cpu_cores'] = cores
            model = self._shell_cmd("grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2")
            if model:
                result['cpu_modelo'] = model.strip()
            freq = self._shell_cat('/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq')
            if freq and freq.isdigit():
                mhz = int(freq) / 1000
                result['cpu_freq_mhz'] = '%.0f' % mhz
            cpu_parts = []
            if 'cpu_cores' in result:
                cpu_parts.append('%s cores' % result['cpu_cores'])
            if 'cpu_modelo' in result:
                cpu_parts.append(result['cpu_modelo'])
            if 'cpu_freq_mhz' in result:
                cpu_parts.append('%s MHz' % result['cpu_freq_mhz'])
            if cpu_parts:
                log('CPU: %s' % ' | '.join(cpu_parts))
            log('Verificando memoria...')
            mem_total = self._shell_cmd("grep 'MemTotal' /proc/meminfo | awk '{print $2}'")
            if mem_total and mem_total.isdigit():
                gb = int(mem_total) / 1024 / 1024
                result['ram_total_gb'] = '%.1f' % gb
                log('RAM: %.1f GB' % gb)
            mem_avail = self._shell_cmd("grep 'MemAvailable' /proc/meminfo | awk '{print $2}'")
            if mem_avail and mem_avail.isdigit():
                mb = int(mem_avail) / 1024
                result['ram_livre_mb'] = '%.0f' % mb
            log('Verificando storage...')
            for dev in ('mmcblk0', 'sda'):
                sz = self._shell_cat('/sys/class/block/%s/size' % dev)
                if not sz:
                    continue
                if not sz.isdigit():
                    continue
                if not int(sz) > 0:
                    continue
                gb = int(sz) * 512 / 1073741824
                result['storage_gb'] = '%.1f' % gb
                result['storage_dev'] = dev
                log('Storage: %.1f GB (%s)' % (gb, dev))
                break
            log('Diagnostico concluido: %d itens.' % len(result))
        except Exception as e:
            logger.debug('diagnostics error: %s', e)
            log('Falha no diagnostico.')
            self._close_serial()
            return {}
        finally:
            self._close_serial()
        return result
    def hw_diagnostics(self, port, log_cb=None) -> dict:
        log = log_cb or _noop_log
        try:
            self._open_session(port, log_cb)
            from . import _mit_hw_diag as _hw
        except Exception as e:
            logger.debug('hw_diagnostics error: %s', e)
            log('Falha no diagnostico de hardware.')
            self._close_serial()
            return {}
        finally:
            self._close_serial()
        return _hw.run_diagnostics(shell_fn=self._shell_cmd, log_fn=log)
    def erase_frp(self, port, log_cb=None) -> Tuple[bool, str]:
        log = log_cb or _noop_log
        try:
            self._open_session(port, log_cb)
            log('Localizando protecao...')
            storage = self._shell_cmd('ls /dev/block/sdc 2>/dev/null && echo sdc || echo mmcblk0')
            frp_path = self._shell_cmd('readlink -f /dev/block/by-name/frp 2>/dev/null')
            if not frp_path or '/dev/block' not in frp_path:
                self._close_serial()
                return (False, 'Protecao nao encontrada')
            frp_block = posixpath.basename(frp_path)
            start = self._shell_cmd('cat /sys/class/block/%s/start 2>/dev/null' % frp_block)
            size = self._shell_cmd('cat /sys/class/block/%s/size 2>/dev/null' % frp_block)
            if not start or not start.isdigit() or not size or not size.isdigit():
                self._close_serial()
                return (False, 'Parametros invalidos')
            start_i = int(start)
            count = min(int(size), 10)
            dd_cmd = 'dd if=/dev/zero of=/dev/block/%s bs=512 count=%d seek=%d conv=notrunc 2>/dev/null' % (storage, count, start_i)
            b64 = base64.b64encode(dd_cmd.encode()).decode()
            log('Processando...')
            result = self._shell_cmd("echo -n '%s' | base64 -d | sh; sync; echo EXIT:$?" % b64, timeout=15.0)
            if 'EXIT:0' in (result or ''):
                log('Operacao concluida.')
                self._close_serial()
                return (True, 'Operacao concluida')
        except Exception as e:
            logger.debug('erase_frp error: %s', e)
            self._close_serial()
            return (False, 'Falha na operacao')
        finally:
            self._close_serial()
        return (False, 'Falha no processamento')
    def _build_factory_pkt(self):
        header = struct.pack('<H', 12)
        header += struct.pack('<H', 8)
        header += struct.pack('<H', self._next_seq())
        header += bytes([121, 0])
        header += b'\x00\x00\x00\x00'
        header += struct.pack('<I', 1)
        header += struct.pack('<H', 0)
        header += struct.pack('<H', 1)
        header += struct.pack('<H', 0)
        header += struct.pack('<H', 1)
        packet = b'U' + struct.pack('>H', len(header)) + b'f' + header
        return packet + bytes([self._xor_checksum(packet)])
    def factory_reset(self, port, log_cb=None) -> Tuple[bool, str]:
        log = log_cb or _noop_log
        try:
            self._open_session(port, log_cb)
            log('Preparando reset...')
            for recovery_path in ('/cache/recovery/command', '/data/misc/recovery/command'):
                self._shell_cmd(f"mkdir -p {recovery_path.rsplit('/', 1)[0]!s} 2>/dev/null; echo '--wipe_data' > {recovery_path!s} 2>/dev/null", timeout=5.0)
            self._shell_cmd('settings delete secure user_setup_complete 2>/dev/null', timeout=3.0)
            self._shell_cmd('settings delete global device_provisioned 2>/dev/null', timeout=3.0)
            log('Executando reset...')
            try:
                pkt = self._build_factory_pkt()
                self._exchange(pkt, timeout=10.0)
            except Exception:
                pass
            try:
                pkt = self._build_meta_packet(self._CMD_CONTROL, b'\x02\x00\x00\x00')
                self._exchange(pkt, timeout=5.0)
            except Exception:
                pass
            else:
                log('Reiniciando dispositivo...')
        except (serial.SerialException, OSError):
            log('Dispositivo reiniciou.')
        except Exception as e:
            logger.debug('factory_reset error: %s', e)
            try:
                pass
            finally:
                self._close_serial()
            return (False, 'Falha na operacao')
        try:
            pkt = self._build_meta_packet(self._CMD_CONTROL, b'\x00\x00\x00\x00')
            self._exchange(pkt, timeout=5.0)
        except (serial.SerialException, OSError):
            log('Dispositivo reiniciou.')
        except Exception as e:
            logger.debug('factory_reset error: %s', e)
            try:
                try:
                    pass
                except Exception:
                    pass
            finally:
                self._close_serial()
            return (False, 'Falha na operacao')
        log('Dispositivo reiniciando com reset...')
        self._close_serial()
        return (True, 'Reset concluido')
    def reboot(self, port, log_cb=None) -> Tuple[bool, str]:
        log = log_cb or _noop_log
        try:
            self._open_session(port, log_cb)
            log('Reiniciando dispositivo...')
            pkt = self._build_meta_packet(self._CMD_CONTROL, b'\x00\x00\x00\x00')
            self._exchange(pkt, timeout=3.0)
            log('Dispositivo reiniciando...')
        except (serial.SerialException, OSError):
            log('Dispositivo reiniciou.')
        except Exception as e:
            logger.debug('reboot error: %s', e)
            self._close_serial()
            return (False, 'Falha na operacao')
        finally:
            self._close_serial()
        return (True, 'Reiniciado')
    def factory_reset_new(self, port, log_cb=None) -> Tuple[bool, str]:
        log = log_cb or _noop_log
        try:
            self._open_session(port, log_cb)
            log('Preparando operacao...')
            try:
                pkt = self._build_meta_packet(self._CMD_PREPARE, b'0\x00\x00\x00')
                rx = self._exchange(pkt, timeout=3.0)
                if rx:
                    logger.debug('PREPARE: rx %dB', len(rx))
            except Exception:
                logger.debug('prepare: sem resposta')
            else:
                log('Executando reset...')
        except (serial.SerialException, OSError):
            log('Dispositivo reiniciou.')
        except Exception as e:
            logger.debug('factory_reset_new: %s', e)
            try:
                pass
            finally:
                self._close_serial()
            return (False, 'Falha na operacao')
        try:
            pkt = self._build_factory_pkt()
            rx = self._exchange(pkt, timeout=10.0)
            if rx and self._contains_meta_response(rx):
                logger.debug('factory_new: rx %dB', len(rx))
        except Exception:
            pass
        for rpath in ('/cache/recovery/command', '/data/misc/recovery/command'):
            self._shell_cmd(f"mkdir -p {rpath.rsplit('/', 1)[0]!s} 2>/dev/null; echo '--wipe_data' > {rpath!s} 2>/dev/null", timeout=5.0)
        self._shell_cmd('settings delete secure user_setup_complete 2>/dev/null', timeout=3.0)
        self._shell_cmd('settings delete global device_provisioned 2>/dev/null', timeout=3.0)
        log('Reiniciando dispositivo...')
        try:
            pkt = self._build_meta_packet(self._CMD_CONTROL, b'\x02\x00\x00\x00')
            self._exchange(pkt, timeout=5.0)
        except Exception:
            pass
        try:
            pkt = self._build_meta_packet(self._CMD_CONTROL, b'\x00\x00\x00\x00')
            self._exchange(pkt, timeout=5.0)
        except (serial.SerialException, OSError):
            log('Dispositivo reiniciou.')
        except Exception as e:
            logger.debug('factory_reset_new: %s', e)
            try:
                try:
                    pass
                except Exception:
                    pass
            finally:
                self._close_serial()
            return (False, 'Falha na operacao')
        log('Dispositivo reiniciando com reset...')
        self._close_serial()
        return (True, 'Reset concluido')
    def frp_erase_new(self, port, log_cb=None) -> Tuple[bool, str]:
        log = log_cb or _noop_log
        try:
            self._open_session(port, log_cb)
            log('Localizando protecao...')
            frp_offset = None
            storage_dev = None
            log('Analisando tabela de particoes...')
            try:
                frp_offset, storage_dev = self._gpt_find_frp()
            except Exception as e:
                logger.debug('frp_erase_new: %s', e)
                try:
                    try:
                        pass
                    except Exception:
                        logger.debug('metodo 1 falhou, tentando alternativo')
                finally:
                    self._close_serial()
                return (False, 'Falha na operacao')
            else:
                if frp_offset is None:
                    log('Usando metodo alternativo...')
                    storage = self._shell_cmd('ls /dev/block/sdc 2>/dev/null && echo sdc || echo mmcblk0')
                    frp_path = self._shell_cmd('readlink -f /dev/block/by-name/frp 2>/dev/null')
                    if frp_path and '/dev/block' in frp_path:
                        frp_block = posixpath.basename(frp_path)
                        start = self._shell_cmd('cat /sys/class/block/%s/start 2>/dev/null' % frp_block)
                        if start and start.isdigit():
                            frp_offset = int(start) * 512
                            storage_dev = storage.strip() if storage else 'mmcblk0'
                if frp_offset is None or storage_dev is None:
                    self._close_serial()
                    return (False, 'Protecao nao encontrada')
                log('Processando...')
                dd_cmd = 'dd if=/dev/zero of=/dev/block/%s bs=1 count=256 seek=%d conv=notrunc 2>/dev/null' % (storage_dev, frp_offset)
                b64 = base64.b64encode(dd_cmd.encode()).decode()
                result = self._shell_cmd("echo -n '%s' | base64 -d | sh; sync; echo EXIT:$?" % b64, timeout=15.0)
                if 'EXIT:0' in (result or ''):
                    log('Operacao concluida.')
        except Exception as e:
            logger.debug('frp_erase_new: %s', e)
            try:
                pass
            finally:
                self._close_serial()
            return (False, 'Falha na operacao')
        self._close_serial()
        return (False, 'Falha no processamento')
    def _gpt_find_frp(self) -> Tuple[Optional[int], Optional[str]]:
        for dev in ('sdc', 'mmcblk0'):
            gpt_header_b64 = self._shell_cmd('dd if=/dev/block/%s bs=512 skip=1 count=1 2>/dev/null | base64 -w 0' % dev, timeout=5.0)
            if not gpt_header_b64:
                continue
            try:
                header = base64.b64decode(gpt_header_b64)
            except Exception:
                continue
            if header[:8] != b'EFI PART':
                continue
            storage_dev = dev
            for sector in range(2, 34):
                sector_b64 = self._shell_cmd('dd if=/dev/block/%s bs=512 skip=%d count=1 2>/dev/null | base64 -w 0' % (dev, sector), timeout=3.0)
                if sector_b64:
                    try:
                        sector_data = base64.b64decode(sector_b64)
                    except Exception:
                        continue
                    for i in range(0, len(sector_data), 128):
                        entry = sector_data[i:i + 128]
                        if len(entry) < 128:
                            break
                        if entry[:16] == b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00':
                            continue
                        try:
                            name = entry[56:128].decode('utf-16-le').rstrip('\x00').lower()
                        except Exception:
                            continue
                        if name == 'frp':
                            start_lba = struct.unpack_from('<Q', entry, 32)[0]
                            offset = start_lba * 512
                            logger.debug('encontrado: LBA=%d offset=%d dev=%s', start_lba, offset, storage_dev)
                            return offset, storage_dev
            continue
        return (None, None)
    def remove_payjoy(self, port, log_cb=None) -> Tuple[bool, str]:
        log = log_cb or _noop_log
        try:
            self._open_session(port, log_cb)
            log('Verificando dispositivo...')
            build_id = ''
            prod_name = ''
            for idx, pname in enumerate(('ro.build.display.id', 'ro.product.name'), start=2):
                pkt = self._build_read_prop(idx, pname)
                resp = self._exchange(pkt, timeout=1.5)
                val = self._parse_prop_value(resp)
                if not val:
                    pass
                if val == 'unknown':
                    pass
                if pname == 'ro.build.display.id':
                    build_id = val
                else:
                    prod_name = val
                log(f'{pname.split('.')[-1]!s}: {val!s}')
            has_pyj = _core.PYJ_INDICATOR in build_id or _core.PYJ_INDICATOR in prod_name or '-PJ-' in build_id
            if not has_pyj:
                log('Indicador nao detectado neste dispositivo.')
                self._close_serial()
                return (False, 'Dispositivo sem indicador compativel')
            log('Indicador detectado.')
            log('Configurando dispositivo...')
            for cmd in _core.PYJ_SETTINGS:
                pass
            try:
                self._exec_shell(cmd, timeout=5.0)
            except Exception:
                pass
            else:
                log('Autenticando...')
                auth_ok = False
                for key in _core.PYJ_AUTH_KEYS:
                    pass
        except Exception as e:
            logger.debug('remove_payjoy error: %s', e)
            try:
                pass
            finally:
                self._close_serial()
            return (False, 'Falha na operacao')
        if not auth_ok:
            log('Autenticacao nao confirmada, tentando continuar...')
        log('Processando particao...')
        dd_cmd = _core.PYJ_DD_CMD % (_core.PYJ_PROINFO_OFFSET, _core.PYJ_PROINFO_SIZE)
        b64 = base64.b64encode(dd_cmd.encode()).decode()
        result = self._shell_cmd("echo -n '%s' | base64 -d | sh; sync; echo EXIT:$?" % b64, timeout=15.0)
        if 'EXIT:0' not in (result or ''):
            log('Falha na escrita.')
            self._close_serial()
            return (False, 'Falha ao processar particao')
        try:
            log('Escrita concluida.')
            log('Verificando...')
            verify_cmd = "dd if=/dev/block/by-name/proinfo bs=1 skip=%d count=32 2>/dev/null | od -An -tx1 -v | tr -d ' \\n'" % _core.PYJ_PROINFO_OFFSET
            verify = self._shell_cmd("printf 'S0F:'; %s; printf ':E0F'" % verify_cmd, timeout=5.0)
            if verify and verify.replace('0', '') == '':
                log('Verificacao: area zerada com sucesso.')
            else:
                log('Verificacao: dados escritos.')
            log('Operacao concluida.')
        except Exception as e:
            logger.debug('remove_payjoy error: %s', e)
            try:
                pass
            finally:
                self._close_serial()
            return (False, 'Falha na operacao')
        self._close_serial()
        return (True, 'Operacao concluida')
    def _build_shell_packet(self, cmd):
        header = struct.pack('<I', 67633164)
        header += struct.pack('<H', 62)
        header += bytes([121, 0])
        header += b'\x00\x00\x00\x00'
        header += struct.pack('<I', 3)
        header += struct.pack('<H', 1024)
        header += struct.pack('<H', 1)
        header += struct.pack('<H', 0)
        header += struct.pack('<H', 1)
        cmd_bytes = cmd.encode('utf-8')[:1024]
        cmd_padded = cmd_bytes + b'\x00' * (1024 - len(cmd_bytes))
        packet = b'U\x04\x18f' + header + cmd_padded
        return packet + bytes([self._xor_checksum(packet)])
    def _exec_shell(self, cmd, timeout=10.0):
        packet = self._build_shell_packet(cmd)
        resp = self._exchange(packet, timeout=timeout)
        if not resp:
            return ''
        text = resp.decode('ascii', errors='replace')
        return _core.parse_shell_response(text)
    def _shell_cat(self, path):
        try:
            val = self._exec_shell("printf 'S0F:'; cat %s 2>/dev/null; printf ':E0F'" % path, timeout=3.0)
            if val:
                return val.strip()
            return ''
        except Exception:
            return ''
    def _shell_cmd(self, cmd, timeout=5.0):
        try:
            val = self._exec_shell("printf 'S0F:'; %s; printf ':E0F'" % cmd, timeout=timeout)
            if val:
                return val.strip()
            return ''
        except Exception:
            return ''
