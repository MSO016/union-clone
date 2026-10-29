'''
Protocolo BSL: comandos send_* e processamento de respostas.
Ver: alan/documentacao/16-08-2026-ARQUITETURA-SPD-INTERNA/01_MAPA_REFERENCIAS_INTERNAS.md
'''
import struct
import logging
from typing import Optional, Tuple
from .constants import (BSL_CMD_CHECK_BAUD, BSL_CMD_CONNECT, BSL_CMD_START_DATA, BSL_CMD_MIDST_DATA, BSL_CMD_END_DATA, BSL_CMD_EXEC_DATA, BSL_CMD_NORMAL_RESET, BSL_CMD_ERASE_FLASH, BSL_CMD_READ_START, BSL_CMD_READ_MIDST, BSL_CMD_READ_END, BSL_CMD_KEEP_CHARGE, BSL_CMD_READ_FLASH_INFO, BSL_CMD_ENABLE_WRITE_FLASH, BSL_CMD_DISABLE_TRANSCODE, BSL_CMD_POWER_OFF, BSL_CMD_READ_PARTITION, BSL_REP_ACK, BSL_REP_VER, BSL_REP_READ_FLASH, BSL_REP_VERIFY_ERROR, BSL_REP_INCOMPATIBLE_PARTITION, BSL_REP_DOWN_SIZE_ERROR, BSL_REP_SIGN_VERIFY_ERROR, BSL_REP_NOT_ENABLE_WRITE_FLASH, BSL_REP_READ_PARTITION, BSL_REP_UNSUPPORTED_COMMAND, REP_NAMES, FDL_CHUNK_SIZE)
from .checksum import Checksum
from .hdlc import (generate_packet, parse_packet, parse_packet_no_transcode, str_to_size)
from .transport import SerialTransport
logger = logging.getLogger(__name__)
class SPDProtocol:
    '''
Protocolo BSL para comunica├º├úo com dispositivos Spreadtrum/Unisoc.
Orquestra todos os comandos BSL sobre um SerialTransport,
gerencia o checksum ativo (CRC16/ADD), e processa respostas.
     Vari├íveis de estado: isACK, isReadFlash, isPartitionOperation,
     buffer, logs_on, response.
'''
    def __init__(self, transport: SerialTransport):
        self.transport = transport
        self.checksum = Checksum()
        self.is_ack = True
        self.is_read_flash = False
        self.version = ''
        self.read_buffer = None
        self.last_read_data = b''
        self._cancel = False
        self.da_disable_hdlc = False
        self.da_support_raw_data = False
        self.da_storage_type = 0
        self.on_log = None
    def cancel(self):
        '''Sinaliza cancelamento para opera├º├Áes em andamento.'''
        self._cancel = True
    def reset_cancel(self):
        '''Reseta flag de cancelamento.'''
        self._cancel = False
    def _check_cancel(self):
        '''Verifica se foi cancelado e lan├ºa exce├º├úo.'''
        if self._cancel:
            raise OperationCancelledError('Opera├º├úo cancelada pelo usu├írio')
    def _log(self, msg: str, level: str='info'):
        '''Log interno + callback externo.'''
        getattr(logger, level, logger.info)(msg)
        if self.on_log:
            self.on_log(msg, level)
    def _send_command(self, command: int, data: bytes=b'', timeout: float=None) -> Tuple[int, bytes, bool]:
        '''
Envia comando BSL e retorna a resposta parseada.
Suporta dois modos:
- Transcode (HDLC): 0x7E + escaping 0x7D + 0x7E (default)
- Non-transcode: 0x7E + dados SEM escaping + 0x7E
     Ambos os modos usam 0x7E como delimitador.
     A diferenca ├® apenas o byte stuffing (escape 0x7D).
     Ent├úo RX SEMPRE usa read_hdlc_frame (l├¬ entre 0x7E).
Returns:
    (response_cmd, response_data, checksum_ok)
'''
        self._check_cancel()
        transcode = self.transport.transcode
        frame = generate_packet(command, data, self.checksum, transcode=transcode)
        self.transport.write(frame)
        raw_response = self.transport.read_hdlc_frame(timeout=timeout)
        if not raw_response:
            self._log('Sem resposta do dispositivo (timeout)', 'warning')
            self.is_ack = False
            return (None, None, False)
        if transcode:
            response_cmd, response_data, chk_ok = parse_packet(raw_response, self.checksum)
        else:
            response_cmd, response_data, chk_ok = parse_packet_no_transcode(raw_response, self.checksum)
        return response_cmd, response_data, chk_ok
    def _process_response(self, response_cmd: int, response_data: bytes, chk_ok: bool) -> bool:
        '''
Processa a resposta do dispositivo e atualiza estado.
     Interpreta response code e atualiza isACK, isReadFlash,
     buffer, version conforme o tipo de resposta.
Args:
    response_cmd: c├│digo da resposta BSL
    response_data: dados da resposta
    chk_ok: se o checksum bateu
Returns:
    True se ACK/sucesso, False se erro
'''
        if response_cmd is None:
            self.is_ack = False
            return False
        rep_name = REP_NAMES.get(response_cmd, f'0x{response_cmd:02X}')
        if response_cmd == BSL_REP_VER:
            if response_data:
                self.version = response_data.rstrip(b'\x00').decode('utf-8', errors='replace')
                self._log(f'Boot version: {self.version}')
            self.is_ack = True
            return True
        if response_cmd == BSL_REP_ACK:
            self.is_ack = True
            return True
        if response_cmd == BSL_REP_READ_FLASH:
            if chk_ok and response_data:
                self.read_buffer = bytes(response_data)
            else:
                self.read_buffer = None
            self.is_read_flash = True
            self.is_ack = True
            return True
        if response_cmd == BSL_REP_VERIFY_ERROR:
            self._log('Resposta: Verify Error', 'error')
            self.is_ack = False
            return False
        if response_cmd == BSL_REP_INCOMPATIBLE_PARTITION:
            self._parse_da_info(response_data)
            self._log('Resposta: Incompatible Partition (n├úo bloqueia)')
            self.is_ack = True
            return True
        if response_cmd == BSL_REP_DOWN_SIZE_ERROR:
            self._log('Resposta: Download Size Error', 'error')
            self.is_ack = False
            return False
        if response_cmd == BSL_REP_SIGN_VERIFY_ERROR:
            self._log('Resposta: Sign Verify Error ÔÇö FDL rejeitado', 'error')
            self.is_ack = False
            return False
        if response_cmd == BSL_REP_NOT_ENABLE_WRITE_FLASH:
            self._log('Flash n├úo habilitada ÔÇö enviando enable_flash', 'warning')
            self.is_ack = True
            return True
        if response_cmd == BSL_REP_UNSUPPORTED_COMMAND:
            self._log('Comando nao suportado pelo FDL2', 'warning')
            self.is_ack = False
            return False
        self._log(f'Resposta: {rep_name} (tratada como ACK)')
        self.is_ack = True
        return True
    def _parse_da_info(self, data: bytes) -> None:
        '''
Parseia DA_INFO_T do payload INCOMPATIBLE_PARTITION.
     Se come├ºa com "newt" (0x7477656e): formato TLV
       tag=0 ÔåÆ bDisableHDLC
       tag=2 ÔåÆ bSupportRawData
       tag=3 ÔåÆ dwFlushSize
       tag=6 ÔåÆ dwStorageType
     Sen├úo: memcpy direto para DA_INFO_T struct
'''
        if not data or len(data) < 4:
            return
        if data[:4] == b'newt':
            pos = 4
            while pos + 3 <= len(data):
                tag = data[pos]
                val_type = data[pos + 1]
                val_len = data[pos + 2]
                pos += 3
                if pos + val_len > len(data):
                    break
                val_bytes = data[pos:pos + val_len]
                pos += val_len
                if tag == 0 and val_len >= 1:
                    self.da_disable_hdlc = val_bytes[0] != 0
                elif tag == 2 and val_len >= 1:
                    self.da_support_raw_data = val_bytes[0] != 0
                elif tag == 6 and val_len >= 4:
                    self.da_storage_type = struct.unpack('<I', val_bytes[:4])[0]
            logger.info(f'DA_INFO (TLV): disable_hdlc={self.da_disable_hdlc}, raw_data={self.da_support_raw_data}, storage=0x{self.da_storage_type:X}')
            return
        if len(data) >= 12:
            self.da_disable_hdlc = struct.unpack('<I', data[4:8])[0] != 0
            if len(data) >= 10:
                self.da_support_raw_data = data[9] != 0
            if len(data) >= 16:
                self.da_storage_type = struct.unpack('<I', data[12:16])[0]
            logger.info(f'DA_INFO (struct): disable_hdlc={self.da_disable_hdlc}, raw_data={self.da_support_raw_data}, storage=0x{self.da_storage_type:X}')
    def _send_and_process(self, command: int, data: bytes=b'', timeout: float=None) -> bool:
        '''Envia comando e processa resposta num ├║nico passo.'''
        cmd, resp_data, chk_ok = self._send_command(command, data, timeout)
        return self._process_response(cmd, resp_data, chk_ok)
    def send_checkbaud(self) -> bool:
        '''
Envia ping de baud rate (0x7E raw, sem pacote BSL).
     generate_packet(CMD_CHECK_BAUD) retorna [0x7E] (caso especial).
     O dispositivo responde com REP_VER (vers├úo do bootloader).
'''
        return self._send_and_process(BSL_CMD_CHECK_BAUD)
    def send_connect(self) -> bool:
        '''
Estabelece conex├úo com o dispositivo.
     Envia CMD_CONNECT sem dados. Resposta: REP_ACK.
     Chamado duas vezes: antes do FDL1 e ap├│s FDL1 executar.
     return self.send_data(generate_packet(BSL_CMD_CONNECT))
'''
        return self._send_and_process(BSL_CMD_CONNECT)
    def send_enable_flash(self) -> bool:
        '''
Habilita escrita na flash.
     CMD_ENABLE_WRITE_FLASH sem dados. Chamado ap├│s FDL2 executar.
     Obrigat├│rio antes de qualquer erase/write de parti├º├úo.
'''
        return self._send_and_process(BSL_CMD_ENABLE_WRITE_FLASH)
    def send_read_flash_info(self) -> bool:
        '''
L├¬ informa├º├Áes da flash (inicializa subsistema de storage no FDL2).
     DISABLE_TRANSCODE e partition_list:
     encode_msg_nocpy(io, BSL_CMD_READ_FLASH_INFO, 0);
     send_msg(io); ret = recv_msg(io);
     if (ret) { ret = recv_type(io); }
Este comando pode ser necess├írio para que o FDL2 inicialize
o driver de storage (eMMC/UFS/NAND) e habilite comandos de
parti├º├úo como READ_START, READ_PARTITION etc.
'''
        cmd, resp_data, chk_ok = self._send_command(BSL_CMD_READ_FLASH_INFO, timeout=5.0)
        if cmd is not None:
            self._log(f'READ_FLASH_INFO resposta: 0x{cmd:04X}')
            return True
        self._log('READ_FLASH_INFO sem resposta', 'warning')
        return False
    def send_disable_transcode(self) -> bool:
        '''
Desativa HDLC byte stuffing (escaping 0x7D).
     Ap├│s DISABLE_TRANSCODE, os frames AINDA usam 0x7E como
     delimitador, mas SEM escape de bytes internos.
     Isso ├® "non-transcode mode", N├âO "raw mode sem 0x7E".
     encode_msg_nocpy(io, BSL_CMD_DISABLE_TRANSCODE, 0);
     if (!send_and_check(io)) io->flags &= ~FLAGS_TRANSCODE;
Fluxo:
1. Envia DISABLE_TRANSCODE em HDLC (transcode=True)
2. Se ACK, muda transport para non-transcode
3. Flush buffer serial
'''
        ok = self._send_and_process(BSL_CMD_DISABLE_TRANSCODE)
        if ok:
            self.transport.set_transcode(False)
            self.transport.flush_input()
            self._log('Transcode desativado ÔÇö non-transcode mode ativo')
            return ok
        self._log('DISABLE_TRANSCODE nao suportado ÔÇö mantendo HDLC', 'warning')
        return ok
    def send_keepcharge(self) -> bool:
        '''
Mant├®m carregamento da bateria durante opera├º├Áes.
     CMD_KEEP_CHARGE sem dados.
'''
        return self._send_and_process(BSL_CMD_KEEP_CHARGE)
    def send_reset(self) -> bool:
        '''
Reinicia o dispositivo.
     CMD_NORMAL_RESET sem dados. Tamb├®m faz Dispose() da serial.
     Aqui s├│ enviamos o comando ÔÇö o cleanup ├® feito pelo caller.
'''
        self._log('Reiniciando dispositivo...')
        return self._send_and_process(BSL_CMD_NORMAL_RESET)
    def send_power_off(self) -> bool:
        '''
Desliga o dispositivo.
     N├úo implementado no , mas dispon├¡vel no spd_dump.
'''
        self._log('Desligando dispositivo...')
        return self._send_and_process(BSL_CMD_POWER_OFF)
    def send_start_data(self, addr: int, total_size: int) -> bool:
        """
Inicia transfer├¬ncia de dados (FDL ou parti├º├úo) para um endere├ºo.
     Payload: parse_reverse(BitConverter.GetBytes(total_size) ++ GetBytes(addr))
     BitConverter em C# ├® LE. parse_reverse inverte o array inteiro.
     Resultado final: addr(4B BE) + size(4B BE).
     addr.to_bytes(4, 'big') + total_size.to_bytes(4, 'big')
     Mesmo resultado, mais claro.
Args:
    addr: endere├ºo de destino no dispositivo
    total_size: tamanho total dos dados em bytes
"""
        data = struct.pack('>II', addr, total_size)
        return self._send_and_process(BSL_CMD_START_DATA, data)
    def send_midst_data(self, chunk: bytes) -> bool:
        '''
Envia chunk de dados durante transfer├¬ncia.
     CMD_MIDST_DATA com os bytes do chunk.
     Tamanho t├¡pico: 528 bytes (uni.MIDST_SIZE).
     return self.send_data(generate_packet(BSL_CMD_MIDST_DATA, data))
Args:
    chunk: bytes do chunk (max ~528B com CRC16, ~1016B com ADD)
'''
        return self._send_and_process(BSL_CMD_MIDST_DATA, chunk)
    def send_end_data(self) -> bool:
        '''
Finaliza transfer├¬ncia de dados.
     CMD_END_DATA sem dados.
'''
        return self._send_and_process(BSL_CMD_END_DATA)
    def send_exec_data(self) -> bool:
        '''
Executa c├│digo no endere├ºo previamente carregado.
     CMD_EXEC_DATA sem dados.
     Usado para executar FDL1 (ap├│s carregar na SRAM) e FDL2.
'''
        return self._send_and_process(BSL_CMD_EXEC_DATA)
    def _build_partition_struct(self, name: str, size: int, mode64: bool=False) -> bytes:
        '''
Monta a estrutura de sele├º├úo de parti├º├úo.
     Estrutura 32-bit (76 bytes): nome_utf16le + padding_zeros + size_4B_LE
     Estrutura 64-bit (88 bytes): nome_utf16le + padding + flag_0x01 + size_8B_LE
     O nome ├® codificado em UTF-16LE (Encoding.Unicode no C#).
     O padding preenche at├® o total_length.
Modo 32-bit (76B total):
  ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö¼ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö¼ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ
  Ôöé nome UTF-16LE      Ôöé zeros    Ôöé size 4B Ôöé
  Ôöé (N bytes)          Ôöé (pad)    Ôöé LE      Ôöé
  ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö┤ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö┤ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ
            72 bytes de nome+pad          4B
Modo 64-bit (88B total):
  ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö¼ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö¼ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö¼ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ
  Ôöé nome UTF-16LE      Ôöé zeros    Ôöé 0x01 Ôöé size 8B  Ôöé
  Ôöé (N bytes)          Ôöé (pad)    Ôöé      Ôöé LE       Ôöé
  ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö┤ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö┤ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö┤ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ
Args:
    name: nome da parti├º├úo (ex: "persist", "userdata")
    size: tamanho em bytes
    mode64: True para struct de 88 bytes (UFS/64-bit)
'''
        name_bytes = name.encode('utf-16-le')
        if mode64:
            total_length = 88
            size_bytes = struct.pack('<I', size & 4294967295)
            padding_len = total_length - len(name_bytes) - len(size_bytes)
            result = name_bytes + b'\x00' * padding_len + size_bytes
            part_a = result[:78]
            flag = b'\x01'
            part_c = result[79:88]
            result = part_a + flag + part_c
            return result
        total_length = 76
        size_bytes = struct.pack('<I', size & 4294967295)
        padding_len = total_length - len(name_bytes) - len(size_bytes)
        result = name_bytes + b'\x00' * padding_len + size_bytes
        return result
    def send_erase_partition(self, name: str, size_str: str='1M', mode64: bool=False) -> bool:
        '''
Apaga uma parti├º├úo pelo nome.
     uni.send_select_partition(name, size, false, CMD_ERASE_FLASH)
Fluxo: monta struct de parti├º├úo ÔåÆ envia como CMD_ERASE_FLASH.
Args:
    name: nome da parti├º├úo (ex: "persist")
    size_str: tamanho como string (ex: "2M", "1M")
    mode64: True para modo 64-bit
'''
        self._log(f'Apagando parti├º├úo: {name} ({size_str})')
        size = str_to_size(size_str)
        data = self._build_partition_struct(name, size, mode64)
        return self._send_and_process(BSL_CMD_ERASE_FLASH, data)
    def send_read_start(self, name: str, size_str: str='256G', mode64: bool=True) -> bool:
        '''
Inicia leitura de parti├º├úo pelo nome.
     Usado por send_check_partition_size para descobrir tamanho.
Args:
    name: nome da parti├º├úo
    size_str: tamanho m├íximo estimado
    mode64: normalmente True para read
'''
        size = str_to_size(size_str)
        data = self._build_partition_struct(name, size, mode64)
        return self._send_and_process(BSL_CMD_READ_START, data)
    def send_read_midst(self, read_size: int, offset: int, offset_hi: int=0) -> bool:
        '''
L├¬ chunk de dados de uma parti├º├úo.
     Payload: total(4B LE) + len(4B LE)
     Overload com 12 bytes: size(4B) + offset(4B) + offset_hi(4B)
Args:
    read_size: quantidade de bytes para ler neste chunk
    offset: offset na parti├º├úo (low 32-bit)
    offset_hi: offset alto (high 32-bit, para parti├º├Áes > 4GB)
'''
        data = struct.pack('<III', read_size, offset, offset_hi)
        cmd, resp_data, chk_ok = self._send_command(BSL_CMD_READ_MIDST, data)
        if cmd == BSL_REP_READ_FLASH and resp_data:
            self.last_read_data = resp_data
        else:
            self.last_read_data = b''
        return self._process_response(cmd, resp_data, chk_ok)
    def send_read_end(self) -> bool:
        '''
Finaliza leitura de parti├º├úo.
     CMD_READ_END sem dados.
'''
        return self._send_and_process(BSL_CMD_READ_END)
    def send_read_partition_table(self) -> Optional[bytes]:
        '''
Solicita tabela de parti├º├Áes ao dispositivo.
     Envia BSL_CMD_READ_PARTITION (0x2D).
     Resposta BSL_REP_READ_PARTITION (0xBA) com payload binario.
     Cada entry = 76 bytes (72 name UTF-16LE + 4 size LE).
Returns:
    bytes do payload da tabela ou None se nao suportado/erro.
'''
        cmd, resp_data, chk_ok = self._send_command(BSL_CMD_READ_PARTITION, timeout=10.0)
        if cmd == BSL_REP_READ_PARTITION and resp_data:
            self._log('READ_PARTITION suportado pelo dispositivo')
            return resp_data
        if cmd == BSL_REP_UNSUPPORTED_COMMAND:
            self._log('READ_PARTITION nao suportado ÔÇö usar traverse')
            return
        if cmd == BSL_REP_ACK:
            return
        self._log(f'READ_PARTITION resposta inesperada: 0x{cmd:02X}' if cmd else 'READ_PARTITION sem resposta')
    def check_partition_exists(self, name: str) -> bool:
        '''
Verifica se uma parti├º├úo existe no dispositivo.
     READ_START(name, 8B) ÔåÆ READ_MIDST(8B, offset=0) ÔåÆ READ_END
     Se READ_MIDST retorna REP_READ_FLASH ÔåÆ parti├º├úo existe.
IMPORTANTE: Se READ_START retorna UNSUPPORTED_COMMAND ou timeout,
N├âO enviar READ_END ÔÇö n├úo h├í sess├úo aberta. Enviar READ_END
nesse caso trava o dispositivo.
'''
        read_start_ok = False
        try:
            size = 8
            data = self._build_partition_struct(name, size, mode64=False)
            cmd, resp_data, chk_ok = self._send_command(BSL_CMD_READ_START, data, timeout=3.0)
            if cmd == BSL_REP_UNSUPPORTED_COMMAND:
                return False
            if cmd is None:
                return False
            if cmd != BSL_REP_ACK:
                return False
            read_start_ok = True
            midst_data = struct.pack('<III', 8, 0, 0)
            cmd2, resp_data2, chk_ok2 = self._send_command(BSL_CMD_READ_MIDST, midst_data, timeout=3.0)
            self._try_read_end()
            return cmd2 == BSL_REP_READ_FLASH
        except Exception:
            if read_start_ok:
                self._try_read_end()
            return False
    def _try_read_end(self):
        '''Tenta enviar READ_END para limpar estado, ignorando erros.'''
        try:
            self._send_command(BSL_CMD_READ_END, timeout=1.0)
            return
        except Exception:
            return
    def send_write_partition_start(self, name: str, size: int, mode64: bool=False) -> bool:
        '''
Inicia escrita numa parti├º├úo (como CMD_START_DATA com struct de parti├º├úo).
     uni.send_select_partition(name, size, false, CMD_START_DATA)
Args:
    name: nome da parti├º├úo
    size: tamanho dos dados a gravar
    mode64: True para modo 64-bit
'''
        self._log(f'Iniciando escrita em: {name} ({size} bytes)')
        data = self._build_partition_struct(name, size, mode64)
        return self._send_and_process(BSL_CMD_START_DATA, data)
    def send_file_chunks(self, file_data: bytes, chunk_size: int=None, on_progress=None) -> bool:
        '''
Envia dados em chunks via CMD_MIDST_DATA.
     Divide os dados em chunks de MIDST_SIZE (528B).
     Para cada chunk: send_midst(chunk).
     Ap├│s todos: send_end().
Args:
    file_data: bytes completos do arquivo
    chunk_size: tamanho de cada chunk (default: FDL_CHUNK_SIZE=528)
    on_progress: callback(sent, total) para progress bar
Returns:
    True se todos os chunks foram aceitos
'''
        chunk_size = chunk_size or FDL_CHUNK_SIZE
        total = len(file_data)
        sent = 0
        while sent < total:
            self._check_cancel()
            end = min(sent + chunk_size, total)
            chunk = file_data[sent:end]
            if not self.send_midst_data(chunk):
                self._log(f'Erro no chunk offset={sent}', 'error')
                return False
            sent = end
            if on_progress:
                on_progress(sent, total)
        return True
class OperationCancelledError(Exception):
    '''Exce├º├úo para opera├º├Áes canceladas pelo usu├írio.'''
