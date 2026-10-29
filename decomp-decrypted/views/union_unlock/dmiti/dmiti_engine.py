import base64
import logging
import os
import re
import struct
import subprocess
import sys
import time
from typing import (Callable, Dict, List, Optional, Tuple)
from ._dmiti_core import (FRAME_DELIMITER, FRAME_HEADER_SIZE, DEFAULT_BAUD, BUFFER_SIZE, DCB_FLAGS, TIMEOUT_READ_INTERVAL, TIMEOUT_READ_MULTIPLIER, TIMEOUT_READ_CONSTANT, TIMEOUT_WRITE_MULTIPLIER, TIMEOUT_WRITE_CONSTANT, MAX_OPEN_RETRIES, OPEN_RETRY_DELAY_MS, INIT_START_SEQ, INIT_PAYLOADS, INIT_CMD_TIMEOUT_MS, BOOT_DIAG_SWITCH_SEQ, BOOT_DIAG_SWITCH_PAYLOAD, BOOT_DIAG_SWITCH_TIMEOUT_MS, PRIVILEGE_ELEVATE_SEQ, PRIVILEGE_ELEVATE_PAYLOAD, PRIVILEGE_ELEVATE_TIMEOUT_MS, FACTORY_RESET_TIMEOUT_MS, AT_PREFIX, SPRD_KEYWORDS, SCAN_POLL_MS, PYJ_MARKER, PYJ_READ_OFFSET, PYJ_READ_SIZE, PYJ_WRITE_CHUNK, PYJ_PATCH_SIZE, ADB_ENABLE_COMMANDS, PROPS_READ_INFO, SEC_PLUGIN_SECTORS, SEC_PLUGIN_DETECT_SECTOR, SEC_PLUGIN_DETECT_PATTERN, SEC_PYJ_SECTOR, SEC_PYJ_MARKER, frame_build, only_base64, parse_shell_response, sanitize_log, build_patch)
logger = logging.getLogger(__name__)
try:
    import serial
    import serial.tools.list_ports
    _HAS_SERIAL = True
except ImportError:
    _HAS_SERIAL = False
LogCallback = Optional[Callable[[str], None]]
def _noop(msg: str) -> None:
    pass
class DmitiPortScanner:
    def __init__(self):
        self._cache = []
        self._cache_time = 0.0
    def scan(self) -> List[dict]:
        now = time.time()
        if now - self._cache_time < SCAN_POLL_MS / 1000.0:
            return self._cache
        self._cache = self._scan_internal()
        self._cache_time = now
        return self._cache
    def scan_sprd_only(self) -> List[dict]:
        return [p for p in self.scan() if p.get('likely_sprd')]
    def wait_port(self, timeout_s: float=60.0, exclude: str='', log_cb: LogCallback=None) -> str:
        cb = log_cb or _noop
        logger.debug(f'wait_port timeout={timeout_s}s exclude={exclude}')
        inicio = time.time()
        iniciais = set()
        primeiro = True
        while time.time() - inicio < timeout_s:
            self._cache_time = 0
            portas = self.scan()
            elapsed = time.time() - inicio
            if primeiro:
                iniciais = {p['port'] for p in portas}
                primeiro = False
            for p in portas:
                if not p.get('likely_sprd'):
                    continue
                if p['port'] != exclude:
                    cb('Dispositivo detectado!')
                    logger.debug(f'SPRD encontrada: {p['port']}')
                    return p['port']
            if elapsed > 7.0 and exclude:
                for p in portas:
                    if not p.get('likely_sprd'):
                        continue
                    if p['port'] == exclude:
                        cb('Dispositivo reconectado!')
                        logger.debug(f'SPRD re-enumerate: {p['port']}')
                        return p['port']
            if elapsed > 12.0:
                atuais = {p['port'] for p in portas}
                novas = atuais - iniciais - {exclude}
                if novas:
                    porta = sorted(novas)[0]
                    cb('Dispositivo detectado!')
                    logger.debug(f'Nova porta: {porta}')
                    return porta
            time.sleep(SCAN_POLL_MS / 1000.0)
        raise TimeoutError(f'Nenhuma porta detectada em {timeout_s}s')
    def _scan_internal(self) -> List[dict]:
        portas = []
        try:
            portas = self._scan_powershell()
        except Exception:
            pass
        if not portas:
            try:
                portas = self._scan_pyserial()
            except Exception:
                pass
            return portas
        return portas
    def _scan_powershell(self) -> List[dict]:
        cmd = 'Get-CimInstance Win32_PnPEntity -Filter "Name LIKE \'%(COM%\'" | Select-Object Name,PNPDeviceID | ConvertTo-Csv -NoTypeInformation'
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        result = subprocess.run(['powershell', '-NoProfile', '-Command', cmd], capture_output=True, text=True, timeout=8, startupinfo=si)
        portas = []
        for line in result.stdout.splitlines()[1:]:
            match = re.search('\\(COM(\\d+)\\)', line)
            if match:
                port = f'COM{match.group(1)}'
                name = line.strip('"').split('","')[0] if '","' in line else line
                pnp = line.strip('"').split('","')[1] if '","' in line else ''
                likely = self._is_sprd(name, pnp)
                portas.append({'port': port, 'name': name, 'pnp': pnp, 'likely_sprd': likely})
        return portas
    def _scan_pyserial(self) -> List[dict]:
        if not _HAS_SERIAL:
            return []
        portas = []
        for p in serial.tools.list_ports.comports():
            portas.append({'port': p.device, 'name': p.description or '', 'pnp': p.hwid or '', 'likely_sprd': self._is_sprd(p.description or '', p.hwid or '')})
        return portas
    @staticmethod
    def _is_sprd(name: str, pnp: str) -> bool:
        combined = (name + ' ' + pnp).upper()
        return any((kw in combined for kw in SPRD_KEYWORDS))
