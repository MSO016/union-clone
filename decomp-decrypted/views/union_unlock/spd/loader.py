import logging
import time
from typing import Callable, Optional
from .protocol import SPDProtocol
logger = logging.getLogger(__name__)
class FDLLoader:
    def __init__(self, protocol: SPDProtocol):
        self.protocol = protocol
        self.on_progress = None
        self.on_log = None
    def _log(self, msg: str, level: str='info'):
        getattr(logger, level, logger.info)(msg)
        if self.on_log:
            self.on_log(msg, level)
    def _progress(self, sent: int, total: int, label: str=''):
        if self.on_progress:
            self.on_progress(sent, total, label)
    def load_fdl1(self, fdl1_data: bytes, fdl1_addr: int) -> bool:
        self._log('=== Carregando FDL1 ===')
        self.protocol.checksum.set_type('crc16')
        self._log('Enviando check baud...')
        if not self.protocol.send_checkbaud():
            self._log('Falha no check baud', 'error')
            return False
        self._log('Enviando connect...')
        if not self.protocol.send_connect():
            self._log('Falha na conex├úo', 'error')
            return False
        self._log(f'FDL1: addr=0x{fdl1_addr:08X} size={len(fdl1_data)} bytes')
        if not self.protocol.send_start_data(fdl1_addr, len(fdl1_data)):
            self._log('Falha no start_data FDL1', 'error')
            return False
        self._log('Enviando FDL1...')
        if not self.protocol.send_file_chunks(fdl1_data, on_progress=(lambda s, t: self._progress(s, t, 'FDL1'))):
            self._log('Falha no envio de chunks FDL1', 'error')
            return False
        if not self.protocol.send_end_data():
            self._log('Falha no end_data FDL1', 'error')
            return False
        if not self.protocol.send_exec_data():
            self._log('Falha no exec_data FDL1', 'error')
            return False
        self._log('FDL1 executado com sucesso')
        self._log('Reconectando com FDL1...')
        if not self.protocol.send_connect():
            self._log('Falha na reconex├úo com FDL1', 'error')
            return False
        self._log('FDL1 OK')
        return True
    def load_fdl2(self, fdl2_data: bytes, fdl2_addr: int) -> bool:
        self._log('=== Carregando FDL2 ===')
        self.protocol.send_connect()
        self.protocol.checksum.set_type('add')
        self._log('Checksum alterado para ADD')
        self._log(f'FDL2: addr=0x{fdl2_addr:08X} size={len(fdl2_data)} bytes')
        if not self.protocol.send_start_data(fdl2_addr, len(fdl2_data)):
            self._log('Falha no start_data FDL2', 'error')
            return False
        self._log('Enviando FDL2...')
        if not self.protocol.send_file_chunks(fdl2_data, on_progress=(lambda s, t: self._progress(s, t, 'FDL2'))):
            self._log('Falha no envio de chunks FDL2', 'error')
            return False
        if not self.protocol.send_end_data():
            self._log('Falha no end_data FDL2', 'error')
            return False
        if not self.protocol.send_exec_data():
            self._log('Falha no exec_data FDL2', 'error')
            return False
        self._log('FDL2 executado com sucesso')
        if not self.protocol.send_enable_flash():
            self._log('Falha no enable_flash', 'error')
            return False
        self._log('Flash habilitada ÔÇö pronto para opera├º├Áes')
        self._log('FDL2 OK')
        return True
    def connect_and_load(self, fdl1_data: bytes, fdl1_addr: int, fdl2_data: bytes, fdl2_addr: int) -> bool:
        self._log('Iniciando download de FDLs...')
        if not self.load_fdl1(fdl1_data, fdl1_addr):
            return False
        if not self.load_fdl2(fdl2_data, fdl2_addr):
            return False
        self._log('=== FDLs carregados ÔÇö dispositivo pronto ===')
        return True
