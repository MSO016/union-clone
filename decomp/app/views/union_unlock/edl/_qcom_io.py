'''
Operacoes de I/O Qualcomm via comunicacao direta.
TECH UNION SOLUTIONS
'''
import logging
import os
import struct
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import (Callable, List, Optional, Tuple)
import serial
import serial.tools.list_ports
_logger = logging.getLogger('qcom_io')
_XML_H = b'<?xml version="1.0" encoding="UTF-8" chimerais="power"?>'
_PARTITIONS_CRITICAS = frozenset({'tz', 'aop', 'hyp', 'rpm', 'xbl', 'pmic', 'sbl1', 'sbl2', 'sbl3', 'shrm', 'uefi', 'aboot', 'qupfw', 'cmnlib', 'devcfg', 'imagefv', 'cmnlib64', 'keymaster', 'uefisecapp', 'xbl_config', 'multiimgoem'})
_CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
def detectar_porta_edl() -> Optional[str]:
    '''Detecta porta COM em modo EDL (Qualcomm 9008).'''
    for p in serial.tools.list_ports.comports():
        desc = (p.description or '').lower()
        vid_pid = f'{p.vid or 0:04X}:{p.pid or 0:04X}'
        if '9008' not in desc and vid_pid != '05C6:9008':
            if not 'qualcomm' in desc:
                continue
        return p.device