class DmitiClient:
    def __init__(self):
        self._serial = None
        self._porta = ''
        self._conectado = False
        self._sequence = INIT_START_SEQ
        self._cancelado = False
    @property
    def conectado(self) -> bool:
        return self._conectado
    @property
    def porta(self) -> str:
        return self._porta
    def cancelar(self):
        self._cancelado = True
    def abrir(self, porta: str, log_cb: LogCallback=None) -> bool:
        cb = log_cb or _noop
        if not _HAS_SERIAL:
            cb('Modulo serial nao disponivel')
            return False
        logger.debug(f'Abrindo {porta} (max {MAX_OPEN_RETRIES} tentativas)')
        ultimo_erro = ''
        for tentativa in range(1, MAX_OPEN_RETRIES + 1):
            if self._cancelado:
                return False
            try:
                self._serial = serial.Serial(port=porta, baudrate=DEFAULT_BAUD, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0.1, write_timeout=5.0, inter_byte_timeout=0.02, dsrdtr=False, rtscts=False)
                self._serial.set_buffer_size(rx_size=BUFFER_SIZE, tx_size=BUFFER_SIZE)
                self._patch_dcb()
                self._serial.dtr = True
                self._serial.rts = True
                self._serial.reset_input_buffer()
                self._serial.reset_output_buffer()
                self._porta = porta
                self._conectado = True
                self._sequence = INIT_START_SEQ
                logger.debug(f'{porta} aberta (tentativa {tentativa})')
            except FileNotFoundError:
                ultimo_erro = 'Porta nao encontrada'
                time.sleep(0.5 if tentativa < 5 else OPEN_RETRY_DELAY_MS / 1000.0)
            except Exception as e:
                ultimo_erro = str(e)
                if tentativa < MAX_OPEN_RETRIES:
                    time.sleep(OPEN_RETRY_DELAY_MS / 1000.0)
            return True
        cb('Falha na conexao com dispositivo')
        logger.error(f'Falha ao abrir {porta}: {ultimo_erro}')
        return False
    def fechar(self, log_cb: LogCallback=None):
        if self._serial:
            try:
                self._serial.close()
                logger.debug(f'{self._porta} fechada')
            except Exception:
                pass
        self._serial = None
        self._conectado = False
    def init(self, log_cb: LogCallback=None) -> bool:
        cb = log_cb or _noop
        if not self._serial:
            return False
        logger.debug(f'Init seq_start={INIT_START_SEQ}')
        self._sequence = INIT_START_SEQ
        for i, payload in enumerate(INIT_PAYLOADS):
            if self._cancelado:
                return False
            resp = self._send(payload, INIT_CMD_TIMEOUT_MS, strict=False)
            logger.debug(f'Init cmd {i + 1}/6: {len(resp)}B')
        return True
    def boot_diag_switch(self, log_cb: LogCallback=None) -> bool:
        if not self._serial:
            return False
        frame = frame_build(BOOT_DIAG_SWITCH_SEQ, BOOT_DIAG_SWITCH_PAYLOAD)
        logger.debug(f'Boot Diag TX: {frame.hex(' ')}')
        try:
            self._write_raw(frame)
            self._read_until_timeout(BOOT_DIAG_SWITCH_TIMEOUT_MS)
        except Exception:
            logger.debug('Boot diag switch: device desconectou (normal)')
        return True
    def privilege_elevate(self, log_cb: LogCallback=None) -> bool:
        if not self._serial:
            return False
        frame = frame_build(PRIVILEGE_ELEVATE_SEQ, PRIVILEGE_ELEVATE_PAYLOAD)
        try:
            self._write_raw(frame)
            resp = self._read_until_timeout(PRIVILEGE_ELEVATE_TIMEOUT_MS)
            return b'\xfe\xff' in resp or len(resp) > 0
        except Exception:
            return False
    def shell(self, command: str, timeout_ms: int=8000, log_cb: LogCallback=None) -> str:
        at_text = f'AT+SHELL="{command}"'
        at_bytes = at_text.encode('ascii')
        payload = bytearray(len(at_bytes) + 2)
        payload[0] = 104
        payload[1] = 0
        payload[2:] = at_bytes
        resp_bytes = self._send(bytes(payload), timeout_ms, strict=True)
        if not resp_bytes:
            return ''
        raw_text = resp_bytes.decode('ascii', errors='replace')
        return parse_shell_response(raw_text, command)
    def send_factory_reset(self, log_cb: LogCallback=None) -> bytes:
        cb = log_cb or _noop
        try:
            r = self.shell('getprop ro.product.model', timeout_ms=5000)
            modelo = r.strip()[:30] if r else ''
            if modelo:
                cb(f'Dispositivo: {modelo}')
        except Exception:
            pass
        try:
            self.shell('sync', timeout_ms=4000)
        except Exception:
            pass
        try:
            self.shell('setprop persist.service.adb.enable 1 2>/dev/null', timeout_ms=5000)
        except Exception:
            pass
        cb('Enviando comando de reset...')
        at_text = 'AT+SPDIAG="AT+ETSRESET"\r\n'
        at_bytes = at_text.encode('ascii')
        payload = bytearray(len(at_bytes) + 2)
        payload[0] = 104
        payload[1] = 0
        payload[2:] = at_bytes
        return self._send(bytes(payload), FACTORY_RESET_TIMEOUT_MS, strict=True)
    def _send_at_raw(self, at_cmd: str, timeout_ms: int) -> bytes:
        at_bytes = at_cmd.encode('ascii')
        payload = bytearray(len(at_bytes) + 2)
        payload[0] = 104
        payload[1] = 0
        payload[2:] = at_bytes
        try:
            return self._send(bytes(payload), timeout_ms, strict=False)
        except Exception:
            return b''
    def _send_diag_raw(self, diag_payload: bytes, timeout_ms: int) -> bytes:
        try:
            return self._send(diag_payload, timeout_ms, strict=False)
        except Exception:
            return b''
    def _send(self, payload: bytes, timeout_ms: int, strict: bool) -> bytes:
        frame = frame_build(self._sequence, payload)
        self._sequence += 1
        return self._write_and_read(frame, timeout_ms, strict)
    def _write_and_read(self, frame: bytes, timeout_ms: int, strict: bool) -> bytes:
        if not self._serial:
            return b''
        try:
            self._write_raw(frame)
        except Exception as e:
            if strict:
                raise
            return b''
        return self._read_until_timeout(timeout_ms, strict)
    def _write_raw(self, data: bytes):
        if self._serial:
            self._serial.write(data)
            self._serial.flush()
    def _read_until_timeout(self, timeout_ms: int, strict: bool=False) -> bytes:
        if not self._serial:
            return b''
        buffer = bytearray()
        deadline = time.perf_counter() + timeout_ms / 1000.0
        last_rx_time = 0.0
        while time.perf_counter() < deadline:
            try:
                waiting = self._serial.in_waiting
                if waiting == 0:
                    if buffer and last_rx_time > 0:
                        idle = time.perf_counter() - last_rx_time
                        if idle > 0.2:
                            break
                    time.sleep(0.025)
                    continue
            except Exception as e:
                if not strict:
                    break
                else:
                    raise
            try:
                chunk = self._serial.read(min(waiting, 65536))
                if chunk:
                    buffer.extend(chunk)
                    last_rx_time = time.perf_counter()
            except Exception as e:
                if not strict:
                    break
                else:
                    raise
        return bytes(buffer)
    def _patch_dcb(self):
        if sys.platform != 'win32' or not self._serial:
            return
        try:
            import ctypes
            from ctypes import wintypes
            handle = self._serial._port_handle
            if not handle:
                return
            class DCB(ctypes.Structure):
                _fields_ = [('DCBlength', wintypes.DWORD), ('BaudRate', wintypes.DWORD), ('fFlags', wintypes.DWORD), ('wReserved', wintypes.WORD), ('XonLim', wintypes.WORD), ('XoffLim', wintypes.WORD), ('ByteSize', wintypes.BYTE), ('Parity', wintypes.BYTE), ('StopBits', wintypes.BYTE), ('XonChar', ctypes.c_char), ('XoffChar', ctypes.c_char), ('ErrorChar', ctypes.c_char), ('EofChar', ctypes.c_char), ('EvtChar', ctypes.c_char), ('wReserved1', wintypes.WORD)]
            class COMMTIMEOUTS(ctypes.Structure):
                _fields_ = [('ReadIntervalTimeout', wintypes.DWORD), ('ReadTotalTimeoutMultiplier', wintypes.DWORD), ('ReadTotalTimeoutConstant', wintypes.DWORD), ('WriteTotalTimeoutMultiplier', wintypes.DWORD), ('WriteTotalTimeoutConstant', wintypes.DWORD)]
            kernel32 = ctypes.windll.kernel32
            dcb = DCB()
            dcb.DCBlength = ctypes.sizeof(DCB)
            if kernel32.GetCommState(handle, ctypes.byref(dcb)):
                dcb.BaudRate = DEFAULT_BAUD
                dcb.ByteSize = 8
                dcb.Parity = 0
                dcb.StopBits = 0
                dcb.fFlags = DCB_FLAGS
                kernel32.SetCommState(handle, ctypes.byref(dcb))
            timeouts = COMMTIMEOUTS()
            timeouts.ReadIntervalTimeout = TIMEOUT_READ_INTERVAL
            timeouts.ReadTotalTimeoutMultiplier = TIMEOUT_READ_MULTIPLIER
            timeouts.ReadTotalTimeoutConstant = TIMEOUT_READ_CONSTANT
            timeouts.WriteTotalTimeoutMultiplier = TIMEOUT_WRITE_MULTIPLIER
            timeouts.WriteTotalTimeoutConstant = TIMEOUT_WRITE_CONSTANT
            kernel32.SetCommTimeouts(handle, ctypes.byref(timeouts))
            kernel32.EscapeCommFunction(handle, 5)
            kernel32.EscapeCommFunction(handle, 3)
            kernel32.PurgeComm(handle, 15)
            return
        except Exception as e:
            logger.debug(f'DCB patch falhou (nao critico): {e}')
