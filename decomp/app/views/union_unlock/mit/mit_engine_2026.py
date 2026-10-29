'''
Engine 2026 ÔÇö factory reset e remocao PYJ (conexao CDC/SLA direta).
Ref: administrativo/documentacao/29-07-2026-ANALISE-MTK-BOOT-META - V2/
'''
import hashlib
import logging
import os
import struct
import threading
import time
from typing import (Callable, Optional, Tuple)
from . import _mit_core as _core
from .mit_engine import MitEngine
logger = logging.getLogger(__name__)
LogCb = Callable[[str], None]
_PID_CDC = 8192
def _noop(msg):
    pass
_SLA_SECRET = bytearray([124, 52, 225, 137, 18, 225, 205, 61, 86, 49, 173, 178, 36, 118, 211, 18, 52, 226, 202, 253, 19, 18, 61, 43, 59, 19, 225, 87, 34, 173, 193, 29, 61, 52, 253, 61, 26, 87, 70, 26, 53, 19, 196, 175, 90, 134, 34, 69, 157, 61, 209, 70, 114, 65, 79, 173, 70, 173, 83, 17, 194, 59, 61, 45, 26, 47, 61, 250, 223, 53, 87, 36, 167, 77, 94, 79, 52, 211, 79, 45, 223, 31, 19, 211, 178, 145, 65, 61, 79, 209, 93, 145, 253, 46, 77, 111, 61, 65, 52, 127, 69, 243, 138, 38, 26, 51, 79, 62, 94, 100, 54, 138, 209, 246, 159, 53, 106, 150, 42, 93])
_SLA_SECRET_NOSHA = b'\xc4\x92\xad:a\xf9\xce\xc3\x13\x7f\xa9\xcb'
_SLA_SECRET_TECNO = b'L\xee\xcb\x1c\xb4\xb1\x1d+C\x18\x84?'
_META_CMD = b'METAMETA'
_META_PARAMS = bytes([4, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 192])
_SLA_START = b'SLASTART\x00'
_ATEM_PARAMS_1 = bytes([4, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 192])
_ATEM_PARAMS_2 = bytes([6, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 12, 0, 0, 0, 0])
_DISCONNECT = b'DISCONNECT\x00'
class MitEngine2026:
    '''Engine 2026 ÔÇö conexao CDC/SLA direta + factory reset / PYJ.'''
    def __init__(self):
        self._engine = MitEngine()
        self._cancelado = False
        self._device_id = ''
        self._save_dir = ''
    @property
    def available(self) -> bool:
        return self._engine.available
    def cancel(self):
        self._cancelado = True
        self._engine.cancel()
    def _safe_open_session(self, port: str, log: 'LogCb') -> bool:
        '''Abre sessao com protecao contra bloqueio indefinido (thread + timeout).'''
        result = [False]
        error = [None]
        def _run():
            try:
                self._engine._open_session(port, log_cb=log)
                result[0] = True
                return
            except Exception as e:
                error[0] = e
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=15.0)
        if t.is_alive():
            log('Conexao demorou demais. Tentando novamente...')
            self._safe_close()
            raise RuntimeError('Timeout na conexao')
        if error[0]:
            raise error[0]
        return result[0]
    def factory_reset_2026(self, port: str='', log_cb: LogCb=None) -> Tuple[bool, str]:
        '''Ref: administrativo/documentacao/29-07-2026-ANALISE-MTK-BOOT-META - V2/'''
        log = log_cb or _noop
        self._cancelado = False
        self._safe_close()
        try:
            porta = self._connect(port, log)
            if not porta:
                self._safe_close()
                return (False, 'Falha na conexao')
            if self._cancelado:
                self._safe_close()
                return (False, 'Operacao cancelada')
            log('Identificando dispositivo...')
            self._read_basic_info(log)
            if self._cancelado:
                self._safe_close()
                return (False, 'Operacao cancelada')
            self._unlock(log)
            log('Preparando reset...')
            self._write_bcb(log)
            log('Enviando comando de reset...')
            trigger = self._build_shell_trigger()
            try:
                pkt = self._engine._build_meta_packet(121, trigger)
                rx = self._engine._exchange(pkt, timeout=10.0)
                if rx:
                    logger.debug('shell_trigger: %dB resp', len(rx))
                    log('Comando aceito.')
            except Exception:
                pass
        except Exception as e:
            logger.debug('factory_reset_2026: %s', e)
            if 'Serial' in type(e).__name__ or 'OSError' in type(e).__name__:
                log('Dispositivo reiniciou.')
                try:
                    pass
                finally:
                    self._safe_close()
                return (True, 'Reset enviado com sucesso')
            try:
                pass
            finally:
                self._safe_close()
            return (False, 'Falha na operacao')
        log('Reiniciando dispositivo...')
        for mode in (b'\x02\x00\x00\x00', b'\x00\x00\x00\x00'):
            try:
                pkt = self._engine._build_meta_packet(10, mode)
                self._engine._exchange(pkt, timeout=5.0)
            except Exception as e:
                logger.debug('factory_reset_2026: %s', e)
                if 'Serial' in type(e).__name__ or 'OSError' in type(e).__name__:
                    log('Dispositivo reiniciou.')
                    try:
                        try:
                            pass
                        except Exception:
                            pass
                    finally:
                        self._safe_close()
                    return (True, 'Reset enviado com sucesso')
                try:
                    pass
                finally:
                    self._safe_close()
                return (False, 'Falha na operacao')
            time.sleep(0.3)
        log('Reset de fabrica enviado com sucesso.')
        self._safe_close()
        return (True, 'Reset enviado com sucesso')
    def remove_payjoy_2026(self, port: str='', log_cb: LogCb=None, save_dir: str='') -> Tuple[bool, str]:
        '''Remocao completa do bloqueio PayJoy via META mode.
        Ref: administrativo/documentacao/28-08-2026-PAYJOY-REMOVAL-NVRAM-WRITE-FIX/
        '''
        log = log_cb or _noop
        self._cancelado = False
        self._save_dir = save_dir
        self._device_id = ''
        self._safe_close()
        try:
            porta = self._connect(port, log)
            if not porta:
                self._safe_close()
                return (False, 'Falha na conexao')
            if self._cancelado:
                self._safe_close()
                return (False, 'Operacao cancelada')
            log('Identificando dispositivo...')
            props = self._read_device_props(log)
            if props.get('ro.build.display.id'):
                self._device_id = props['ro.build.display.id']
            log('Verificando indicador...')
            detected = self._detect_indicator(log)
            if not detected:
                log('Indicador nao encontrado neste dispositivo.')
                self._safe_close()
                return (False, 'Dispositivo sem indicador compativel')
            log('Indicador detectado.')
            if self._cancelado:
                self._safe_close()
                return (False, 'Operacao cancelada')
            log('Preparando ambiente...')
            self._init_shell(log)
            if self._cancelado:
                self._safe_close()
                return (False, 'Operacao cancelada')
            log('Carregando permissoes...')
            apdb_ok = self._download_apdb(log)
            if not apdb_ok:
                logger.debug('download permissoes falhou, continuando')
            if self._cancelado:
                self._safe_close()
                return (False, 'Operacao cancelada')
            log('Removendo bloqueio...')
            unlock_ok = self._unlock(log)
            if unlock_ok:
                log('Bloqueio removido com sucesso.')
            else:
                log('Continuando...')
            log('Lendo dados do dispositivo...')
            proinfo = self._file_recv_read('dev/block/by-name/proinfo', timeout=120.0)
            if not proinfo:
                log('Leitura negada (continuando).')
            else:
                log('Leitura concluida (%d bytes).' % len(proinfo))
                save_path = self._save_proinfo_backup(proinfo)
                if save_path:
                    log('Backup salvo: %s' % os.path.basename(save_path))
            if self._cancelado:
                self._safe_close()
                return (False, 'Operacao cancelada')
            log('Preparando reset...')
            self._write_bcb(log)
            log('Reiniciando dispositivo...')
            trigger = self._build_shell_trigger()
            try:
                pkt = self._engine._build_meta_packet(121, trigger)
                self._engine._exchange(pkt, timeout=10.0)
            except Exception as e:
                logger.debug('remove_payjoy_2026: %s', e)
                if 'Serial' in type(e).__name__ or 'OSError' in type(e).__name__:
                    try:
                        try:
                            pass
                        except Exception:
                            pass
                    finally:
                        self._safe_close()
                    return (True, 'Operacao enviada (dispositivo reiniciou)')
                try:
                    pass
                finally:
                    self._safe_close()
                return (False, 'Falha na operacao')
            else:
                log('Operacao concluida com sucesso.')
                safe_name = self._device_id or 'backup'
                size = len(proinfo) if proinfo else 0
        except Exception as e:
            logger.debug('remove_payjoy_2026: %s', e)
            if 'Serial' in type(e).__name__ or 'OSError' in type(e).__name__:
                try:
                    pass
                finally:
                    self._safe_close()
                return (True, 'Operacao enviada (dispositivo reiniciou)')
            try:
                pass
            finally:
                self._safe_close()
            return (False, 'Falha na operacao')
        self._safe_close()
        return True, '%s (%d bytes)' % (safe_name, size)
    def _connect(self, port: str, log: LogCb) -> str:
        '''Conecta via CDC/SLA ÔåÆ META. Fallback para boot_meta.'''
        try:
            import serial
            import serial.tools.list_ports
        except ImportError:
            log('Componente necessario nao disponivel.')
            return ''
        if port:
            log('Conectando...')
            try:
                self._safe_open_session(port, log)
                return
            except Exception:
                logger.debug('open_session falhou port=%s', port)
                log('Tentando conexao...')
        meta_port = self._connect_via_cdc(log, serial)
        if meta_port:
            return meta_port
        if self._cancelado:
            return ''
        log('Tentando metodo alternativo...')
        ok, msg, porta = self._engine.boot_meta(log_cb=log)
        if not ok:
            log('Falha na conexao.')
            return ''
        time.sleep(1.0)
        try:
            self._safe_open_session(porta, log)
        except Exception:
            log('Falha: dispositivo nao respondeu.')
            return ''
        return porta
    def _connect_via_cdc(self, log: LogCb, serial_mod) -> str:
        '''Conexao CDC/SLA ÔåÆ espera META ÔåÆ abre sessao.
        Ref: administrativo/documentacao/29-07-2026-ANALISE-MTK-BOOT-META - V2/
        '''
        cdc_port = self._find_cdc_port(serial_mod)
        if not cdc_port:
            log('Aguardando dispositivo...')
            cdc_port = self._wait_cdc_port(serial_mod, timeout=15.0)
        if not cdc_port:
            meta_port = self._find_meta_port(serial_mod)
            if meta_port:
                log('Dispositivo detectado.')
                try:
                    self._safe_open_session(meta_port, log)
                except Exception:
                    return ''
                return meta_port
            return ''
        log('Dispositivo detectado.')
        ok = self._cdc_handshake(cdc_port, log, serial_mod)
        if not ok:
            return ''
        log('Aguardando dispositivo...')
        time.sleep(1.5)
        meta_port = self._wait_meta_port(serial_mod, timeout=20.0)
        if not meta_port:
            log('Falha: dispositivo nao respondeu.')
            return ''
        log('Conectando...')
        time.sleep(2.0)
        try:
            self._safe_open_session(meta_port, log)
        except Exception as e:
            logger.debug('open_session pos-CDC falhou: %s', e)
            log('Falha na conexao.')
            return ''
        return meta_port
    def _cdc_handshake(self, port: str, log: LogCb, serial_mod) -> bool:
        '''Handshake CDC com SLA.
        Ref: administrativo/documentacao/29-07-2026-ANALISE-MTK-BOOT-META - V2/
        '''
        path = '\\\\.\\%s' % port if os.name == 'nt' else port
        try:
            ser = serial_mod.Serial(port=path, baudrate=921600, timeout=0.5, write_timeout=0.5, bytesize=serial_mod.EIGHTBITS, parity=serial_mod.PARITY_NONE, stopbits=serial_mod.STOPBITS_ONE, dsrdtr=False, rtscts=False)
        except Exception as e:
            logger.debug('CDC open falhou: %s', e)
            log('Falha ao acessar dispositivo.')
            return False
        try:
            log('Iniciando comunicacao...')
            if not self._wait_keyword(ser, b'READY', timeout=3.0):
                log('Dispositivo nao respondeu.')
                try:
                    ser.close()
                except Exception:
                    pass
                return False
            ser.write(_META_CMD + _META_PARAMS)
            ser.flush()
            resp = self._read_past_ready(ser)
            if not resp:
                log('Sem resposta do dispositivo.')
                try:
                    ser.close()
                except Exception:
                    pass
                return False
            if b'METASLA' in resp:
                log('Autenticando...')
                try:
                    ser.close()
                except Exception:
                    return
                return self._do_sla(ser, log)
            if b'ATEMATEM' in resp:
                ser.write(_META_PARAMS + _META_PARAMS)
                params_ext = bytes([6, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 192, 0, 128, 0, 0])
                ser.write(params_ext)
                ser.flush()
                self._fast_read(ser, 0.3)
                ser.write(_DISCONNECT)
                ser.flush()
                log('Autenticacao concluida.')
                try:
                    ser.close()
                except Exception:
                    pass
                return True
            if b'ATEMEVDX' in resp or b'TOOBTSAF' in resp:
                ser.write(_DISCONNECT)
                ser.flush()
                log('Autenticacao concluida.')
                try:
                    ser.close()
                except Exception:
                    pass
                return True
            log('Dispositivo nao compativel.')
        finally:
            try:
                ser.close()
            except Exception:
                return False
        return False
    def _do_sla(self, ser, log: LogCb) -> bool:
        '''Autenticacao SLA.
        Ref: administrativo/documentacao/29-07-2026-ANALISE-MTK-BOOT-META - V2/
        '''
        ser.write(_SLA_START)
        ser.flush()
        challenge = self._fast_read(ser, timeout=1.0)
        if not challenge or b'RANDOM' not in challenge:
            log('Falha na autenticacao.')
            return False
        random_idx = challenge.find(b'RANDOM')
        challenge_data = challenge[random_idx:]
        keyid = 0
        if len(challenge_data) > 16:
            keyid = int.from_bytes(challenge_data[13:17], 'little')
        logger.debug('SLA challenge: keyid=%d', keyid)
        auth_response = self._compute_sla(challenge_data)
        ser.write(auth_response)
        ser.flush()
        resp = self._fast_read(ser, timeout=1.5)
        if not resp or b'ATEM0001' not in resp:
            log('Falha na autenticacao.')
            return False
        ser.write(_ATEM_PARAMS_1)
        ser.flush()
        resp = self._fast_read(ser, timeout=1.5)
        if not resp or b'ATEM0002' not in resp:
            log('Falha na autenticacao.')
            return False
        ser.write(_ATEM_PARAMS_2)
        ser.flush()
        resp = self._fast_read(ser, timeout=1.5)
        if not resp or b'ATEMATEX' not in resp:
            log('Falha na autenticacao.')
            return False
        ser.write(_DISCONNECT)
        ser.flush()
        log('Autenticacao concluida.')
        return True
    @staticmethod
    def _compute_sla(challenge_data: bytes) -> bytes:
        '''Ref: administrativo/documentacao/29-07-2026-ANALISE-MTK-BOOT-META - V2/'''
        is_tecno = b'EXT' in challenge_data
        has_sha = b'SHA' in challenge_data
        timeval = challenge_data[6:10]
        if has_sha:
            keyid = int.from_bytes(challenge_data[13:17], 'little')
            key_offset = 12 * keyid
            key = bytes(_SLA_SECRET[key_offset:key_offset + 12])
            logger.debug('SLA: key[%d] = %s', keyid, key.hex())
            return hashlib.sha256(timeval + key).digest()
        if is_tecno:
            return hashlib.md5(timeval + _SLA_SECRET_TECNO).digest()
        return hashlib.md5(timeval + _SLA_SECRET_NOSHA).digest()
    @staticmethod
    def _find_cdc_port(serial_mod) -> Optional[str]:
        for p in serial_mod.tools.list_ports.comports():
            if p.vid != _core.VID:
                continue
            if not p.pid == _PID_CDC:
                continue
            return p.device
    @staticmethod
    def _find_meta_port(serial_mod) -> Optional[str]:
        pids = _core.PIDS_META + (8199,)
        for p in serial_mod.tools.list_ports.comports():
            if p.vid != _core.VID:
                continue
            if not p.pid in pids:
                continue
            return p.device
    def _wait_cdc_port(self, serial_mod, timeout: float=15.0) -> Optional[str]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._cancelado:
                return
            port = self._find_cdc_port(serial_mod)
            if port:
                return port
            time.sleep(0.3)
    def _wait_meta_port(self, serial_mod, timeout: float=20.0) -> Optional[str]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._cancelado:
                return
            port = self._find_meta_port(serial_mod)
            if port:
                return port
            time.sleep(0.3)
    @staticmethod
    def _wait_keyword(ser, keyword: bytes, timeout: float=3.0) -> bool:
        buf = bytearray()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            waiting = ser.in_waiting
            if waiting > 0:
                buf.extend(ser.read(waiting))
                if keyword in buf:
                    return True
            else:
                time.sleep(0.005)
        return keyword in buf
    @staticmethod
    def _fast_read(ser, timeout: float=1.0) -> bytes:
        buf = bytearray()
        deadline = time.monotonic() + timeout
        last_data = time.monotonic()
        while time.monotonic() < deadline:
            waiting = ser.in_waiting
            if waiting > 0:
                buf.extend(ser.read(waiting))
                last_data = time.monotonic()
            elif buf and time.monotonic() - last_data > 0.02:
                break
            time.sleep(0.003)
        return bytes(buf)
    @staticmethod
    def _read_past_ready(ser, timeout: float=3.0) -> bytes:
        '''Le ate receber algo que nao seja READY.'''
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            chunk = MitEngine2026._fast_read(ser, timeout=0.5)
            if not chunk:
                break
            while b'READY' in chunk:
                idx = chunk.find(b'READY')
                after = chunk[idx + 5:]
                if after:
                    chunk = after
                else:
                    chunk = MitEngine2026._fast_read(ser, timeout=0.5)
                    if not chunk:
                        return b''
            if chunk and chunk != b'READY':
                return chunk
        return b''
    def _unlock(self, log: LogCb) -> bool:
        '''Zera REGIONFLAG (LID 54) para remover bloqueio.
        Ref: administrativo/documentacao/28-08-2026-PAYJOY-REMOVAL-NVRAM-WRITE-FIX/
        '''
        payload_16 = bytes([54, 0, 1, 0])
        try:
            pkt = self._engine._build_meta_packet(22, payload_16)
            rx = self._engine._exchange(pkt, timeout=3.0)
        except Exception as e:
            logger.debug('_unlock 0x16 exception: %s', e)
            rx = b''
        if not rx or len(rx) < 6:
            return False
        time.sleep(2.0)
        payload_18 = bytes([54, 0, 1, 0]) + b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        try:
            pkt = self._engine._build_meta_packet(24, payload_18, data_payload_size=2056)
            rx = self._engine._exchange(pkt, timeout=10.0)
        except Exception as e:
            logger.debug('_unlock 0x18 exception: %s', e)
            rx = b''
        if not rx:
            time.sleep(3.0)
            try:
                pkt = self._engine._build_meta_packet(24, payload_18, data_payload_size=2056)
                rx = self._engine._exchange(pkt, timeout=10.0)
            except Exception as e:
                logger.debug('_unlock 0x18 retry exception: %s', e)
                rx = b''
        if rx and len(rx) > 16:
            resp_data = rx[12:-1] if len(rx) > 12 else b''
            if len(resp_data) >= 5 and resp_data[4] == 1:
                return True
        return False
    @staticmethod
    def _build_shell_trigger() -> bytes:
        '''Payload 0x79 ÔÇö reboot/factory reset.
        Ref: administrativo/documentacao/28-08-2026-PAYJOY-REMOVAL-NVRAM-WRITE-FIX/
        '''
        payload = bytearray(1040)
        struct.pack_into('<I', payload, 0, 0)
        struct.pack_into('<I', payload, 4, 1)
        payload[9] = 4
        payload[10] = 1
        payload[14] = 1
        return bytes(payload)
    def _write_bcb(self, log: LogCb):
        '''Escreve BCB em misc+para para factory reset.
        Ref: administrativo/documentacao/28-08-2026-PAYJOY-REMOVAL-NVRAM-WRITE-FIX/
        '''
        bcb_content = bytearray(256)
        bcb_content[0:14] = b'boot-recovery\x00'
        bcb_content[64:85] = b'recovery\n--wipe_data\n'
        for target in ('dev/block/by-name/misc', 'dev/block/by-name/para'):
            path_padded = target.encode('ascii')[:255].ljust(256, b'\x00')
            pad = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            try:
                payload_list = struct.pack('<I', 0) + path_padded + pad
                pkt = self._engine._build_meta_packet(163, payload_list)
                self._engine._exchange(pkt, timeout=3.0)
                time.sleep(0.1)
                payload_info = struct.pack('<I', 1) + path_padded + pad
                pkt = self._engine._build_meta_packet(163, payload_info)
                self._engine._exchange(pkt, timeout=3.0)
                time.sleep(0.1)
            except Exception as e:
                logger.debug("BCB list/info exception '%s': %s", target, e)
            payload = struct.pack('<I', 2)
            payload += path_padded
            payload += pad
            payload += struct.pack('<I', 256)
            payload += struct.pack('<I', 5)
            payload += bytes(bcb_content)
            try:
                pkt = self._engine._build_meta_packet(163, payload, data_payload_size=264)
                rx = self._engine._exchange(pkt, timeout=10.0)
                if rx:
                    if len(rx) > 20:
                        resp_data = rx[12:-1] if len(rx) > 13 else b''
                        if len(resp_data) >= 12:
                            flags = struct.unpack_from('<I', resp_data, 8)[0]
                            logger.debug("BCB '%s' flags=%d", target, flags)
                            continue
            except Exception as e:
                logger.debug("BCB WRITE '%s' exception: %s", target, e)
    def _file_recv_read(self, path: str, timeout: float=60.0) -> bytes:
        '''Le particao via FILE_RECV (0xA3 op=3).
        Ref: administrativo/documentacao/29-07-2026-ANALISE-MTK-BOOT-META - V2/
        '''
        clean_path = path.lstrip('/')
        path_padded = clean_path.encode('ascii')[:255].ljust(256, b'\x00')
        payload = struct.pack('<I', 3) + path_padded + b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        pkt = self._engine._build_meta_packet(163, payload)
        ser = self._engine._ser
        if not ser:
            return b''
        try:
            ser.reset_input_buffer()
        except Exception:
            pass
        ser.write(pkt)
        ser.flush()
        buf = bytearray()
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            if self._cancelado:
                break
            waiting = ser.in_waiting
            if waiting > 0:
                buf.extend(ser.read(waiting))
            elif buf:
                time.sleep(0.01)
                if ser.in_waiting == 0:
                    time.sleep(0.05)
                    if ser.in_waiting == 0:
                        break
            else:
                time.sleep(0.02)
        if not buf:
            return b''
        result = bytearray()
        offset = 0
        while offset < len(buf):
            if buf[offset] == 85 and offset + 12 < len(buf):
                frame_len = struct.unpack_from('>H', buf, offset + 1)[0]
                expected = 4 + frame_len + 1
                if offset + expected <= len(buf):
                    frame = buf[offset:offset + expected]
                    if len(frame) >= 20 and frame[3] == 96:
                        sub_cmd = struct.unpack_from('<H', frame, 10)[0]
                        if sub_cmd == 164:
                            resp_data = frame[12:-1]
                            if len(resp_data) >= 12:
                                flags = struct.unpack_from('<I', resp_data, 8)[0]
                                if flags == 0:
                                    return b''
                                block_data = resp_data[12:]
                                result.extend(block_data)
                                if flags == 6:
                                    break
                    offset += expected
                else:
                    break
            next_frame = buf.find(b'U', offset + 1)
            if next_frame > 0:
                raw_chunk = buf[offset:next_frame]
                if len(raw_chunk) > 1:
                    result.extend(raw_chunk[1:])
                offset = next_frame
            else:
                raw_chunk = buf[offset:]
                if len(raw_chunk) > 1:
                    result.extend(raw_chunk[1:])
                break
        return bytes(result)
    def _detect_indicator(self, log: LogCb) -> bool:
        '''Verifica indicador via protocolo META 0x89 (nao depende de shell).'''
        for idx, prop in enumerate(('ro.build.display.id', 'ro.product.name'), start=10):
            try:
                pkt = self._engine._build_read_prop(idx, prop)
                rx = self._engine._exchange(pkt, timeout=2.0)
                val = self._engine._parse_prop_value(rx)
                if val:
                    if _core.PYJ_INDICATOR in val or '-PJ-' in val:
                        return True
            except Exception:
                continue
        return False
    _APDB_CANDIDATES = ['APDB_{chip}_S01__W2609', 'APDB_{chip}_S01__W2552', 'APDB_{chip}_S01__W2448', 'APDB_{chip}_S01__W2420']
    def _download_apdb(self, log: LogCb) -> bool:
        '''Carrega base de permissoes do device (requerido para escrita).
        Ref: administrativo/documentacao/28-08-2026-PAYJOY-REMOVAL-NVRAM-WRITE-FIX/
        '''
        chip = self._get_chip_name()
        if not chip:
            chip = 'MT6768'
        chip_upper = chip.upper()
        apdb_base = self._get_apdb_path()
        self._file_recv_list(apdb_base)
        self._file_recv_info('')
        for tpl in self._APDB_CANDIDATES:
            candidate = f'{apdb_base!s}/{tpl.format(chip=chip_upper)!s}'
            data = self._file_recv_read(candidate, timeout=10.0)
            size = len(data) if data else 0
            if not data:
                continue
            if not size > 1000:
                continue
            log('Permissoes carregadas.')
            return True
        return False
    def _get_chip_name(self) -> str:
        '''Retorna nome do chip via GET_INFO (0x85).'''
        try:
            pkt = self._engine._build_meta_packet(133)
            rx = self._engine._exchange(pkt, timeout=3.0)
            if rx and len(rx) > 14:
                data = rx[12:-1] if len(rx) > 13 else rx[12:]
                return data.split(b'\x00')[0].decode('ascii', errors='replace')
        except Exception:
            pass
        return ''
    def _get_apdb_path(self) -> str:
        '''Obtem path base via 0xAD.'''
        try:
            payload = b'\x00\x00\x00\x00\x00\x00\x00\x00'
            pkt = self._engine._build_meta_packet(173, payload)
            rx = self._engine._exchange(pkt, timeout=2.0)
            if rx and len(rx) > 16:
                data = rx[12:-1] if len(rx) > 13 else rx[12:]
                if len(data) >= 8:
                    path = data[4:].split(b'\x00')[0].decode('ascii', errors='replace')
                    if path:
                        return path
        except Exception:
            pass
        return 'odm/etc/apdb'
    def _file_recv_list(self, path: str) -> bytes:
        '''FILE_RECV LIST (op=0).'''
        clean = path.lstrip('/')
        path_padded = clean.encode('ascii')[:255].ljust(256, b'\x00')
        payload = struct.pack('<I', 0) + path_padded + b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        try:
            pkt = self._engine._build_meta_packet(163, payload)
            return self._engine._exchange(pkt, timeout=3.0)
        except Exception:
            return b''
    def _file_recv_info(self, path: str) -> bytes:
        '''FILE_RECV INFO (op=1).'''
        clean = path.lstrip('/') if path else ''
        path_padded = clean.encode('ascii')[:255].ljust(256, b'\x00')
        payload = struct.pack('<I', 1) + path_padded + b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        try:
            pkt = self._engine._build_meta_packet(163, payload)
            return self._engine._exchange(pkt, timeout=3.0)
        except Exception:
            return b''
    _DEVICE_PROPS = [('ro.product.system.brand', 'brand'), ('ro.product.system.model', 'model'), ('ro.product.device', 'device'), ('ro.product.system.manufacturer', 'manufacturer'), ('ro.system.build.version.release', 'version.release'), ('ro.build.version.security_patch', 'security_patch'), ('ro.build.display.id', 'display.id'), ('ro.system.build.date', 'build.date'), ('ro.system.build.version.incremental', 'incremental'), ('ro.system.build.id', 'build.id'), ('ro.boot.slot_suffix', 'slot_suffix')]
    def _read_device_props(self, log: LogCb) -> dict:
        '''Le propriedades do device e exibe ao tecnico.
        Ref: administrativo/documentacao/28-08-2026-PAYJOY-REMOVAL-NVRAM-WRITE-FIX/
        '''
        props = {}
        for idx, (prop_name, label) in enumerate(self._DEVICE_PROPS, start=20):
            try:
                pkt = self._engine._build_read_prop(idx, prop_name)
                rx = self._engine._exchange(pkt, timeout=2.0)
                val = self._engine._parse_prop_value(rx)
                if val:
                    if val != 'unknown':
                        props[prop_name] = val
                        log(f'  {label!s}: {val!s}')
            except Exception:
                continue
        if not props:
            log('  Dispositivo identificado.')
        return props
    def _save_proinfo_backup(self, proinfo: bytes) -> Optional[str]:
        '''Salva proinfo no diretorio escolhido pelo tecnico.'''
        try:
            save_dir = getattr(self, '_save_dir', '') or os.path.join(os.path.expanduser('~'), 'Documents')
            if not os.path.isdir(save_dir):
                os.makedirs(save_dir, exist_ok=True)
            device_id = getattr(self, '_device_id', '') or 'proinfo_backup'
            safe_name = device_id.replace('/', '_').replace('\\', '_')
            filepath = os.path.join(save_dir, '%s.bin' % safe_name)
            with open(filepath, 'wb') as f:
                f.write(proinfo)
        except Exception:
            return
        return filepath
    def _read_basic_info(self, log: LogCb):
        '''Le info via protocolo META (0x89) ÔÇö formato identico ao read_info principal.'''
        props_to_read = ['ro.product.brand', 'ro.build.version.release', 'ro.build.display.id', 'ro.boot.hardware']
        found_any = False
        for idx, prop_name in enumerate(props_to_read, start=2):
            try:
                pkt = self._engine._build_read_prop(idx, prop_name)
                rx = self._engine._exchange(pkt, timeout=2.0)
                val = self._engine._parse_prop_value(rx)
                if val:
                    if val != 'unknown':
                        short = prop_name.split('.')[-1]
                        log(f'{short!s}: {val!s}')
                        found_any = True
                        if prop_name == 'ro.build.display.id':
                            self._device_id = val
                else:
                    continue
            except Exception:
                continue
        if not found_any:
            log('Dispositivo identificado.')
    def _init_shell(self, log: LogCb):
        '''Inicializa subsistema shell no device (requerido antes de comandos shell).
        Ref: administrativo/documentacao/29-07-2026-ANALISE-MTK-BOOT-META - V2/
        '''
        self._shell("printf 'S0F:'; whoami; printf ':E0F'", timeout=5.0)
        if self._cancelado:
            return
        time.sleep(17)
        log('Ambiente preparado.')
    def _shell(self, cmd: str, timeout: float=10.0) -> Optional[str]:
        try:
            return self._engine._exec_shell(cmd, timeout=timeout)
        except Exception:
            return
    def _safe_close(self):
        try:
            self._engine._close_serial()
            return
        except Exception:
            return