class QcomSession:
    '''Sessao de comunicacao direta com dispositivo Qualcomm em modo Firehose.'''
    ''
    ''
    ''
    def __init__(self, port: str, memory: str='emmc', log_cb: Optional[Callable[[str], None]]=None, progress_cb: Optional[Callable[[int], None]]=None):
        self._port = port
        self._memory = memory
        self._log_cb = log_cb
        self._progress_cb = progress_cb
        self._ser = None
        self._max_payload = 1048576
        self._partitions = []
    @property
    def is_active(self) -> bool:
        return self._ser is not None and self._ser.is_open
    @property
    def memory(self) -> str:
        return self._memory
    @property
    def partitions(self) -> List[Tuple[str, int, int, float]]:
        return self._partitions
    def _log(self, msg: str):
        _logger.debug(msg)
        if self._log_cb:
            self._log_cb(msg)
    def _progress(self, val: int):
        if self._progress_cb:
            self._progress_cb(val)
    def _recv(self, token: bytes, timeout_s: float=5.0) -> bytes:
        ser = self._ser
        buf = b''
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            w = ser.in_waiting
            if w > 0:
                buf += ser.read(w)
                if token in buf:
                    time.sleep(0.05)
                    if ser.in_waiting:
                        buf += ser.read(ser.in_waiting)
                    return buf
            else:
                time.sleep(0.01)
        return buf
    def _send(self, data: bytes, chunk_sz: int=512):
        for i in range(0, len(data), chunk_sz):
            self._ser.write(data[i:i + chunk_sz])
    def _flush_rx(self, duration: float=1.0):
        ser = self._ser
        deadline = time.time() + duration
        while time.time() < deadline:
            w = ser.in_waiting
            if w > 0:
                ser.read(w)
            else:
                time.sleep(0.02)
    def _verify_session(self) -> bool:
        '''Verifica se a sessao esta viva via NOP.'''
        ser = self._ser
        nop = _XML_H + b'<data><nop /></data>'
        for attempt in range(3):
            self._flush_rx(0.5 + attempt * 0.5)
            ser.reset_input_buffer()
            time.sleep(0.05)
            ser.write(nop)
            ser.flush()
            resp = self._recv(b'ACK', timeout_s=5.0)
            if b'VIP is enabled' in resp:
                return False
            if b'ACK' in resp:
                return True
        return False
    def sahara(self, loader_path: str, qsahara_path: str) -> bool:
        '''Upload do loader via QSaharaServer (protocolo Sahara).'''
        if not os.path.isfile(loader_path):
            self._log('Arquivo de suporte nao encontrado.')
            return False
        if not os.path.isfile(qsahara_path):
            self._log('Componente QSahara nao disponivel.')
            return False
        size_kb = os.path.getsize(loader_path) / 1024
        self._log(f'Enviando programador [{size_kb:.0f} KB]...')
        port_arg = f'\\\\.\\{self._port}'
        args = [str(qsahara_path), '-p', port_arg, '-s', f'13:{loader_path}']
        try:
            proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=str(Path(loader_path).parent), creationflags=_CREATE_NO_WINDOW)
            timer = threading.Timer(30, proc.kill)
            timer.start()
            stdout, _ = proc.communicate()
            timer.cancel()
            out = stdout.decode('utf-8', errors='replace')
        except Exception as e:
            _logger.error(f'sahara: {e}')
            self._log('Falha na comunicacao inicial.')
            return False
        ok = 'File transferred successfully' in out or 'Sahara protocol completed' in out
        if ok:
            self._log('Programador carregado.')
            return ok
        _logger.error(f'sahara output: {out[-300:]}')
        self._log('Falha ao carregar programador.')
        return ok
    def _recv_sahara_pkt(self, timeout_s: float=5.0) -> Optional[bytes]:
        '''Recebe um unico pacote do protocolo Sahara (leitura exata).'''
        ser = self._ser
        buf = b''
        deadline = time.time() + timeout_s
        while len(buf) < 8 and time.time() < deadline:
            w = ser.in_waiting
            if w > 0:
                buf += ser.read(min(w, 8 - len(buf)))
            else:
                time.sleep(0.01)
        if len(buf) < 8:
            return
        pkt_len = struct.unpack('<I', buf[4:8])[0]
        if pkt_len < 8 or pkt_len > 4096:
            _logger.warning('sahara_pkt: tamanho invalido %d', pkt_len)
            return buf
        while len(buf) < pkt_len and time.time() < deadline:
            w = ser.in_waiting
            if w > 0:
                buf += ser.read(min(w, pkt_len - len(buf)))
            else:
                time.sleep(0.01)
        if len(buf) >= pkt_len:
            return buf[:pkt_len]
    def sahara_direct(self, loader_path: str) -> bool:
        '''Upload do loader via protocolo Sahara direto (porta permanece aberta).
        Diferente de sahara() que usa QSaharaServer como subprocesso,
        este metodo mantem a sessao serial aberta para evitar que o
        dispositivo resete ao fechar a porta ÔÇö necessario para chipsets
        que reiniciam ao perder a conexao USB (ex: SM7475).
        '''
        if not os.path.isfile(loader_path):
            self._log('Arquivo de suporte nao encontrado.')
            return False
        with open(loader_path, 'rb') as f:
            loader_data = f.read()
        size_kb = len(loader_data) / 1024
        self._log(f'Enviando programador [{size_kb:.0f} KB]...')
        port_path = f'\\\\.\\{self._port}'
        try:
            ser = serial.Serial(port=port_path, baudrate=115200, timeout=1, write_timeout=10, xonxoff=False)
        except serial.SerialException as e:
            _logger.error('sahara_direct open port: %s', e)
            self._log('Falha ao acessar porta de comunicacao.')
            return False
        self._ser = ser
        _logger.debug('sahara_direct: porta %s aberta', port_path)
        try:
            return self._sahara_protocol(loader_data)
        except Exception as e:
            _logger.error('sahara_direct: %s', e)
            self._log('Falha na comunicacao inicial.')
            self.close()
            return False
    def _sahara_protocol(self, loader_data: bytes) -> bool:
        '''Executa protocolo Sahara completo sobre sessao serial aberta.'''
        ser = self._ser
        hello = self._recv_sahara_pkt(timeout_s=5.0)
        if not hello:
            _logger.debug('sahara: sem HELLO, enviando RESET')
            ser.write(struct.pack('<II', 7, 8))
            ser.flush()
            hello = self._recv_sahara_pkt(timeout_s=5.0)
        if not hello:
            _logger.error('sahara: device nao enviou HELLO')
            self._log('Dispositivo nao respondeu.')
            self.close()
            return False
        cmd = struct.unpack('<I', hello[:4])[0]
        if cmd != 1:
            _logger.error('sahara: esperado HELLO(0x01), recebido 0x%02X', cmd)
            self.close()
            return False
        version = struct.unpack('<I', hello[8:12])[0]
        compat = struct.unpack('<I', hello[12:16])[0]
        mode = struct.unpack('<I', hello[20:24])[0]
        _logger.debug('sahara: HELLO v%d compat=%d mode=%d', version, compat, mode)
        hello_rsp = struct.pack('<IIIIII', 2, 48, version, compat, 0, mode) + b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        ser.write(hello_rsp)
        ser.flush()
        bytes_sent = 0
        total = len(loader_data)
        while True:
            pkt = self._recv_sahara_pkt(timeout_s=15.0)
            if not pkt:
                _logger.error('sahara: timeout aguardando READ_DATA')
                self.close()
                return False
            pkt_cmd = struct.unpack('<I', pkt[:4])[0]
            if pkt_cmd == 3:
                offset = struct.unpack('<I', pkt[12:16])[0]
                length = struct.unpack('<I', pkt[16:20])[0]
                if offset + length > total:
                    _logger.error('sahara: READ fora do loader (%d+%d > %d)', offset, length, total)
                    self.close()
                    return False
                ser.write(loader_data[offset:offset + length])
                ser.flush()
                bytes_sent += length
            elif pkt_cmd == 18:
                offset = struct.unpack('<Q', pkt[12:20])[0]
                length = struct.unpack('<Q', pkt[20:28])[0]
                if offset + length > total:
                    _logger.error('sahara: READ64 fora do loader')
                    self.close()
                    return False
                ser.write(loader_data[offset:offset + length])
                ser.flush()
                bytes_sent += length
            elif pkt_cmd == 4:
                status = struct.unpack('<I', pkt[12:16])[0]
                if status != 0:
                    _logger.error('sahara: END_IMAGE_TX status=%d', status)
                    self.close()
                    return False
                _logger.debug('sahara: image TX completo (%d bytes)', bytes_sent)
                break
            if pkt_cmd == 7:
                _logger.error('sahara: device solicitou RESET')
                self.close()
                return False
            _logger.warning('sahara: cmd desconhecido 0x%02X', pkt_cmd)
        ser.write(struct.pack('<II', 5, 8))
        ser.flush()
        done_rsp = self._recv_sahara_pkt(timeout_s=5.0)
        if done_rsp:
            rsp_cmd = struct.unpack('<I', done_rsp[:4])[0]
            if rsp_cmd == 6:
                _logger.debug('sahara: DONE_RSP OK')
            else:
                _logger.warning('sahara: esperado DONE_RSP(0x06), recebido 0x%02X', rsp_cmd)
        else:
            _logger.warning('sahara: sem DONE_RSP (prosseguindo)')
        time.sleep(0.5)
        self._log('Programador carregado.')
        return True
    def auth(self, digest: bytes, sign: bytes) -> bool:
        '''Autenticacao VIP completa (digest -> verify -> sign -> configure).
        Reutiliza sessao serial aberta pelo sahara_direct quando disponivel.
        '''
        self._log('Autenticando...')
        verify_xml = _XML_H + b'<data><verify EnableVip="0"/></data>'
        if self._ser and self._ser.is_open:
            _logger.info('auth: reutilizando sessao serial (sahara_direct)')
            ser = self._ser
        else:
            port_path = f'\\\\.\\{self._port}'
            _logger.info('auth: abrindo porta %s', port_path)
            try:
                ser = serial.Serial(port=port_path, baudrate=115200, timeout=1, write_timeout=5, xonxoff=False)
            except serial.SerialException as e:
                _logger.error(f'auth open port: {e}')
                self._log('Falha ao acessar porta de comunicacao.')
                return False
            self._ser = ser
        time.sleep(0.3)
        resp = self._recv(b'VIP is enabled', timeout_s=5.0)
        if b'VIP is enabled' not in resp:
            _logger.info('auth: sem VIP announce explicito, prosseguindo')
            if resp:
                self._flush_rx(0.3)
        self._send(digest, 512)
        ser.flush()
        resp = self._recv(b'rawmode="false"', timeout_s=25.0)
        if b"doesn't match" in resp.lower() or b'hash' in resp.lower() and b'error' in resp.lower():
            _logger.error('auth: digest rejected')
            self._log('Autenticacao rejeitada.')
            ser.close()
            self._ser = None
            return False
        if b'ACK' not in resp:
            _logger.error('auth: digest no ACK')
            self._log('Falha na autenticacao.')
            ser.close()
            self._ser = None
            return False
        tcfg = _XML_H + b'<data><transfercfg reboot_type="off" timeout_in_sec="90"/></data>'
        ser.write(tcfg)
        ser.flush()
        self._recv(b'</data>', timeout_s=3.0)
        ser.write(verify_xml)
        ser.flush()
        resp = self._recv(b'rawmode="true"', timeout_s=5.0)
        if b'rawmode="true"' not in resp:
            _logger.error('auth: verify failed')
            self._log('Falha na verificacao.')
            ser.close()
            self._ser = None
            return False
        actual_sign = sign
        if self._memory != 'emmc' and len(sign) < 4096:
            actual_sign = sign + b'\x00' * (4096 - len(sign))
        self._send(actual_sign, 512)
        ser.flush()
        resp = self._recv(b'rawmode="false"', timeout_s=15.0)
        if b"doesn't match" in resp.lower():
            _logger.error('auth: sign rejected')
            self._log('Assinatura rejeitada.')
            ser.close()
            self._ser = None
            return False
        if b'rawmode="false"' not in resp and b'ACK' not in resp:
            _logger.error('auth: sign no confirmation')
            self._log('Falha na assinatura.')
            ser.close()
            self._ser = None
            return False
        ser.write(_XML_H + b'<data><sha256init Verbose="1"/></data>')
        ser.flush()
        self._recv(b'</data>', timeout_s=3.0)
        ser.write(_XML_H + b'<data><nop value="Hello"/></data>')
        ser.flush()
        self._recv(b'ACK', timeout_s=3.0)
        gsi = _XML_H + b'<data><getstorageinfo physical_partition_number="0" slot="0" storage_type="' + self._memory.encode() + b'" verbose="1"/></data>'
        ser.write(gsi)
        ser.flush()
        resp = self._recv(b'rawmode="false"', timeout_s=5.0)
        if b'NAK' in resp:
            alt = 'emmc' if self._memory == 'ufs' else 'ufs'
            _logger.debug(f'auth: storage NAK, trying {alt}')
            self._memory = alt
            gsi = _XML_H + b'<data><getstorageinfo physical_partition_number="0" slot="0" storage_type="' + self._memory.encode() + b'" verbose="1"/></data>'
            ser.write(gsi)
            ser.flush()
            self._recv(b'rawmode="false"', timeout_s=5.0)
        cfg = _XML_H + b'<data><configure AlwaysValidate="0" MaxDigestTableSizeInBytes="0" MaxPayloadSizeToTargetInBytes="4194304" MaxPayloadSizeFromTargetInBytes="4194304" AckRawDataEveryNumPackets="0" MemoryName="' + self._memory.encode() + b'" SkipStorageInit="0" SkipWrite="0" ZLPAwareHost="1" verbose="1"/></data>'
        ser.write(cfg)
        ser.flush()
        resp = self._recv(b'ACK', timeout_s=5.0)
        if b'ACK' in resp:
            idx = resp.find(b'MaxPayloadSizeToTargetInBytesSupported="')
            if idx >= 0:
                val_s = idx + 39
                val_e = resp.find(b'"', val_s)
                if val_e > val_s:
                    try:
                        self._max_payload = int(resp[val_s:val_e])
                    except ValueError:
                        self._max_payload = 1048576
                else:
                    self._max_payload = 1048576
            else:
                self._max_payload = 4194304
        else:
            _logger.warning('auth: configure no ACK')
            self._max_payload = 1048576
        self._log('Autenticacao concluida.')
        return True
    def list_partitions(self) -> List[Tuple[str, int, int, float]]:
        '''Le GPT e retorna lista de particoes: (name, start, end, size_mb).'''
        ser = self._ser
        if not ser or not ser.is_open:
            self._log('Sessao nao disponivel.')
            return []
        sector_sz = 512 if self._memory == 'emmc' else 4096
        read_gpt = _XML_H + b'<data><read SECTOR_SIZE_IN_BYTES="' + str(sector_sz).encode() + b'" num_partition_sectors="34" physical_partition_number="0" start_sector="0" filename="gpt_main0.bin" label="PrimaryGPT"/></data>'
        ser.reset_input_buffer()
        ser.write(read_gpt)
        ser.flush()
        expected = 34 * sector_sz
        buf = b''
        deadline = time.time() + 15.0
        while time.time() < deadline:
            w = ser.in_waiting
            if w > 0:
                buf += ser.read(w)
            else:
                time.sleep(0.01)
            if len(buf) > expected + 300:
                break
        if b'ACK' not in buf:
            _logger.error('list_partitions: no ACK')
            self._log('Falha ao ler mapa de particoes.')
            return []
        rm_idx = buf.find(b'rawmode="true"')
        if rm_idx >= 0:
            data_end = buf.find(b'</data>', rm_idx)
        else:
            ack_idx = buf.find(b'value="ACK"')
            data_end = buf.find(b'</data>', ack_idx)
        if data_end < 0:
            _logger.error('list_partitions: bad format')
            self._log('Formato de resposta inesperado.')
            return []
        binary_start = data_end + 7
        gpt_data = buf[binary_start:]
        remaining = expected - len(gpt_data)
        if remaining > 0:
            old_t = ser.timeout
            ser.timeout = 10
            gpt_data += ser.read(remaining)
            ser.timeout = old_t
        time.sleep(0.1)
        if ser.in_waiting:
            ser.read(ser.in_waiting)
        if len(gpt_data) < expected:
            _logger.error(f'list_partitions: incomplete {len(gpt_data)}/{expected}')
            self._log('Mapa de particoes incompleto.')
            return []
        gpt_data = gpt_data[:expected]
        self._partitions = self._parse_gpt(gpt_data, sector_sz)
        self._log(f'Particoes encontradas: {len(self._partitions)}')
        return self._partitions
    def _parse_gpt(self, data: bytes, sector_sz: int=512) -> List[Tuple[str, int, int, float]]:
        if len(data) < 1152:
            return []
        num_parts = struct.unpack_from('<I', data, 592)[0]
        entry_size = struct.unpack_from('<I', data, 596)[0]
        parts = []
        for i in range(min(num_parts, 128)):
            off = 1024 + i * entry_size
            if off + entry_size > len(data):
                break
            if data[off:off + 16] == b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00':
                break
            start = struct.unpack_from('<Q', data, off + 32)[0]
            end = struct.unpack_from('<Q', data, off + 40)[0]
            name = data[off + 56:off + 56 + 72].decode('utf-16-le', errors='replace').rstrip('\x00')
            sz_mb = (end - start + 1) * sector_sz / 1048576
            parts.append((name, start, end, sz_mb))
        return parts
    def read_partition(self, start: int, sectors: int, output_path: str) -> bool:
        '''Le particao via streaming (comando unico).'''
        ser = self._ser
        if not ser or not ser.is_open:
            self._log('Sessao nao disponivel.')
            return False
        sector_sz = 512 if self._memory == 'emmc' else 4096
        total_bytes = sectors * sector_sz
        total_mb = total_bytes / 1048576
        self._log(f'Lendo {total_mb:.1f} MB...')
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        read_xml = _XML_H + b'<data><read SECTOR_SIZE_IN_BYTES="' + str(sector_sz).encode() + b'" num_partition_sectors="' + str(sectors).encode() + b'" physical_partition_number="0" start_sector="' + str(start).encode() + b'" label="PrimaryGPT" filename="partition.bin"/></data>'
        ser.reset_input_buffer()
        ser.write(read_xml)
        ser.flush()
        header = b''
        deadline = time.time() + 30.0
        while time.time() < deadline:
            w = ser.in_waiting
            if w > 0:
                header += ser.read(w)
            else:
                time.sleep(0.001)
            if b'NAK' in header or b'VIP is enabled' in header:
                _logger.error('read_partition: NAK')
                self._log('Leitura rejeitada pelo dispositivo.')
                return False
            if b'rawmode="true"' in header:
                rm_idx = header.find(b'rawmode="true"')
                tail = header[rm_idx:]
                if b'</data>' in tail:
                    break
        else:
            _logger.error('read_partition: ACK timeout')
            self._log('Timeout na leitura.')
            return False
        if b'ACK' not in header:
            _logger.error('read_partition: no ACK in header')
            self._log('Dispositivo nao confirmou leitura.')
            return False
        rm_idx = header.find(b'rawmode="true"')
        data_end = header.find(b'</data>', rm_idx)
        if data_end < 0:
            self._log('Formato de resposta invalido.')
            return False
        initial = header[data_end + 7:]
        if initial.startswith(b'<?xml') or initial.startswith(b'<'):
            xml_end = initial.find(b'</data>')
            if xml_end >= 0:
                initial = initial[xml_end + 7:]
        bytes_written = len(initial)
        last_progress = 0
        with open(output_path, 'wb') as fout:
            if initial:
                fout.write(initial)
            deadline = time.time() + 600.0
            stall_deadline = time.time() + 60.0
            while bytes_written < total_bytes and time.time() < deadline:
                w = ser.in_waiting
                if w > 0:
                    to_read = min(w, total_bytes - bytes_written)
                    chunk = ser.read(to_read)
                    fout.write(chunk)
                    bytes_written += len(chunk)
                    stall_deadline = time.time() + 60.0
                    pct = int(bytes_written * 100 / total_bytes)
                    if pct >= last_progress + 5:
                        last_progress = pct
                        self._progress(pct)
                else:
                    time.sleep(0.001)
                    if time.time() > stall_deadline:
                        _logger.error(f'read: stall {bytes_written}/{total_bytes}')
                        self._log('Leitura interrompida (sem dados).')
                        break
        final = b''
        deadline = time.time() + 5.0
        while time.time() < deadline:
            w = ser.in_waiting
            if w > 0:
                final += ser.read(w)
            else:
                time.sleep(0.01)
            if b'</data>' in final:
                break
        real_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        if bytes_written >= total_bytes:
            self._log(f'Leitura concluida ({real_size:,} bytes).')
            self._progress(100)
            return True
        if real_size > 0:
            self._log(f'Leitura parcial ({real_size:,}/{total_bytes:,} bytes).')
            return True
        self._log('Nenhum dado recebido.')
        return False
    def erase_partition(self, name: str, start: int, sectors: int) -> bool:
        '''Apaga particao: tenta <erase> direto, fallback para header zero.'''
        ser = self._ser
        if not ser or not ser.is_open:
            self._log('Sessao nao disponivel.')
            return False
        if name.lower() in _PARTITIONS_CRITICAS:
            self._log('Operacao bloqueada por seguranca.')
            return False
        sector_sz = 512 if self._memory == 'emmc' else 4096
        if not self._verify_session():
            self._log('Sessao expirada.')
            return False
        self._log(f'Limpando {name}...')
        erase_xml = _XML_H + b'<data><erase SECTOR_SIZE_IN_BYTES="' + str(sector_sz).encode() + b'" num_partition_sectors="' + str(sectors).encode() + b'" physical_partition_number="0" start_sector="' + str(start).encode() + b'" label="PrimaryGPT"/></data>'
        ser.reset_input_buffer()
        ser.write(erase_xml)
        ser.flush()
        resp = b''
        deadline = time.time() + 30.0
        while time.time() < deadline:
            w = ser.in_waiting
            if w > 0:
                resp += ser.read(w)
            else:
                time.sleep(0.01)
            if b'ACK' in resp or b'NAK' in resp:
                time.sleep(0.2)
                if ser.in_waiting:
                    resp += ser.read(ser.in_waiting)
                break
        if b'ACK' in resp and b'NAK' not in resp:
            self._log(f'{name} limpa.')
            return True
        _logger.debug(f'erase: direct NAK for {name}, fallback to header')
        time.sleep(0.3)
        self._flush_rx(0.5)
        if not self._verify_session():
            self._log('Conexao perdida.')
            return False
        return self.erase_header(name, start, sectors)
    def erase_header(self, name: str, start: int, sectors: int) -> bool:
        '''Invalida particao zerando primeiros bytes do header.'''
        ser = self._ser
        if not ser or not ser.is_open:
            self._log('Sessao nao disponivel.')
            return False
        if name.lower() in _PARTITIONS_CRITICAS:
            self._log('Operacao bloqueada por seguranca.')
            return False
        sector_sz = 512 if self._memory == 'emmc' else 4096
        sectors_to_patch = min(sectors, 2)
        patches = []
        for s_idx in range(sectors_to_patch):
            target = start + s_idx
            patches.append((target, 0, 4, '00000000'))
            patches.append((target, 4, 4, '00000000'))
        if not self._verify_session():
            self._log('Sessao expirada.')
            return False
        self._log(f'Invalidando {name}...')
        for target_sector, offset, size, value in patches:
            patch_xml = _XML_H + b'<data><patch SECTOR_SIZE_IN_BYTES="' + str(sector_sz).encode() + b'" byte_offset="' + str(offset).encode() + b'" filename="DISK" physical_partition_number="0" size_in_bytes="' + str(size).encode() + b'" start_sector="' + str(target_sector).encode() + b'" value="' + value.encode() + b'" what="Update"/></data>'
            ser.reset_input_buffer()
            ser.write(patch_xml)
            ser.flush()
            resp = b''
            deadline = time.time() + 10.0
            while time.time() < deadline:
                w = ser.in_waiting
                if w > 0:
                    resp += ser.read(w)
                else:
                    time.sleep(0.005)
                if b'ACK' in resp or b'NAK' in resp:
                    break
            if b'NAK' in resp:
                _logger.error(f'erase_header: NAK sector={target_sector} off={offset}')
                self._log('Falha na operacao.')
                return False
            if b'ACK' in resp:
                continue
            _logger.error(f'erase_header: no resp sector={target_sector} off={offset}')
            self._log('Dispositivo nao respondeu.')
            return False
        self._log(f'{name} invalidada.')
        return True
    def patch_frp(self, misc_sector: int, frp_sector: int) -> bool:
        '''FRP bypass via patches minimais (misc + frp).'''
        ser = self._ser
        if not ser or not ser.is_open:
            self._log('Sessao nao disponivel.')
            return False
        sector_sz = 512 if self._memory == 'emmc' else 4096
        ser.reset_input_buffer()
        ser.write(_XML_H + b'<data><nop /></data>')
        ser.flush()
        nop_resp = self._recv(b'ACK', timeout_s=5.0)
        if b'ACK' not in nop_resp:
            _logger.error('patch_frp: session dead')
            self._log('Sessao expirada.')
            return False
        self._log('Removendo FRP...')
        patch_misc = _XML_H + b'<data><patch SECTOR_SIZE_IN_BYTES="' + str(sector_sz).encode() + b'" byte_offset="0" filename="DISK" physical_partition_number="0" size_in_bytes="1" start_sector="' + str(misc_sector).encode() + b'" value="0" what="Update"/></data>'
        ser.reset_input_buffer()
        ser.write(patch_misc)
        ser.flush()
        resp = self._recv(b'ACK', timeout_s=10.0)
        if b'NAK' in resp:
            _logger.error('patch_frp: misc NAK')
            self._log('Falha ao limpar flag.')
            return False
        if b'ACK' not in resp:
            _logger.error('patch_frp: misc no response')
            self._log('Dispositivo nao respondeu.')
            return False
        patch_frp = _XML_H + b'<data><patch SECTOR_SIZE_IN_BYTES="' + str(sector_sz).encode() + b'" byte_offset="0" filename="DISK" physical_partition_number="0" size_in_bytes="4" start_sector="' + str(frp_sector).encode() + b'" value="00000000" what="Update"/></data>'
        ser.reset_input_buffer()
        ser.write(patch_frp)
        ser.flush()
        resp = self._recv(b'ACK', timeout_s=10.0)
        if b'NAK' in resp:
            _logger.error('patch_frp: frp NAK')
            self._log('Falha ao limpar protecao.')
            return False
        if b'ACK' not in resp:
            _logger.error('patch_frp: frp no response')
            self._log('Dispositivo nao respondeu.')
            return False
        self._log('FRP removido com sucesso!')
        return True
    def write_partition(self, start: int, sectors: int, data: bytes) -> bool:
        '''Escreve dados em particao via <program> + rawmode.
        ATENCAO: Usar APENAS para particoes pequenas (<10MB).
        Obrigatorio fazer backup (read) antes de qualquer write.
        '''
        ser = self._ser
        if not ser or not ser.is_open:
            self._log('Sessao nao disponivel.')
            return False
        sector_sz = 512 if self._memory == 'emmc' else 4096
        expected_size = sectors * sector_sz
        if len(data) > expected_size:
            _logger.error(f'write: data {len(data)} > expected {expected_size}')
            self._log('Tamanho de dados incompativel.')
            return False
        if len(data) > 10485760:
            self._log('Escrita limitada a particoes pequenas.')
            return False
        if len(data) < expected_size:
            data = data + b'\x00' * (expected_size - len(data))
        if not self._verify_session():
            self._log('Sessao expirada.')
            return False
        self._log('Escrevendo dados...')
        self._write_fw_blocked = False
        _logger.debug(f'write: start={start} sectors={sectors} sector_sz={sector_sz} data_len={len(data)}')
        ok = self._write_program_bulk(ser, start, sectors, sector_sz, data)
        if ok:
            self._log('Escrita concluida.')
            return True
        _logger.debug('write: bulk falhou, tentando setor a setor...')
        self._log('Tentando escrita setor a setor...')
        ok = self._write_sector_by_sector(ser, start, sectors, sector_sz, data)
        if ok:
            self._log('Escrita concluida (setor a setor).')
            return True
        self._write_fw_blocked = True
        self._log('Escrita nao permitida pelo dispositivo.')
        return False
    def _write_program_bulk(self, ser, start, sectors, sector_sz, data):
        '''Tenta program em bloco (rapido, pode falhar em particoes protegidas).'''
        program_xml = _XML_H + b'<data><program SECTOR_SIZE_IN_BYTES="' + str(sector_sz).encode() + b'" num_partition_sectors="' + str(sectors).encode() + b'" physical_partition_number="0" start_sector="' + str(start).encode() + b'" label="PrimaryGPT"/></data>'
        _logger.debug(f'write_bulk: XML = {program_xml[:200]}')
        ser.reset_input_buffer()
        ser.write(program_xml)
        ser.flush()
        resp = self._recv(b'</data>', timeout_s=15.0)
        _logger.debug(f'write_bulk: resp ({len(resp)} B) = {resp[:300]}')
        if b'Failed' in resp or b'NAK' in resp:
            _logger.debug('write_bulk: rejeitado pelo firmware')
            time.sleep(0.2)
            if ser.in_waiting:
                ser.read(ser.in_waiting)
            return False
        if b'ACK' not in resp:
            _logger.debug('write_bulk: sem ACK')
            time.sleep(0.2)
            if ser.in_waiting:
                ser.read(ser.in_waiting)
            return False
        max_payload = 1048576
        bytes_sent = 0
        while bytes_sent < len(data):
            chunk = data[bytes_sent:bytes_sent + max_payload]
            ser.write(chunk)
            ser.flush()
            bytes_sent += len(chunk)
            pct = int(bytes_sent * 100 / len(data))
            self._progress(pct)
        resp = self._recv(b'</data>', timeout_s=30.0)
        _logger.debug(f'write_bulk: resp final ({len(resp)} B) = {resp[:300]}')
        if b'ACK' in resp and b'NAK' not in resp:
            return True
        return False
    def _write_sector_by_sector(self, ser, start, sectors, sector_sz, data):
        '''Fallback: escreve 1 setor por vez (mais lento, mais compativel).'''
        total = sectors
        for i in range(total):
            sector_data = data[i * sector_sz:(i + 1) * sector_sz]
            cur_sector = start + i
            program_xml = _XML_H + b'<data><program SECTOR_SIZE_IN_BYTES="' + str(sector_sz).encode() + b'" num_partition_sectors="1" physical_partition_number="0" start_sector="' + str(cur_sector).encode() + b'"/></data>'
            ser.reset_input_buffer()
            ser.write(program_xml)
            ser.flush()
            resp = self._recv(b'</data>', timeout_s=10.0)
            if b'Failed' in resp or b'NAK' in resp:
                _logger.error(f'write_s2s: setor {cur_sector} rejeitado')
                if ser.in_waiting:
                    ser.read(ser.in_waiting)
                return False
            if b'ACK' not in resp:
                _logger.error(f'write_s2s: setor {cur_sector} sem ACK')
                if ser.in_waiting:
                    ser.read(ser.in_waiting)
                return False
            ser.write(sector_data)
            ser.flush()
            resp = self._recv(b'</data>', timeout_s=10.0)
            if b'ACK' not in resp or b'NAK' in resp:
                _logger.error(f'write_s2s: setor {cur_sector} ACK final falhou')
                return False
            if i % 50 != 0 and i != total - 1:
                continue
            pct = int((i + 1) * 100 / total)
            self._progress(pct)
            _logger.debug(f'write_s2s: {i + 1}/{total} setores')
            continue
        return True
    def reboot(self) -> bool:
        '''Reinicia o dispositivo.'''
        ser = self._ser
        if not ser or not ser.is_open:
            self._log('Sessao nao disponivel.')
            return False
        reboot_xml = _XML_H + b'<data><power value="reset"/></data>'
        try:
            ser.write(reboot_xml)
            ser.flush()
        except (serial.SerialException, OSError):
            self._log('Dispositivo reiniciando...')
            self._ser = None
            return True
        time.sleep(1.0)
        self._log('Dispositivo reiniciando...')
        try:
            ser.close()
        except Exception:
            pass
        self._ser = None
        return True
    def close(self):
        '''Fecha sessao serial de forma segura.'''
        if self._ser:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None
