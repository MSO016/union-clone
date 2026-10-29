import logging
import struct
import time
import serial
from .constants import (HDLC_HEADER, SERIAL_BAUDRATE, SERIAL_BYTESIZE, SERIAL_PARITY, SERIAL_STOPBITS, SERIAL_TIMEOUT, SERIAL_WRITE_TIMEOUT)
logger = logging.getLogger(__name__)
class SerialTransport:
    def __init__(self):
        self._port = None
        self._connected = False
        self._transcode = True
        self._raw_mode_failed = False
    @property
    def is_connected(self) -> bool:
        return self._connected and self._port is not None and self._port.is_open
    @property
    def port_name(self) -> str:
        if self._port is not None:
            return self._port.port or ''
        return ''
    @property
    def transcode(self) -> bool:
        return self._transcode
    @property
    def raw_mode_failed(self) -> bool:
        return self._raw_mode_failed
    def set_transcode(self, enabled: bool) -> None:
        self._transcode = enabled
        mode = 'HDLC (transcode)' if enabled else 'raw (sem transcode)'
        logger.info(f'Transport mode: {mode}')
    def connect(self, port: str, baudrate: int=None) -> bool:
        if self.is_connected:
            self.disconnect()
        baudrate = baudrate or SERIAL_BAUDRATE
        try:
            self._port = serial.Serial(port=port, baudrate=baudrate, bytesize=SERIAL_BYTESIZE, parity=SERIAL_PARITY, stopbits=SERIAL_STOPBITS, timeout=SERIAL_TIMEOUT, write_timeout=SERIAL_WRITE_TIMEOUT)
            self._connected = True
            logger.info(f'Porta serial aberta: {port} @ {baudrate} baud')
            return True
        except serial.SerialException as e:
            logger.error(f'Falha ao abrir porta {port}: {e}')
            self._port = None
            self._connected = False
            return False
        except Exception as e:
            logger.error(f'Erro inesperado ao abrir {port}: {e}')
            self._port = None
            self._connected = False
            return False
    def disconnect(self) -> None:
        if self._port is not None:
            try:
                if self._port.is_open:
                    self._port.reset_input_buffer()
                    self._port.reset_output_buffer()
            except Exception:
                pass
            try:
                self._port.close()
            except Exception:
                pass
            self._port = None
        self._connected = False
        logger.info('Desconectado')
    def write(self, data: bytes) -> int:
        if not self.is_connected:
            raise ConnectionError('Porta serial n├úo conectada')
        logger.debug(f'TX [{len(data)}B]: {data[:32].hex(' ')}')
        written = self._port.write(data)
        self._port.flush()
        return written
    def read(self, size: int=1024, timeout: float=None) -> bytes:
        if not self.is_connected:
            raise ConnectionError('Porta serial n├úo conectada')
        old_timeout = None
        if timeout is not None:
            old_timeout = self._port.timeout
            self._port.timeout = timeout
        try:
            response = self._port.read(size)
            remaining = self._port.in_waiting
            if remaining > 0:
                response += self._port.read(remaining)
        finally:
            if old_timeout is not None:
                self._port.timeout = old_timeout
        if response:
            logger.debug(f'RX [{len(response)}B]: {response[:32].hex(' ')}')
            return response
        logger.debug('RX: timeout (sem dados)')
        return response
    def read_hdlc_frame(self, timeout: float=None) -> bytes:
        if not self.is_connected:
            raise ConnectionError('Porta serial n├úo conectada')
        old_timeout = None
        if timeout is not None:
            old_timeout = self._port.timeout
            self._port.timeout = timeout
        try:
            frame = bytearray()
            while True:
                byte = self._port.read(1)
                if not byte:
                    if old_timeout is not None:
                        self._port.timeout = old_timeout
                        return b''
                    return b''
                if byte[0] == HDLC_HEADER:
                    frame.append(HDLC_HEADER)
                    break
        finally:
            if old_timeout is not None:
                self._port.timeout = old_timeout
        while True:
            byte = self._port.read(1)
            if not byte:
                logger.warning('Timeout aguardando fim do frame HDLC')
                if old_timeout is not None:
                    self._port.timeout = old_timeout
                    return b''
                return b''
        if old_timeout is not None:
            self._port.timeout = old_timeout
        logger.debug(f'RX HDLC [{len(frame)}B]: {frame[:32].hex(' ')}')
        return bytes(frame)
    def flush_input(self) -> int:
        if not self.is_connected:
            return 0
        discarded = self._port.in_waiting
        if discarded > 0:
            self._port.read(discarded)
            logger.debug(f'Flush: {discarded} bytes descartados do buffer RX')
        self._port.reset_input_buffer()
        return discarded
    def read_raw_frame(self, timeout: float=None) -> bytes:
        if not self.is_connected:
            raise ConnectionError('Porta serial n├úo conectada')
        old_timeout = None
        if timeout is not None:
            old_timeout = self._port.timeout
            self._port.timeout = timeout
        try:
            first_byte = self._port.read(1)
            if not first_byte:
                logger.debug('RX raw: timeout no header')
                if old_timeout is not None:
                    self._port.timeout = old_timeout
                    return b''
                return b''
        finally:
            if old_timeout is not None:
                self._port.timeout = old_timeout
        try:
            if first_byte[0] == HDLC_HEADER:
                logger.warning('RX raw: detectado 0x7E ÔÇö device ainda em HDLC! Fazendo fallback para leitura HDLC.')
                self._raw_mode_failed = True
                frame = bytearray([HDLC_HEADER])
                while True:
                    byte = self._port.read(1)
                    if not byte:
                        logger.warning('Timeout no fallback HDLC read')
                        if old_timeout is not None:
                            self._port.timeout = old_timeout
                            return b''
                        return b''
                    frame.append(byte[0])
                    if byte[0] == HDLC_HEADER:
                        break
                logger.debug(f'RX HDLC-fallback [{len(frame)}B]: {frame[:32].hex(' ')}')
                if old_timeout is not None:
                    self._port.timeout = old_timeout
                    return bytes(frame)
                return
        finally:
            if old_timeout is not None:
                self._port.timeout = old_timeout
        try:
            remaining_header = self._port.read(3)
            if len(remaining_header) < 3:
                logger.debug('RX raw: timeout no header (parcial)')
                if old_timeout is not None:
                    self._port.timeout = old_timeout
                    return b''
                return b''
        finally:
            if old_timeout is not None:
                self._port.timeout = old_timeout
        try:
            header = bytes([first_byte[0]]) + remaining_header
            length = struct.unpack('>H', header[2:4])[0]
            remaining = length + 2
            rest = self._port.read(remaining)
            if len(rest) < remaining:
                logger.warning(f'RX raw: dados incompletos ({len(rest)}/{remaining})')
            frame = header + rest
            logger.debug(f'RX raw [{len(frame)}B]: {frame[:32].hex(' ')}')
        finally:
            if old_timeout is not None:
                self._port.timeout = old_timeout
        return bytes(frame)
    def send_and_receive(self, data: bytes, timeout: float=None) -> bytes:
        self.write(data)
        return self.read_hdlc_frame(timeout=timeout)
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
    def __repr__(self) -> str:
        if self.is_connected:
            return f'SerialTransport({self.port_name}, connected)'
        return 'SerialTransport(disconnected)'
# WARNING: Decompyle incomplete