class DmitiEngine:
    def __init__(self):
        self._scanner = DmitiPortScanner()
        self._client = None
        self._cancelado = False
    @property
    def available(self) -> bool:
        return _HAS_SERIAL
    def cancel(self):
        self._cancelado = True
        if self._client:
            self._client.cancelar()
    def _reset(self):
        self._cancelado = False
    def boot_diag(self, log_cb: LogCallback=None) -> Tuple[bool, str, str]:
        self._reset()
        cb = log_cb or _noop
        cb('Aguardando conexao...')
        cb('  -> Conecte o aparelho DESLIGADO via USB')
        cb('  -> Ou segure VOL- e plugue o cabo')
        try:
            porta = self._scanner.wait_port(timeout_s=60.0, log_cb=cb)
        except TimeoutError:
            return (False, 'Dispositivo nao detectado', '')
        if self._cancelado:
            return (False, 'Cancelado', '')
        cb('Conectando...')
        client = DmitiClient()
        if not client.abrir(porta, log_cb=cb):
            return (False, 'Falha na conexao', '')
        client.boot_diag_switch(log_cb=cb)
        client.fechar(log_cb=cb)
        if self._cancelado:
            return (False, 'Cancelado', '')
        cb('Aguardando modo DIAG...')
        try:
            nova = self._scanner.wait_port(timeout_s=45.0, exclude=porta, log_cb=cb)
        except TimeoutError:
            return (False, 'Timeout aguardando modo DIAG', '')
        cb('Conectado!')
        return True, 'Conectado com sucesso!', nova
    def read_info(self, porta: str, log_cb: LogCallback=None) -> Dict[str, str]:
        self._reset()
        cb = log_cb or _noop
        info = {}
        client = DmitiClient()
        if not client.abrir(porta, log_cb=cb):
            cb('Falha na conexao')
            return info
        try:
            cb('Inicializando...')
            if not client.init(log_cb=cb):
                cb('Falha na comunicacao')
                client.fechar(log_cb=cb)
                return info
        finally:
            client.fechar(log_cb=cb)
        try:
            total_props = len(PROPS_READ_INFO)
            cb('Lendo informacoes do dispositivo...')
            for idx, (prop_name, label) in enumerate(PROPS_READ_INFO):
                if self._cancelado:
                    break
                if idx > 0 and idx % 4 == 0:
                    cb(f'  Processando... ({idx}/{total_props})')
                try:
                    valor = client.shell(f'getprop {prop_name}', timeout_ms=3000)
                    if valor:
                        if len(valor) > 1:
                            clean = valor.strip('\x00\r\n\t ~~')
                            if clean:
                                if clean not in ('~', '', 'unknown'):
                                    info[label] = clean
                    else:
                        continue
                except Exception:
                    continue
            if not self._cancelado:
                try:
                    df = client.shell('df /data 2>/dev/null | tail -1', timeout_ms=3000)
                    if df:
                        if 'G' in df or 'M' in df:
                            clean_df = df.strip('\x00\r\n\t ~~')
                            if clean_df:
                                info['Storage'] = clean_df
                except Exception:
                    pass
        finally:
            try:
                df = client.shell('df /data 2>/dev/null | tail -1', timeout_ms=3000)
                if df:
                    if 'G' in df or 'M' in df:
                        clean_df = df.strip('\x00\r\n\t ~~')
                        if clean_df:
                            info['Storage'] = clean_df
            except Exception:
                pass
            client.fechar(log_cb=cb)
        return info
    def factory_reset(self, porta: str, log_cb: LogCallback=None) -> Tuple[bool, str]:
        self._reset()
        cb = log_cb or _noop
        client = DmitiClient()
        if not client.abrir(porta, log_cb=cb):
            return (False, 'Falha na conexao')
        try:
            client._serial.reset_input_buffer()
            cb('Executando reset de fabrica...')
            reset_ok = False
            for tentativa in range(3):
                try:
                    cb('Inicializando...')
                    if not client.init(log_cb=cb):
                        try:
                            client.fechar(log_cb=cb)
                        except Exception:
                            pass
                        return (False, 'Falha na comunicacao')
                    if client._serial:
                        pass
                except Exception as e:
                    logger.debug(f'Erro tentativa {tentativa + 1}: {e}')
                    time.sleep(0.5)
                    try:
                        logger.debug(f'Factory reset tentativa {tentativa + 1}/3')
                        resp = client.send_factory_reset(log_cb=cb)
                        resp_text = resp.decode('ascii', errors='replace')
                        logger.debug(f'Resp ({len(resp)}B): {resp[:32].hex(' ')}')
                        if 'OK' in resp_text.upper() or b'\xd5' in resp:
                            reset_ok = True
                            cb('Processando reset...')
                            time.sleep(5.0)
                            break
                    except Exception:
                        pass
                    finally:
                        try:
                            client.fechar(log_cb=cb)
                        except Exception:
                            pass
                    continue
                try:
                    logger.debug('Sem confirmacao, retry...')
                    time.sleep(0.5)
                except Exception as e:
                    logger.debug(f'Erro tentativa {tentativa + 1}: {e}')
                    time.sleep(0.5)
                    continue
                finally:
                    try:
                        client.fechar(log_cb=cb)
                    except Exception:
                        pass
        finally:
            try:
                client._serial.reset_input_buffer()
                cb('Executando reset de fabrica...')
                reset_ok = False
                for tentativa in range(3):
                    try:
                        logger.debug(f'Factory reset tentativa {tentativa + 1}/3')
                        resp = client.send_factory_reset(log_cb=cb)
                        resp_text = resp.decode('ascii', errors='replace')
                        logger.debug(f'Resp ({len(resp)}B): {resp[:32].hex(' ')}')
                        if 'OK' in resp_text.upper() or b'\xd5' in resp:
                            reset_ok = True
                            cb('Processando reset...')
                            time.sleep(5.0)
                            break
                    except Exception as e:
                        logger.debug(f'Erro tentativa {tentativa + 1}: {e}')
                        time.sleep(0.5)
                        continue
                    try:
                        logger.debug('Sem confirmacao, retry...')
                        time.sleep(0.5)
                    except Exception as e:
                        logger.debug(f'Erro tentativa {tentativa + 1}: {e}')
                        time.sleep(0.5)
                        continue
                    finally:
                        try:
                            client.fechar(log_cb=cb)
                        except Exception:
                            pass
            except Exception:
                pass
            finally:
                try:
                    client.fechar(log_cb=cb)
                except Exception:
                    pass
        if not reset_ok:
            cb('Aviso: confirmacao nao recebida, tentando reboot...')
            logger.warning('Factory reset sem confirmacao apos 3 tentativas')
        else:
            cb('Reset de fabrica confirmado!')
        cb('Reiniciando dispositivo...')
        try:
            client.shell('sync; setprop sys.powerctl reboot 2>/dev/null; reboot 2>/dev/null', timeout_ms=5000)
        except Exception:
            pass
        try:
            client.fechar(log_cb=cb)
            return (True, 'Reset de fabrica concluido!')
        except Exception:
            return (True, 'Reset de fabrica concluido!')
    def factory_reset_completo(self, log_cb: LogCallback=None) -> Tuple[bool, str]:
        self._reset()
        cb = log_cb or _noop
        cb('Aguardando conexao...')
        cb('  -> Conecte o aparelho DESLIGADO via USB')
        cb('  -> Ou segure VOL- e plugue o cabo')
        try:
            porta_inicial = self._scanner.wait_port(timeout_s=90.0, log_cb=cb)
        except TimeoutError:
            return (False, 'Dispositivo nao detectado')
        if self._cancelado:
            return (False, 'Cancelado')
        cb('Iniciando modo DIAG...')
        client = DmitiClient()
        if not client.abrir(porta_inicial, log_cb=cb):
            return (False, 'Falha ao abrir porta')
        client.boot_diag_switch(log_cb=cb)
        client.fechar(log_cb=cb)
        if self._cancelado:
            return (False, 'Cancelado')
        cb('Aguardando modo DIAG...')
        try:
            porta_diag = self._scanner.wait_port(timeout_s=120.0, exclude=porta_inicial, log_cb=cb)
        except TimeoutError:
            return (False, 'Modo DIAG nao detectado')
        cb('Conectado!')
        client2 = DmitiClient()
        if not client2.abrir(porta_diag, log_cb=cb):
            return (False, 'Falha ao abrir porta DIAG')
        try:
            client2._serial.reset_input_buffer()
            cb('Executando reset de fabrica...')
            reset_ok = False
            for tentativa in range(3):
                try:
                    time.sleep(1.0)
                    if client2._serial:
                        try:
                            client2._serial.reset_input_buffer()
                        except Exception:
                            pass
                    cb('Inicializando...')
                    if not client2.init(log_cb=cb):
                        try:
                            client2.fechar(log_cb=cb)
                        except Exception:
                            pass
                        return (False, 'Falha na comunicacao')
                    if client2._serial:
                        pass
                except Exception as e:
                    logger.debug(f'Erro tentativa {tentativa + 1}: {e}')
                    time.sleep(0.5)
                    try:
                        logger.debug(f'Factory reset tentativa {tentativa + 1}/3')
                        resp = client2.send_factory_reset(log_cb=cb)
                        resp_text = resp.decode('ascii', errors='replace')
                        logger.debug(f'Resp ({len(resp)}B): {resp[:32].hex(' ')}')
                        if 'OK' in resp_text.upper() or b'\xd5' in resp:
                            reset_ok = True
                            cb('Processando reset...')
                            time.sleep(5.0)
                            break
                    except Exception:
                        pass
                    finally:
                        try:
                            client2.fechar(log_cb=cb)
                        except Exception:
                            pass
                    continue
                try:
                    logger.debug('Sem confirmacao, retry...')
                    time.sleep(0.5)
                except Exception as e:
                    logger.debug(f'Erro tentativa {tentativa + 1}: {e}')
                    time.sleep(0.5)
                    continue
                finally:
                    try:
                        client2.fechar(log_cb=cb)
                    except Exception:
                        pass
        finally:
            try:
                client2._serial.reset_input_buffer()
                cb('Executando reset de fabrica...')
                reset_ok = False
                for tentativa in range(3):
                    try:
                        logger.debug(f'Factory reset tentativa {tentativa + 1}/3')
                        resp = client2.send_factory_reset(log_cb=cb)
                        resp_text = resp.decode('ascii', errors='replace')
                        logger.debug(f'Resp ({len(resp)}B): {resp[:32].hex(' ')}')
                        if 'OK' in resp_text.upper() or b'\xd5' in resp:
                            reset_ok = True
                            cb('Processando reset...')
                            time.sleep(5.0)
                            break
                    except Exception as e:
                        logger.debug(f'Erro tentativa {tentativa + 1}: {e}')
                        time.sleep(0.5)
                        continue
                    try:
                        logger.debug('Sem confirmacao, retry...')
                        time.sleep(0.5)
                    except Exception as e:
                        logger.debug(f'Erro tentativa {tentativa + 1}: {e}')
                        time.sleep(0.5)
                        continue
                    finally:
                        try:
                            client2.fechar(log_cb=cb)
                        except Exception:
                            pass
            except Exception:
                pass
            finally:
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
        if not reset_ok:
            cb('Aviso: confirmacao nao recebida, tentando reboot...')
            logger.warning('Factory reset sem confirmacao apos 3 tentativas')
        else:
            cb('Reset de fabrica confirmado!')
        cb('Reiniciando dispositivo...')
        try:
            client2.shell('sync; setprop sys.powerctl reboot 2>/dev/null; reboot 2>/dev/null', timeout_ms=5000)
        except Exception:
            pass
        cb('Reset de fabrica concluido!')
        try:
            client2.fechar(log_cb=cb)
        except Exception:
            pass
        return (True, 'Reset de fabrica concluido!')
    def frp_remove_completo(self, log_cb: LogCallback=None) -> Tuple[bool, str]:
        self._reset()
        cb = log_cb or _noop
        cb('Aguardando conexao...')
        cb('  -> Conecte o aparelho DESLIGADO via USB')
        cb('  -> Ou segure VOL- e plugue o cabo')
        try:
            porta_inicial = self._scanner.wait_port(timeout_s=90.0, log_cb=cb)
        except TimeoutError:
            return (False, 'Dispositivo nao detectado')
        if self._cancelado:
            return (False, 'Cancelado')
        cb('Iniciando modo DIAG...')
        client = DmitiClient()
        if not client.abrir(porta_inicial, log_cb=cb):
            return (False, 'Falha ao abrir porta')
        client.boot_diag_switch(log_cb=cb)
        client.fechar(log_cb=cb)
        if self._cancelado:
            return (False, 'Cancelado')
        cb('Aguardando modo DIAG...')
        try:
            porta_diag = self._scanner.wait_port(timeout_s=120.0, exclude=porta_inicial, log_cb=cb)
        except TimeoutError:
            return (False, 'Modo DIAG nao detectado')
        cb('Conectado!')
        client2 = DmitiClient()
        if not client2.abrir(porta_diag, log_cb=cb):
            return (False, 'Falha ao abrir porta DIAG')
        try:
            time.sleep(1.0)
            if client2._serial:
                try:
                    client2._serial.reset_input_buffer()
                except Exception:
                    pass
            cb('Inicializando...')
            if not client2.init(log_cb=cb):
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
                return (False, 'Falha na comunicacao')
            if self._cancelado:
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
                return (False, 'Cancelado')
            cb('Lendo mapa do dispositivo...')
            partitions = self._parse_gpt(client2, cb)
            if not partitions:
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
                return (False, 'Falha ao ler mapa do dispositivo')
            target = None
            for p in partitions:
                if not p['name'].lower() == 'persist':
                    continue
                target = p
                break
            if not target:
                cb('Estrutura incompativel com este dispositivo.')
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
                return (False, 'Estrutura incompativel')
            start_lba = target['start_lba']
            size_sec = target['size_sectors']
            size_mb = target['size_mb']
            if size_mb > 10.0:
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
                return (False, 'Estrutura fora do esperado (abort)')
            if start_lba < 2048:
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
                return (False, 'Posicao invalida (abort)')
            cb(f'Estrutura validada ({size_mb:.1f} MB)')
            if self._cancelado:
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
                return (False, 'Cancelado')
            cb('Preparando escrita...')
        finally:
            try:
                client2.privilege_elevate(log_cb=cb)
            except Exception:
                pass
            finally:
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
        time.sleep(1.5)
        cb('Processando remocao...')
        try:
            if resp:
                logger.debug(f'FRP write resp: {sanitize_log(resp[:60])}')
            else:
                cb('Aguardando confirmacao...')
        except Exception as e:
            logger.debug(f'FRP write error: {e}')
            cb('Processamento enviado (sem confirmacao)')
            try:
                cmd = f'dd if=/dev/zero of=/dev/block/mmcblk0 bs=512 seek={start_lba} count={size_sec} 2>&1'
                resp = client2.shell(cmd, timeout_ms=30000)
                if 'records' in resp:
                    cb('Processamento confirmado!')
            except Exception as e:
                logger.debug(f'FRP write error: {e}')
                cb('Processamento enviado (sem confirmacao)')
            finally:
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
        time.sleep(1.0)
        cb('Verificando resultado...')
        try:
            logger.debug(f'FRP verify: {v_clean[:20]}')
            cb('Verificacao inconclusiva (continuando...)')
        except Exception as e:
            logger.debug(f'FRP verify error: {e}')
            cb('Verificacao ignorada (continuando...)')
            try:
                v_offset = start_lba * 512 + 1024
                cmd_v = f"dd if=/dev/block/mmcblk0 bs=1 skip={v_offset} count=64 2>/dev/null | od -An -tx1 -v | tr -d ' \\n'"
                v_resp = client2.shell(cmd_v, timeout_ms=5000)
                v_clean = ''.join((c for c in v_resp if c in '0123456789abcdef'))
                if v_clean:
                    if all((c == '0' for c in v_clean[:32])):
                        cb('Verificacao OK!')
            except Exception as e:
                logger.debug(f'FRP verify error: {e}')
                cb('Verificacao ignorada (continuando...)')
            finally:
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
        time.sleep(2.0)
        if self._cancelado:
            try:
                client2.fechar(log_cb=cb)
            except Exception:
                pass
            return (False, 'Cancelado')
        cb('Executando reset de fabrica...')
        reset_ok = False
        for tentativa in range(3):
            pass
        if reset_ok:
            cb('Reset confirmado!')
        else:
            cb('Reset enviado (aguardando...)')
        cb('Reiniciando dispositivo...')
        try:
            resp = client2.send_factory_reset(log_cb=cb)
            resp_text = resp.decode('ascii', errors='replace')
            if 'OK' in resp_text.upper() or b'\xd5' in resp:
                reset_ok = True
                cb('Processando reset...')
                time.sleep(5.0)
                # WARNING: break outside loop (unrecovered structure)
            # WARNING: continue outside loop (unrecovered structure)
        except Exception:
            try:
                client2.shell('sync; setprop sys.powerctl reboot 2>/dev/null; reboot 2>/dev/null', timeout_ms=5000)
            except Exception:
                time.sleep(0.5)
            finally:
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
        cb('Operacao concluida!')
        cb('Aguarde o dispositivo reiniciar (~2 minutos)')
        try:
            client2.fechar(log_cb=cb)
        except Exception:
            pass
        return (True, 'FRP removido com sucesso!')
    def _parse_gpt(self, client: 'DmitiClient', cb: Callable) -> List[dict]:
        partitions = []
        h_hex = self._read_emmc_block(client, 512)
        if not h_hex or len(h_hex) < 16:
            return []
        try:
            header = bytes.fromhex(h_hex)
        except ValueError:
            return []
        if header[:8] != b'EFI PART':
            return []
        num_entries = struct.unpack('<I', header[80:84])[0] if len(header) >= 84 else 128
        entry_size = struct.unpack('<I', header[84:88])[0] if len(header) >= 88 else 128
        empty_streak = 0
        for i in range(min(num_entries, 128)):
            if self._cancelado:
                return partitions
            offset = 1024 + i * entry_size
            e_hex = self._read_emmc_block(client, offset)
            if not e_hex:
                continue
            try:
                entry = bytes.fromhex(e_hex)
            except ValueError:
                continue
            if entry[:16] == b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00':
                empty_streak += 1
                if empty_streak >= 3:
                    return partitions
                continue
            empty_streak = 0
            if len(entry) < 56:
                continue
            start_lba = struct.unpack('<Q', entry[32:40])[0]
            end_lba = struct.unpack('<Q', entry[40:48])[0]
            if len(entry) >= 128:
                name_raw = entry[56:128]
            elif len(entry) > 56:
                name_raw = entry[56:]
            else:
                name_raw = b''
            try:
                name = name_raw.decode('utf-16-le').rstrip('\x00')
            except Exception:
                name = f'p{i}'
            size_sec = end_lba - start_lba + 1
            size_mb = size_sec * 512 / 1048576
            partitions.append({'name': name, 'start_lba': start_lba, 'end_lba': end_lba, 'size_sectors': size_sec, 'size_mb': size_mb})
            if len(partitions) % 20 != 0:
                continue
            cb(f'Lendo blocos... ({len(partitions)})')
            continue
        return partitions
    def _read_emmc_block(self, client: 'DmitiClient', offset: int, count: int=128) -> str:
        try:
            cmd = f"dd if=/dev/block/mmcblk0 bs=1 skip={offset} count={count} 2>/dev/null | od -An -tx1 -v | tr -d ' \\n'"
            resp = client.shell(cmd, timeout_ms=5000)
            clean = ''
            for c in resp:
                if c in '0123456789abcdef':
                    clean += c
                elif not clean:
                    continue
                return clean
            return clean
        except Exception:
            return ''
    def remove_pyj(self, porta: str, log_cb: LogCallback=None) -> Tuple[bool, str]:
        try:
            resp = client.send_factory_reset(log_cb=cb)
            resp_text = resp.decode('ascii', errors='replace')
            if 'OK' in resp_text.upper() or b'\xd5' in resp:
                cb('Processando reset...')
                time.sleep(5.0)
                # WARNING: break outside loop (unrecovered structure)
        except Exception:
            time.sleep(0.5)
        else:
            self._reset()
            cb = log_cb or _noop
            client = DmitiClient()
            if not client.abrir(porta, log_cb=cb):
                return (False, 'Falha na conexao')
            try:
                cb('Inicializando...')
                if not client.init(log_cb=cb):
                    try:
                        client.fechar(log_cb=cb)
                    except Exception:
                        pass
                    return (False, 'Falha na comunicacao')
                cb('Verificando protecao...')
                raw_resp = client.shell('dd if=/dev/block/by-name/miscdata bs=512 skip=1571 count=4 2>/dev/null | base64', timeout_ms=6000)
                if not raw_resp:
                    try:
                        client.fechar(log_cb=cb)
                    except Exception:
                        pass
                    return (False, 'Falha na leitura')
                clean = only_base64(raw_resp)
            finally:
                try:
                    client.fechar(log_cb=cb)
                except Exception:
                    pass
            try:
                data = base64.b64decode(clean)
                if len(data) != PYJ_READ_SIZE:
                    logger.debug(f'PYJ read size: {len(data)} != {PYJ_READ_SIZE}')
                    try:
                        client.fechar(log_cb=cb)
                    except Exception:
                        pass
                    return (False, 'Leitura incompleta')
                if data[:4] != PYJ_MARKER:
                    cb('Protecao nao encontrada neste dispositivo.')
                    try:
                        client.fechar(log_cb=cb)
                    except Exception:
                        pass
                    return (False, 'Protecao nao detectada')
                cb('Protecao detectada! Processando...')
                patch = build_patch()
                total = len(patch) // PYJ_WRITE_CHUNK
                for i in range(0, len(patch), PYJ_WRITE_CHUNK):
                    if self._cancelado:
                        try:
                            client.fechar(log_cb=cb)
                        except Exception:
                            pass
                        return (False, 'Cancelado')
                    chunk = patch[i:i + PYJ_WRITE_CHUNK]
                    chunk_b64 = base64.b64encode(chunk).decode('ascii')
                    offset = PYJ_READ_OFFSET + i
                    resp = client.shell(f"printf '{chunk_b64}' | base64 -d | dd of=/dev/block/by-name/miscdata bs=1 seek={offset} conv=notrunc 2>/dev/null; echo WROTE", timeout_ms=5000)
                    if not 'WROTE' not in resp.upper():
                        continue
                    try:
                        client.fechar(log_cb=cb)
                    except Exception:
                        pass
                    return (False, 'Falha na escrita')
            except Exception:
                try:
                    client.fechar(log_cb=cb)
                    return (False, 'Dados corrompidos')
                except Exception:
                    return (False, 'Dados corrompidos')
            finally:
                try:
                    client.fechar(log_cb=cb)
                except Exception:
                    pass
            try:
                client.shell('sync', timeout_ms=4000)
                cb('Correcao aplicada!')
                cb('Configurando dispositivo...')
                for cmd in ADB_ENABLE_COMMANDS:
                    if self._cancelado:
                        try:
                            client.fechar(log_cb=cb)
                        except Exception:
                            pass
                        return (False, 'Cancelado')
            finally:
                try:
                    client.fechar(log_cb=cb)
                except Exception:
                    return (False, 'Cancelado')
            time.sleep(1.5)
            if client._serial:
                try:
                    client._serial.reset_input_buffer()
                    client._serial.reset_output_buffer()
                except Exception:
                    pass
            cb('Executando reset de fabrica...')
            for tentativa in range(3):
                pass
            cb('Reiniciando dispositivo...')
        finally:
            try:
                client.shell('sync; setprop sys.powerctl reboot 2>/dev/null; reboot 2>/dev/null', timeout_ms=5000)
            except Exception:
                pass
            try:
                client.fechar(log_cb=cb)
            except Exception:
                return (True, 'Operacao concluida! Aguarde o dispositivo reiniciar.')
        return (True, 'Operacao concluida! Aguarde o dispositivo reiniciar.')
    def remove_pyj_completo(self, log_cb: LogCallback=None) -> Tuple[bool, str]:
        self._reset()
        cb = log_cb or _noop
        cb('Aguardando conexao...')
        cb('  -> Conecte o aparelho DESLIGADO via USB')
        cb('  -> Ou segure VOL- e plugue o cabo')
        try:
            porta_inicial = self._scanner.wait_port(timeout_s=90.0, log_cb=cb)
        except TimeoutError:
            return (False, 'Dispositivo nao detectado (timeout 90s)')
        if self._cancelado:
            return (False, 'Cancelado')
        cb('Iniciando modo DIAG...')
        client = DmitiClient()
        if not client.abrir(porta_inicial, log_cb=cb):
            return (False, 'Falha ao abrir porta')
        client.boot_diag_switch(log_cb=cb)
        client.fechar(log_cb=cb)
        if self._cancelado:
            return (False, 'Cancelado')
        cb('Aguardando modo DIAG...')
        try:
            porta_diag = self._scanner.wait_port(timeout_s=120.0, exclude=porta_inicial, log_cb=cb)
        except TimeoutError:
            return (False, 'Modo DIAG nao detectado (timeout 120s)')
        if self._cancelado:
            return (False, 'Cancelado')
        cb('Conectado ao modo DIAG!')
        client2 = DmitiClient()
        if not client2.abrir(porta_diag, log_cb=cb):
            return (False, 'Falha ao abrir porta DIAG')
        try:
            cb('Inicializando...')
            if not client2.init(log_cb=cb):
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
                return (False, 'Falha na comunicacao')
            if self._cancelado:
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
                return (False, 'Cancelado')
            cb('Verificando dispositivo...')
            raw_resp = client2.shell('dd if=/dev/block/by-name/miscdata bs=512 skip=1571 count=4 2>/dev/null | base64', timeout_ms=6000)
            if not raw_resp:
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
                return (False, 'Falha na leitura')
            clean = only_base64(raw_resp)
        finally:
            try:
                client2.fechar(log_cb=cb)
            except Exception:
                pass
        try:
            data = base64.b64decode(clean)
            if len(data) != PYJ_READ_SIZE:
                logger.debug(f'PYJ read size: {len(data)}')
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
                return (False, 'Leitura incompleta')
            if data[:4] != PYJ_MARKER:
                cb('Protecao nao encontrada neste dispositivo.')
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
                return (False, 'Protecao nao detectada')
            cb('Protecao detectada! Processando...')
            patch = build_patch()
            total_chunks = (len(patch) + PYJ_WRITE_CHUNK - 1) // PYJ_WRITE_CHUNK
            chunk_idx = 0
            for i in range(0, len(patch), PYJ_WRITE_CHUNK):
                if self._cancelado:
                    try:
                        client2.fechar(log_cb=cb)
                    except Exception:
                        pass
                    return (False, 'Cancelado')
                chunk = patch[i:i + PYJ_WRITE_CHUNK]
                chunk_b64 = base64.b64encode(chunk).decode('ascii')
                offset = PYJ_READ_OFFSET + i
                chunk_idx += 1
                resp = client2.shell(f"printf '{chunk_b64}' | base64 -d | dd of=/dev/block/by-name/miscdata bs=1 seek={offset} conv=notrunc 2>/dev/null; echo WROTE", timeout_ms=5000)
                if 'WROTE' not in resp.upper():
                    try:
                        client2.fechar(log_cb=cb)
                    except Exception:
                        pass
                    return (False, 'Falha na escrita')
                cb(f'Aplicando correcao... ({chunk_idx}/{total_chunks})')
            client2.shell('sync', timeout_ms=4000)
            cb('Correcao aplicada!')
            cb('Configurando dispositivo...')
            for cmd in ADB_ENABLE_COMMANDS:
                if self._cancelado:
                    try:
                        client2.fechar(log_cb=cb)
                    except Exception:
                        pass
                    return (False, 'Cancelado')
        except Exception:
            try:
                client2.fechar(log_cb=cb)
                return (False, 'Dados corrompidos')
            except Exception:
                return (False, 'Dados corrompidos')
        finally:
            try:
                client2.fechar(log_cb=cb)
            except Exception:
                return (False, 'Cancelado')
        time.sleep(1.5)
        if client2._serial:
            try:
                client2._serial.reset_input_buffer()
                client2._serial.reset_output_buffer()
            except Exception:
                pass
        cb('Executando reset de fabrica...')
        reset_ok = False
        for tentativa in range(3):
            pass
        if not reset_ok:
            cb('Aviso: reset pode nao ter sido confirmado')
            logger.warning('Factory reset: nenhuma confirmacao apos 3 tentativas')
        else:
            cb('Reset de fabrica confirmado!')
        cb('Reiniciando dispositivo...')
        try:
            logger.debug(f'PYJ factory reset tentativa {tentativa + 1}/3')
            resp_reset = client2.send_factory_reset(log_cb=cb)
            resp_text = resp_reset.decode('ascii', errors='replace')
            logger.debug(f'Resp ({len(resp_reset)}B): {resp_reset[:32].hex(' ')}')
            if 'OK' in resp_text.upper() or b'\xd5' in resp_reset:
                reset_ok = True
                cb('Processando reset...')
                time.sleep(5.0)
                # WARNING: break outside loop (unrecovered structure)
            logger.debug('Sem confirmacao, retry...')
            time.sleep(0.5)
            # WARNING: continue outside loop (unrecovered structure)
        except Exception:
            try:
                client2.shell('sync; setprop sys.powerctl reboot 2>/dev/null; reboot 2>/dev/null', timeout_ms=5000)
            except Exception as e:
                logger.debug(f'Erro tentativa {tentativa + 1}: {e}')
                time.sleep(0.5)
            finally:
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
        try:
            client2.fechar(log_cb=cb)
        except Exception:
            pass
        cb('Dispositivo reiniciando...')
        cb('Aguardando dispositivo iniciar (ate 3 minutos)...')
        t_start = time.time()
        while time.time() - t_start < 20.0:
            if self._cancelado:
                return (False, 'Cancelado')
            portas = self._scanner.scan_sprd_only()
            port_names = [p['port'] for p in portas]
            if porta_diag not in port_names:
                break
            time.sleep(0.5)
        try:
            from app.utils.adb_manager import ADBManager
            adb = ADBManager()
        except ImportError:
            logger.error('ADBManager nao disponivel')
            cb('Correcao aplicada! Instale protecao manualmente via ADB.')
            return (True, 'Patch aplicado (sem ADB disponivel)')
        try:
            adb.start_server()
        except Exception:
            pass
        adb_found = False
        adb_timeout = 180.0
        t_start = time.time()
        while time.time() - t_start < adb_timeout:
            if self._cancelado:
                return (False, 'Cancelado')
            elapsed = int(time.time() - t_start)
            if elapsed > 0 and elapsed % 15 == 0:
                cb(f'Aguardando ADB... {elapsed}s')
            try:
                if adb.is_device_connected():
                    adb_found = True
                    break
            except Exception:
                pass
            time.sleep(2.0)
        if not adb_found:
            cb('ADB nao detectado. Ative manualmente e use Anti Relock.')
            return (True, 'Patch aplicado (ADB timeout ÔÇö ative manualmente)')
        cb('Dispositivo conectado via ADB!')
        _PKG = 'com.techunion.deviceadmin'
        _RCV = f'{_PKG}/.MyAdminReceiver'
        _ACT_BLOCK = f'{_PKG}/.DisableFactoryReset'
        _ACT_DNS = f'{_PKG}/.newd'
        _DNS_KEY = '4641d586b3d0c165a1c5d52a4372545e'
        _DNS_HOST = 'a687f8.dns.nextdns.io'
        _APK_NAME = 'techunion_admin.apk'
        def _adb_cmd(args, timeout=15):
            try:
                return adb.execute_adb_command(args, timeout=timeout)
            except Exception:
                return
        apk_path = self._find_apk(_APK_NAME)
        if not apk_path:
            cb('Componente de protecao nao encontrado.')
            return (True, 'Patch aplicado (APK nao encontrado)')
        cb('Instalando protecao...')
        r = _adb_cmd(['install', '-r', apk_path], timeout=60)
        if r is not None:
            if 'success' not in (r or '').lower():
                logger.error(f'Install APK falhou: {(r or '')[:80]}')
                cb('Falha na instalacao. Use Anti Relock manualmente.')
                return (True, 'Patch aplicado (install falhou)')
        cb('Protecao instalada!')
        cb('Registrando protecao...')
        dp = _adb_cmd('shell dumpsys device_policy', timeout=10) or ''
        if _PKG in dp and 'Device Owner' in dp:
            cb('Protecao ja ativa!')
        else:
            r = _adb_cmd(f'shell dpm set-device-owner {_RCV}', timeout=15)
            if r is not None:
                if 'success' not in (r or '').lower():
                    logger.error(f'DPM falhou: {(r or '')[:80]}')
                    cb('Registro parcial. Use Anti Relock para completar.')
                    return (True, 'Patch aplicado (DPM falhou ÔÇö sem contas?)')
            cb('Protecao registrada!')
        cb('Configurando seguranca...')
        _adb_cmd(f'shell am start -n {_ACT_BLOCK}', timeout=10)
        time.sleep(1)
        _adb_cmd('shell settings put global private_dns_mode hostname')
        _adb_cmd(f'shell settings put global private_dns_specifier {_DNS_HOST}')
        _adb_cmd(f'shell am start -n {_ACT_DNS} --es key {_DNS_KEY}', timeout=10)
        _ota_pkgs = ['com.transsion.systemupdate', 'com.transsion.plat.appupdate', 'com.transsion.ota', 'com.transsion.fota', 'com.infinix.systemupdate', 'com.infinix.ota', 'com.infinix.fota', 'com.infinix.xos.update', 'com.tecno.systemupdate', 'com.tecno.ota', 'com.itel.systemupdate', 'com.itel.ota', 'com.android.updater']
        for pkg in _ota_pkgs:
            _adb_cmd(f'shell pm uninstall -k --user 0 {pkg}', timeout=5)
        _adb_cmd('shell am kill com.scorpio.securitycom', timeout=5)
        _adb_cmd('shell pm suspend com.scorpio.securitycom', timeout=5)
        _adb_cmd('shell pm uninstall -k --user 0 com.scorpio.securitycom', timeout=5)
        dp_final = _adb_cmd('shell dumpsys device_policy', timeout=10) or ''
        if 'Device Owner' in dp_final and _PKG in dp_final:
            cb('========================================')
            cb('OPERACAO CONCLUIDA COM SUCESSO!')
            cb('Protecao ativa. Device seguro.')
            cb('========================================')
            return (True, 'Operacao concluida com sucesso!')
        cb('Operacao finalizada. Verifique o dispositivo.')
        return (True, 'Operacao concluida (verificar manualmente)')
    @staticmethod
    def _find_apk(apk_name: str) -> Optional[str]:
        import os
        try:
            from app.utils.path_manager import PathManager
            found = PathManager.get_apk_path(apk_name)
            if found:
                return found
        except Exception:
            pass
        try:
            from app.utils.adb_manager import ADBManager
            mgr = ADBManager()
            if mgr.adb_path and os.path.isfile(mgr.adb_path):
                p = os.path.join(os.path.dirname(mgr.adb_path), apk_name)
                if os.path.isfile(p):
                    return p
        except Exception:
            pass
    def enable_adb(self, porta: str, log_cb: LogCallback=None) -> Tuple[bool, str]:
        self._reset()
        cb = log_cb or _noop
        client = DmitiClient()
        if not client.abrir(porta, log_cb=cb):
            return (False, 'Falha na conexao')
        try:
            cb('Inicializando...')
            if not client.init(log_cb=cb):
                try:
                    client.fechar(log_cb=cb)
                except Exception:
                    pass
                return (False, 'Falha na comunicacao')
            cb('Configurando ADB...')
            for cmd in ADB_ENABLE_COMMANDS:
                if self._cancelado:
                    try:
                        client.fechar(log_cb=cb)
                    except Exception:
                        pass
                    return (False, 'Cancelado')
        finally:
            try:
                client.fechar(log_cb=cb)
            except Exception:
                return (False, 'Cancelado')
        cb('ADB ativado! Reinicie o dispositivo para usar.')
        try:
            client.fechar(log_cb=cb)
            return (True, 'ADB ativado (reinicie o dispositivo)')
        except Exception:
            return (True, 'ADB ativado (reinicie o dispositivo)')
    def reboot(self, porta: str, log_cb: LogCallback=None) -> Tuple[bool, str]:
        self._reset()
        cb = log_cb or _noop
        client = DmitiClient()
        if not client.abrir(porta, log_cb=cb):
            return (False, 'Falha na conexao')
        try:
            cb('Inicializando...')
            if not client.init(log_cb=cb):
                pass
            try:
                client.fechar(log_cb=cb)
            except Exception:
                return (False, 'Falha na comunicacao')
            else:
                return (False, 'Falha na comunicacao')
        except Exception:
            try:
                try:
                    try:
                        client.fechar(log_cb=cb)
                    except Exception:
                        return (True, 'Dispositivo reiniciando...')
                finally:
                    pass
                return (True, 'Dispositivo reiniciando...')
            except Exception:
                pass
        try:
            client.shell('sync; setprop sys.powerctl reboot 2>/dev/null; reboot 2>/dev/null', timeout_ms=5000)
        except Exception:
            pass
        try:
            client.fechar(log_cb=cb)
            return (True, 'Dispositivo reiniciando...')
        except Exception:
            return (True, 'Dispositivo reiniciando...')
    def _boot_diag_auto(self, cb: Callable) -> Tuple[bool, str]:
        cb('Aguardando conexao...')
        cb('  -> Conecte o aparelho DESLIGADO via USB')
        try:
            porta_inicial = self._scanner.wait_port(timeout_s=90.0, log_cb=cb)
        except TimeoutError:
            return (False, '')
        if self._cancelado:
            return (False, '')
        cb('Iniciando modo DIAG...')
        client = DmitiClient()
        if not client.abrir(porta_inicial, log_cb=cb):
            return (False, '')
        client.boot_diag_switch(log_cb=cb)
        client.fechar(log_cb=cb)
        if self._cancelado:
            return (False, '')
        cb('Aguardando modo DIAG...')
        try:
            porta_diag = self._scanner.wait_port(timeout_s=120.0, exclude=porta_inicial, log_cb=cb)
        except TimeoutError:
            return (False, '')
        cb('Conectado!')
        return True, porta_diag
    def read_info_completo(self, log_cb: LogCallback=None) -> Dict[str, str]:
        self._reset()
        cb = log_cb or _noop
        ok, porta = self._boot_diag_auto(cb)
        if not ok:
            cb('Falha na conexao.')
            return {}
        return self.read_info(porta, log_cb=cb)
    def enable_adb_completo(self, log_cb: LogCallback=None) -> Tuple[bool, str]:
        self._reset()
        cb = log_cb or _noop
        ok, porta = self._boot_diag_auto(cb)
        if not ok:
            return (False, 'Falha na conexao')
        return self.enable_adb(porta, log_cb=cb)
    def reboot_completo(self, log_cb: LogCallback=None) -> Tuple[bool, str]:
        self._reset()
        cb = log_cb or _noop
        ok, porta = self._boot_diag_auto(cb)
        if not ok:
            return (False, 'Falha na conexao')
        return self.reboot(porta, log_cb=cb)
    def sec_plugin_completo(self, log_cb: LogCallback=None) -> Tuple[bool, str]:
        self._reset()
        cb = log_cb or _noop
        cb('Aguardando conexao...')
        cb('  -> Conecte o aparelho DESLIGADO via USB')
        cb('  -> Ou segure VOL- e plugue o cabo')
        try:
            porta_inicial = self._scanner.wait_port(timeout_s=90.0, log_cb=cb)
        except TimeoutError:
            return (False, 'Dispositivo nao detectado')
        if self._cancelado:
            return (False, 'Cancelado')
        cb('Iniciando modo DIAG...')
        client = DmitiClient()
        if not client.abrir(porta_inicial, log_cb=cb):
            return (False, 'Falha ao abrir porta')
        client.boot_diag_switch(log_cb=cb)
        client.fechar(log_cb=cb)
        if self._cancelado:
            return (False, 'Cancelado')
        cb('Aguardando modo DIAG...')
        try:
            porta_diag = self._scanner.wait_port(timeout_s=120.0, exclude=porta_inicial, log_cb=cb)
        except TimeoutError:
            return (False, 'Modo DIAG nao detectado')
        cb('Conectado!')
        client2 = DmitiClient()
        if not client2.abrir(porta_diag, log_cb=cb):
            return (False, 'Falha ao abrir porta DIAG')
        try:
            time.sleep(1.0)
            if client2._serial:
                try:
                    client2._serial.reset_input_buffer()
                except Exception:
                    pass
            cb('Inicializando...')
            if not client2.init(log_cb=cb):
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
                return (False, 'Falha na comunicacao')
            if self._cancelado:
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
                return (False, 'Cancelado')
            cb('Lendo mapa do dispositivo...')
            partitions = self._parse_gpt(client2, cb)
            if not partitions:
                pass
            try:
                client2.fechar(log_cb=cb)
            except Exception:
                return (False, 'Falha ao ler mapa do dispositivo')
            else:
                return (False, 'Falha ao ler mapa do dispositivo')
        except Exception as e:
            logger.error(f'sec_plugin_completo error: {e}', exc_info=True)
        try:
            detect_data = bytes.fromhex(detect_hex)
        except ValueError:
            try:
                client2.fechar(log_cb=cb)
                return (False, 'Dados de verificacao invalidos')
            except Exception:
                return (False, 'Dados de verificacao invalidos')
        has_data = any((b != 0 for b in detect_data))
        if not has_data:
            cb('Dados de tracking nao encontrados neste dispositivo.')
            try:
                client2.fechar(log_cb=cb)
            except Exception:
                pass
            return (False, 'Dados de tracking nao encontrados')
        try:
            if SEC_PLUGIN_DETECT_PATTERN in detect_data:
                cb('Dados de tracking detectados!')
            else:
                cb('Dados detectados, prosseguindo...')
            if self._cancelado:
                pass
            try:
                client2.fechar(log_cb=cb)
            except Exception:
                return (False, 'Cancelado')
            else:
                return (False, 'Cancelado')
        except Exception as e:
            logger.error(f'sec_plugin_completo error: {e}', exc_info=True)
        try:
            client2.privilege_elevate(log_cb=cb)
        except Exception:
            pass
        time.sleep(1.5)
        cb('Processando limpeza...')
        total_sec = len(SEC_PLUGIN_SECTORS)
        for idx, rel_sector in enumerate(SEC_PLUGIN_SECTORS):
            if self._cancelado:
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    pass
                return (False, 'Cancelado')
        try:
            client2.shell('sync', timeout_ms=5000)
        except Exception:
            try:
                abs_sector = start_lba + rel_sector
                cmd = f'dd if=/dev/zero of=/dev/block/mmcblk0 bs=512 seek={abs_sector} count=1 conv=notrunc 2>&1'
                ok_write = False
                for attempt in range(3):
                    try:
                        resp = client2.shell(cmd, timeout_ms=8000)
                        if resp is not None:
                            ok_write = True
                            break
                    except Exception:
                        pass
                    time.sleep(0.3)
                if not ok_write:
                    logger.error(f'SEC write fail sector rel={rel_sector}')
                try:
                    client2.fechar(log_cb=cb)
                except Exception:
                    return (False, 'Falha na escrita')
                else:
                    return (False, 'Falha na escrita')
            except Exception as e:
                logger.error(f'sec_plugin_completo error: {e}', exc_info=True)
        cb('Verificando resultado...')
        all_clean = True
        for rel_sector in SEC_PLUGIN_SECTORS:
            abs_sector = start_lba + rel_sector
            v_offset = abs_sector * 512
            v_hex = self._read_emmc_block(client2, v_offset, count=64)
            if v_hex:
                v_clean = ''.join((c for c in v_hex if c in '0123456789abcdef'))
                if not all((c == '0' for c in v_clean[:32])):
                    all_clean = False
                    logger.debug(f'SEC verify: sector {rel_sector} not clean')
            else:
                all_clean = False
        pyj_abs = start_lba + SEC_PYJ_SECTOR
        pyj_offset = pyj_abs * 512
        pyj_hex = self._read_emmc_block(client2, pyj_offset, count=16)
        if pyj_hex:
            try:
                pyj_bytes = bytes.fromhex(pyj_hex)
                if SEC_PYJ_MARKER in pyj_bytes:
                    cb('Integridade PYJ: OK')
                else:
                    cb('PYJ nao presente (normal se nao havia)')
            except ValueError:
                pass
        if not all_clean:
            cb('Operacao parcialmente concluida. Verifique o dispositivo.')
            try:
                client2.fechar(log_cb=cb)
            except Exception:
                pass
            return (False, 'Verificacao incompleta')
        try:
            cb('Limpeza concluida com sucesso!')
        except Exception as e:
            logger.error(f'sec_plugin_completo error: {e}', exc_info=True)
        try:
            client2.fechar(log_cb=cb)
        except Exception:
            pass
        return (True, 'Tracking removido com sucesso!')
# WARNING: Decompyle incomplete
