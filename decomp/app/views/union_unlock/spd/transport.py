'''
Camada de transporte serial (pyserial).
Ver: alan/documentacao/16-08-2026-ARQUITETURA-SPD-INTERNA/01_MAPA_REFERENCIAS_INTERNAS.md
'''
import logging
import struct
import time
import serial
from .constants import (HDLC_HEADER, SERIAL_BAUDRATE, SERIAL_BYTESIZE, SERIAL_PARITY, SERIAL_STOPBITS, SERIAL_TIMEOUT, SERIAL_WRITE_TIMEOUT)
logger = logging.getLogger(__name__)
class SerialTransport:
    '''
Comunica├º├úo serial com dispositivo SPD via pyserial.
     Wraps SerialPort com ConnectAsync, ReadAsync, WriteAsync, Dispose.
     maxtimeout = 500ms para WaitDataReceived.
Simplifica├º├úo: pyserial j├í tem timeout nativo ÔÇö n├úo precisamos de
event handlers, poll loops ou WhenAny. O fluxo ├® s├¡ncrono:
write(data) ÔåÆ read(response).
'''
    def __init__(self):
        self._port = None
        self._connected = False
        self._transcode = True
        self._raw_mode_failed = False
    @property
    def is_connected(self) -> bool:
        '''Verifica se a porta est├í aberta e conectada.'''
        return self._connected and self._port is not None and self._port.is_open
    @property
    def port_name(self) -> str:
        '''Retorna o nome da porta COM ou string vazia.'''
        if self._port is not None:
            return self._port.port or ''
        return ''
    @property
    def transcode(self) -> bool:
        '''True = HDLC mode com escaping, False = raw mode.'''
        return self._transcode
    @property
    def raw_mode_failed(self) -> bool:
        '''True se o device respondeu HDLC quando esper├ívamos raw.'''
        return self._raw_mode_failed
    def set_transcode(self, enabled: bool) -> None:
        '''
        Alterna entre modo HDLC (transcode) e modo raw.
        Ap├│s DISABLE_TRANSCODE, pacotes s├úo enviados/recebidos sem
        0x7E wrapping e sem byte stuffing (escaping).
        '''
        self._transcode = enabled
        mode = 'HDLC (transcode)' if enabled else 'raw (sem transcode)'
        logger.info(f'Transport mode: {mode}')
    def connect(self, port: str, baudrate: int=None) -> bool:
        '''
Abre conex├úo serial com o dispositivo SPD.
     Abre a porta, configura DataReceived handler, seta timeouts.
     m_port.Open() ÔåÆ m_port.BaseStream.WriteTimeout = ...
Args:
    port: nome da porta COM (ex: "COM3", "/dev/ttyUSB0")
    baudrate: baud rate (default: 115200 de constants.py)
Returns:
    True se a porta foi aberta com sucesso, False se falhou.
'''
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
        '''
Fecha a conex├úo serial e limpa buffers.
     DiscardInBuffer() ÔåÆ DiscardOutBuffer() ÔåÆ Close() ÔåÆ Dispose()
     Tudo dentro de lock(m_disposeLock) com try/catch.
'''
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
        '''
Envia dados pela porta serial.
     Escreve via m_port.BaseStream.WriteAsync(buffer, offset, length).
     Usa Task.WhenAny com timeout. Se timeout ÔåÆ cancela e lan├ºa exce├º├úo.
     Ap├│s escrever, chama WaitDataReceived() para esperar resposta.
Em pyserial: serial.write() ├® s├¡ncrono com write_timeout configurado.
Args:
    data: bytes para enviar
Returns:
    N├║mero de bytes escritos
'''
        if not self.is_connected:
            raise ConnectionError('Porta serial n├úo conectada')
        logger.debug(f'TX [{len(data)}B]: {data[:32].hex(' ')}')
        written = self._port.write(data)
        self._port.flush()
        return written
    def read(self, size: int=1024, timeout: float=None) -> bytes:
        '''
L├¬ dados da porta serial.
     Cria buffer[len], l├¬ via BaseStream.ReadAsync com timeout.
     Se timeout ÔåÆ cancela e lan├ºa TimeoutException.
     Poll loop 1ms at├® isReceived ou maxtimeout(500ms).
Em pyserial: serial.read(size) bloqueia at├® size bytes ou timeout.
Usamos read(1) + in_waiting para ler frame HDLC completo.
Args:
    size: m├íximo de bytes para ler
    timeout: timeout em segundos (None = usa padr├úo da porta)
Returns:
    Bytes lidos (pode ser vazio se timeout)
'''
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
        '''
L├¬ um frame HDLC completo (0x7E ... 0x7E).
Diferente de read() gen├®rico, este m├®todo garante que l├¬
exatamente um frame completo delimitado por flags HDLC.
Fluxo:
  1. L├¬ bytes at├® encontrar o primeiro 0x7E (in├¡cio do frame)
  2. Continua lendo at├® encontrar o pr├│ximo 0x7E (fim do frame)
  3. Retorna o frame completo incluindo os dois flags
Args:
    timeout: timeout em segundos para cada leitura
Returns:
    Frame HDLC completo (bytes), ou b"" se timeout
'''
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
        '''
        Limpa buffer de entrada serial. Retorna quantidade de bytes descartados.
        Essencial ap├│s troca de modo HDLCÔåÆraw para evitar dados residuais.
        '''
        if not self.is_connected:
            return 0
        discarded = self._port.in_waiting
        if discarded > 0:
            self._port.read(discarded)
            logger.debug(f'Flush: {discarded} bytes descartados do buffer RX')
        self._port.reset_input_buffer()
        return discarded
    def read_raw_frame(self, timeout: float=None) -> bytes:
        '''
L├¬ um frame BSL em modo raw (sem HDLC framing).
     1. L├¬ 4 bytes de header: command(2B BE) + length(2B BE)
     2. L├¬ length + 2 bytes: data + checksum
     Sem 0x7E delimiters.
DETEC├ç├âO DE FALLBACK HDLC:
Se o primeiro byte for 0x7E, o device N├âO implementou raw mode
apesar de ter ACK'd DISABLE_TRANSCODE. Nesse caso, l├¬ como HDLC
e sinaliza via self._raw_mode_failed = True.
Returns:
    Frame raw completo (header + data + checksum), ou b"" se timeout
'''
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
        '''
Envia dados e aguarda resposta HDLC.
     Chama WriteAsync que internamente faz write + WaitDataReceived.
     O response ├® processado pelo DataReceived handler.
Este m├®todo combina write + read_hdlc_frame num ciclo at├┤mico,
que ├® o padr├úo real do protocolo SPD: comando ÔåÆ resposta.
Args:
    data: frame HDLC para enviar
    timeout: timeout para leitura da resposta
Returns:
    Frame HDLC da resposta, ou b"" se timeout
'''
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