def executar_frp_serial(port: str, loader_path: str, qsahara_path: str, memory: str, digest: bytes, sign: bytes, log_cb: Optional[Callable[[str], None]]=None, progress_cb: Optional[Callable[[int], None]]=None) -> Tuple[bool, str, dict]:
    '''Executa FRP completo via sessao direta.
    Retorna (sucesso, mensagem, device_data).
    '''
    device_data = {}
    t_inicio = time.time()
    session = QcomSession(port, memory, log_cb, progress_cb)
    try:
        if progress_cb:
            progress_cb(5)
        if not session.sahara(loader_path, qsahara_path):
            session.close()
            return False, 'Falha na comunicacao inicial.\nReconecte o dispositivo.', device_data
        time.sleep(0.5)
        if progress_cb:
            progress_cb(15)
        if not session.auth(digest, sign):
            session.close()
            return False, 'Falha na autenticacao.\nVerifique a compatibilidade.', device_data
        device_data['memory'] = session.memory
        if progress_cb:
            progress_cb(35)
        parts = session.list_partitions()
        if not parts:
            session.close()
            return False, 'Nenhuma particao encontrada.\nVerifique o dispositivo.', device_data
        device_data['total_particoes'] = len(parts)
        if progress_cb:
            progress_cb(50)
        misc_sector = None
        frp_sector = None
        for name, start, end, sz in parts:
            nl = name.lower()
            if nl == 'misc' and misc_sector is None:
                misc_sector = start
            elif nl == 'frp':
                if frp_sector is None:
                    frp_sector = start
        if frp_sector is None:
            session.close()
            return False, 'Particao FRP nao encontrada.', device_data
        if misc_sector is None:
            _logger.warning('frp_serial: misc not found, using frp only')
        if progress_cb:
            progress_cb(70)
        if misc_sector:
            ok = session.patch_frp(misc_sector, frp_sector)
        else:
            ok = session.erase_header('frp', frp_sector, 1)
        if not ok:
            session.close()
            return False, 'Falha ao remover FRP.\nTente novamente.', device_data
        device_data['frp_sector'] = frp_sector
        if progress_cb:
            progress_cb(90)
        session.reboot()
        if progress_cb:
            progress_cb(100)
        tempo = time.time() - t_inicio
        device_data['tempo_total'] = round(tempo, 1)
    except Exception as e:
        _logger.error(f'executar_frp_serial: {e}')
        session.close()
        return False, 'Erro inesperado.\nReconecte o dispositivo.', device_data
    finally:
        session.close()
    return True, 'FRP removido com sucesso!', device_data
