'''
FDLLoader ÔÇö orquestracao do envio de FDL1 e FDL2.
Ver: alan/documentacao/16-08-2026-ARQUITETURA-SPD-INTERNA/01_MAPA_REFERENCIAS_INTERNAS.md
'''
import logging
import time
from typing import Callable, Optional
from .protocol import SPDProtocol
logger = logging.getLogger(__name__)
class FDLLoader:
    '''
Carrega FDL1 e FDL2 no dispositivo SPD.
     Vari├íveis: fdl1/fdl2 (bytes), fdl1_len/fdl2_len, fdl1_addr/fdl2_addr.
     M├®todo ConnectDownload() orquestra todo o fluxo.
     Mesmo fluxo em Python via pyusb.
'''
    def __init__(self, protocol: SPDProtocol):
        self.protocol = protocol
        self.on_progress = None
        self.on_log = None
    def _log(self, msg: str, level: str='info'):
        '''Log interno + callback externo.'''
        getattr(logger, level, logger.info)(msg)
        if self.on_log:
            self.on_log(msg, level)
    def _progress(self, sent: int, total: int, label: str=''):
        '''Reporta progresso via callback.'''
        if self.on_progress:
            self.on_progress(sent, total, label)
    def load_fdl1(self, fdl1_data: bytes, fdl1_addr: int) -> bool:
        '''
Carrega FDL1 (SRAM loader) no dispositivo.
     1. set_chksum_type("crc16")
     2. send_checkbaud() ÔåÆ send_connect()
     3. send_start_fdl(fdl1_addr, fdl1_len)
     4. loop send_midst(chunk) com MIDST_SIZE=528
     5. send_end() ÔåÆ send_exec()
     6. send_connect() ÔÇö reconecta com FDL1
     Mesmo fluxo: ping ÔåÆ connect ÔåÆ start ÔåÆ midst├ùN ÔåÆ end ÔåÆ exec
     Ap├│s exec: set_chksum_type("add") ÔåÆ retry ping ├ù 10
Args:
    fdl1_data: bytes do arquivo fdl1-sign.bin
    fdl1_addr: endere├ºo SRAM (ex: 0x65000800 para UMS9620)
Returns:
    True se FDL1 foi carregado e executado com sucesso
'''
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
        '''
Carrega FDL2 (U-Boot/downloader) no dispositivo.
     1. send_connect() ÔÇö confirma FDL1 rodando
     2. set_chksum_type("add") ÔåÉ troca cr├¡tica!
     3. send_start_fdl(fdl2_addr, fdl2_len)
     4. loop send_midst(chunk)
     5. send_end() ÔåÆ send_exec()
     6. Resposta 0x96 (INCOMPATIBLE_PARTITION) ÔÇö normal
     7. send_enable_flash()
     connect ÔåÆ start ÔåÆ midst├ùN ÔåÆ end ÔåÆ exec
     Resposta 0x96 = "U-Boot is up and running!"
Args:
    fdl2_data: bytes do arquivo lk-fdl2-sign.bin
    fdl2_addr: endere├ºo RAM (ex: 0xB4FFFE00 para UMS9620)
Returns:
    True se FDL2 foi carregado, executado e flash habilitada
'''
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
        '''
Fluxo completo: carrega FDL1 + FDL2 e prepara o dispositivo.
     Fluxo inteiro num ├║nico m├®todo ass├¡ncrono.
Este ├® o m├®todo principal chamado pelo worker/GUI.
Args:
    fdl1_data: bytes do fdl1-sign.bin
    fdl1_addr: endere├ºo SRAM para FDL1
    fdl2_data: bytes do lk-fdl2-sign.bin
    fdl2_addr: endere├ºo RAM para FDL2
Returns:
    True se ambos FDLs foram carregados e dispositivo est├í pronto
'''
        self._log('Iniciando download de FDLs...')
        if not self.load_fdl1(fdl1_data, fdl1_addr):
            return False
        if not self.load_fdl2(fdl2_data, fdl2_addr):
            return False
        self._log('=== FDLs carregados ÔÇö dispositivo pronto ===')
        return True
