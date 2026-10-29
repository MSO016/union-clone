import logging
from typing import Callable, Optional
from .protocol import SPDProtocol
logger = logging.getLogger(__name__)
PARTITION_CHUNK_SIZE = 1016
class SPDOperations:
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
    def erase_partition(self, name: str, size_str: str='1M') -> bool:
        self._log(f'Apagando parti├º├úo: {name} ({size_str})')
        result = self.protocol.send_erase_partition(name, size_str)
        if result:
            self._log(f'Particao {name} apagada')
            return result
        self._log(f'Falha ao apagar {name}', 'error')
        return result
    def flash_partition(self, name: str, data: bytes, on_progress=None) -> bool:
        self._log(f'Gravando parti├º├úo: {name} ({len(data)} bytes)')
        if not self.protocol.send_write_partition_start(name, len(data)):
            self._log(f'Falha no start de {name}', 'error')
            return False
        if not self.protocol.send_file_chunks(data, chunk_size=PARTITION_CHUNK_SIZE, on_progress=on_progress or (lambda s, t: self._progress(s, t, f'flash:{name}'))):
            self._log(f'Falha no envio de dados para {name}', 'error')
            return False
        if not self.protocol.send_end_data():
            self._log(f'Falha no end de {name}', 'error')
            return False
        self._log(f'Particao {name} gravada')
        return True
    def recovery_command(self, misc_data: bytes) -> bool:
        self._log('Executando recovery command...')
        if not self.erase_partition('misc', '1M'):
            return False
        if not self.flash_partition('misc', misc_data):
            return False
        self._log('Recovery command OK')
        return True
    def erase_frp(self) -> bool:
        self._log('=== ERASE FRP ===')
        return self.erase_partition('persist', '2M')
    def erase_data_and_frp(self) -> bool:
        self._log('=== ERASE DATA + FRP ===')
        if not self.erase_partition('misc', '1M'):
            return False
        if not self.erase_partition('userdata', '1M'):
            self._log('Falha ao apagar userdata ÔÇö tentando recovery', 'warning')
        return self.erase_frp()
    def recovery_wipe_and_frp(self, misc_data: bytes) -> bool:
        self._log('=== RECOVERY + FRP ===')
        if not self.recovery_command(misc_data):
            return False
        return self.erase_frp()
    def erase_frp_only(self) -> bool:
        self._log('=== ERASE FRP ONLY ===')
        return self.erase_frp()
    def write_persist_clean(self, persist_data: bytes) -> bool:
        self._log('=== WRITE PERSIST CLEAN ===')
        return self.flash_partition('persist', persist_data)
    def full_frp_remove(self, persist_data: bytes=None) -> bool:
        self._log('=== FULL FRP REMOVE ===')
        if persist_data:
            if not self.write_persist_clean(persist_data):
                return False
        elif not self.erase_frp():
            return False
        if not self.erase_partition('userdata', '1M'):
            self._log('Aviso: falha no erase userdata', 'warning')
        self.protocol.send_reset()
        self._log('=== FRP REMOVIDO ÔÇö Dispositivo reiniciando ===')
        return True
    def execute_operation(self, operation: str, misc_data: bytes=None, persist_data: bytes=None) -> bool:
        self._log(f'Opera├º├úo: {operation}')
        self.protocol.checksum.set_type('add')
        self.protocol.send_enable_flash()
        if operation in ('RECOVERY WIPE DATA I + FRP', 'RECOVERY WIPE DATA II + FRP', 'RECOVERY FORMAT DATA + FRP', 'RECOVERY WIPE APP DATA + FRP', 'RECOVERY WIPE DATA ONLY + FRP'):
            if misc_data is None:
                self._log('Dados misc obrigat├│rios para recovery', 'error')
                return False
            success = self.recovery_wipe_and_frp(misc_data)
        elif operation == 'ERASE DATA + FRP':
            success = self.erase_data_and_frp()
        elif operation == 'ERASE FRP ONLY':
            success = self.erase_frp_only()
        elif operation == 'FULL FRP REMOVE':
            success = self.full_frp_remove(persist_data)
        else:
            self._log(f'Opera├º├úo desconhecida: {operation}', 'error')
            return False
        if success:
            self.protocol.send_reset()
            self._log('Dispositivo reiniciando...')
        return success
