'''
Operacoes alto-nivel (erase, flash, recovery, read).
Ver: alan/documentacao/16-08-2026-ARQUITETURA-SPD-INTERNA/01_MAPA_REFERENCIAS_INTERNAS.md
'''
import logging
from typing import Callable, Optional
from .protocol import SPDProtocol
logger = logging.getLogger(__name__)
PARTITION_CHUNK_SIZE = 1016
class SPDOperations:
    '''
Opera├º├Áes alto n├¡vel sobre parti├º├Áes do dispositivo SPD.
     Assume que FDL1+FDL2 j├í foram carregados (via FDLLoader)
     e que send_enable_flash() j├í foi chamado.
Pr├®-requisitos:
  1. FDLLoader.connect_and_load() retornou True
  2. protocol.checksum est├í em modo "add"
  3. protocol.send_enable_flash() retornou True
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
    def erase_partition(self, name: str, size_str: str='1M') -> bool:
        '''
Apaga uma parti├º├úo pelo nome.
     Chama uni.send_select_partition(partition, size, false, CMD_ERASE_FLASH)
Args:
    name: nome da parti├º├úo (ex: "persist", "misc", "userdata")
    size_str: tamanho como string (ex: "1M", "2M")
Returns:
    True se a parti├º├úo foi apagada com sucesso
'''
        self._log(f'Apagando parti├º├úo: {name} ({size_str})')
        result = self.protocol.send_erase_partition(name, size_str)
        if result:
            self._log(f'Particao {name} apagada')
            return result
        self._log(f'Falha ao apagar {name}', 'error')
        return result
    def flash_partition(self, name: str, data: bytes, on_progress=None) -> bool:
        '''
Grava dados numa parti├º├úo.
     1. L├¬ arquivo do disco
     2. send_select_partition(partition, data_len, false, CMD_START_DATA)
     3. Loop send_midst(chunk) com chunk=1016B
     4. send_end()
Nota: o usa 1016B por chunk (linha 229), diferente dos
528B usados no download de FDL. Isso porque na fase ADD o frame
HDLC tem menos overhead de escaping.
Args:
    name: nome da parti├º├úo
    data: bytes a gravar
    on_progress: callback(sent, total) para progress bar
'''
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
        '''
Executa recovery command: apaga misc e grava dados de recovery.
     1. ErasePartition("misc", "1M")
     2. FlashPartition("misc", files)
Os dados de misc v├¬m de Data/Misc/1-6 no (arquivos bin├írios
com comandos de recovery). No UNION, esses dados s├úo passados
diretamente como bytes.
Args:
    misc_data: bytes do arquivo misc (recovery command payload)
'''
        self._log('Executando recovery command...')
        if not self.erase_partition('misc', '1M'):
            return False
        if not self.flash_partition('misc', misc_data):
            return False
        self._log('Recovery command OK')
        return True
    def erase_frp(self) -> bool:
        '''
Apaga parti├º├úo FRP (persist).
     ErasePartition("persist", "2M")
'''
        self._log('=== ERASE FRP ===')
        return self.erase_partition('persist', '2M')
    def erase_data_and_frp(self) -> bool:
        '''
Apaga userdata + FRP.
     Erase_Data() + Erase_FRP()
     1. ErasePartition("misc", "1M")
     2. Obt├®m tamanho de userdata
     3. Se tamanho ok ÔåÆ erase userdata + flash userdata
     4. Se 0 ÔåÆ recovery command com misc/1
Simplifica├º├úo UNION: apagamos misc e userdata diretamente,
sem a l├│gica complexa de send_check_partition_size.
O spd_dump e a pr├ítica real mostram que erase direto funciona.
'''
        self._log('=== ERASE DATA + FRP ===')
        if not self.erase_partition('misc', '1M'):
            return False
        if not self.erase_partition('userdata', '1M'):
            self._log('Falha ao apagar userdata ÔÇö tentando recovery', 'warning')
        return self.erase_frp()
    def recovery_wipe_and_frp(self, misc_data: bytes) -> bool:
        '''
Recovery command + erase FRP.
     Todas as 5 variantes de recovery seguem o mesmo padr├úo:
     Recovery_Command(misc_data) + Erase_FRP()
A diferen├ºa entre as variantes ├® apenas o conte├║do do misc_data
(diferentes bin├írios em Data/Misc/1-5 com comandos de recovery).
Args:
    misc_data: bytes do arquivo misc apropriado
'''
        self._log('=== RECOVERY + FRP ===')
        if not self.recovery_command(misc_data):
            return False
        return self.erase_frp()
    def erase_frp_only(self) -> bool:
        '''
Apaga somente a parti├º├úo FRP (persist).
     Apenas Erase_FRP() sem tocar em misc/userdata.
'''
        self._log('=== ERASE FRP ONLY ===')
        return self.erase_frp()
    def write_persist_clean(self, persist_data: bytes) -> bool:
        '''
Grava persist.img limpa (m├®todo Moto G35 - testado e aprovado).
Ref: DOCUMENTACAO_MOTOG35_SPD_FRP.md
     write_part persist persist.img ÔåÆ "Write Part Done"
Diferente do erase_frp() que apenas apaga, este grava uma
parti├º├úo persist zerada extra├¡da do firmware .pac original.
Mais seguro para dispositivos onde o erase sozinho n├úo resolve.
Args:
    persist_data: bytes do persist.img limpo (~2MB)
'''
        self._log('=== WRITE PERSIST CLEAN ===')
        return self.flash_partition('persist', persist_data)
    def full_frp_remove(self, persist_data: bytes=None) -> bool:
        '''
Remo├º├úo completa de FRP (m├®todo UNION Produ├º├úo).
Fluxo:
  1. Se persist_data ÔåÆ write persist clean
  2. Sen├úo ÔåÆ erase persist
  3. Erase userdata (factory reset)
  4. Reset
Args:
    persist_data: bytes do persist.img limpo (None = usa erase)
'''
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
        '''
Executa opera├º├úo pelo nome (string do ).
     Switch nas 7 strings de opera├º├úo.
Args:
    operation: nome da opera├º├úo (ex: "ERASE FRP ONLY")
    misc_data: dados misc para opera├º├Áes de recovery
    persist_data: dados persist.img para write (opcional)
Returns:
    True se opera├º├úo executou com sucesso
'''
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
