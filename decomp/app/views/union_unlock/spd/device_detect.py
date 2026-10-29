'''
Deteccao de dispositivo em Modo SPD.
Ver: alan/documentacao/16-08-2026-ARQUITETURA-SPD-INTERNA/01_MAPA_REFERENCIAS_INTERNAS.md
'''
import logging
import time
from dataclasses import dataclass
from typing import (List, Optional, Tuple)
import serial.tools.list_ports
from .constants import SPRD_VID, SPRD_PID_MAP
logger = logging.getLogger(__name__)
@dataclass
class SPDDevice:
    '''Informacoes de um dispositivo SPD detectado.
Campos: port, name, hwid, vid, pid, description, mode, mode_label.
- port         : COM (ex: "COM16")
- name         : descricao original do driver (ex: "SPRD U2S Diag (COM16)")
- hwid         : hardware id do pyserial (ex: "USB VID:PID=1782:4D00 ...")
- vid, pid     : Vendor/Product ID em int
- description  : port_info.description (redundante com name mas util p/ debug)
- mode         : codigo do modo (SPD_DOWNLOAD, SPRD3, SPRD4, SPRD_DIAG, UNKNOWN)
- mode_label   : rotulo humano curto (ex: "Download", "SPRD3", "Diag (modem)",
                 "Unknown 0xABCD"). Usar para UI.
'''
    port: str
    name: str = ''
    hwid: str = ''
    vid: int = 0
    pid: int = 0
    description: str = ''
    mode: str = 'UNKNOWN'
    mode_label: str = ''
    @property
    def is_spd_download(self) -> bool:
        '''True somente para PID 0x4D00 (unico compativel com spd_dump).'''
        return self.mode == 'SPD_DOWNLOAD'
class DeviceDetector:
    '''Detecta dispositivos SPD em Modo SPD (FDL).
    Simplificacao: no Python usamos serial.tools.list_ports que ja faz
    o equivalente das queries WMI do C#, listando todas as portas COM
    com informacoes de VID/PID e descricao.
    '''
    SPRD_KEYWORDS = ('SPRD', 'SPREADTRUM', 'UNISOC')
    def __init__(self):
        self._last_devices = []
        self._last_logged_snapshot = set()
    def scan(self) -> List[SPDDevice]:
        '''Escaneia todas as portas COM em busca de dispositivos SPD.
Ordem de matching (mais especifica primeiro):
  1. VID exato Unisoc (0x1782) ÔÇö filtro autoritativo
  2. Palavra-chave "SPRD"/"SPREADTRUM"/"UNISOC" no
     description/name/hwid ÔÇö fallback para drivers atipicos
Log em INFO SOMENTE quando o estado do conjunto de dispositivos
muda entre scans (dispositivo apareceu ou sumiu). Scans que
confirmam o mesmo dispositivo caem em DEBUG. Isso elimina o
log spam observado em producao (Bug 6).
Returns:
    Lista de SPDDevice encontrados (deduplicada por porta).
'''
        devices = []
        seen_ports = set()
        for port_info in serial.tools.list_ports.comports():
            if port_info.device in seen_ports:
                continue
            matched = False
            if port_info.vid == SPRD_VID:
                matched = True
            if not matched:
                blob = ' '.join((port_info.description or '', port_info.name or '', port_info.hwid or '')).upper()
                if any((kw in blob for kw in self.SPRD_KEYWORDS)):
                    matched = True
            if matched:
                devices.append(self._port_to_device(port_info))
                seen_ports.add(port_info.device)
        self._last_devices = devices
        self._log_state_transition(devices)
        return devices
    def find_one(self) -> Optional[SPDDevice]:
        '''Retorna o primeiro dispositivo SPD encontrado, ou None.
        Prioriza SPD_DOWNLOAD (0x4D00) sobre outros modos, ja que e o
        unico compativel com spd_dump para operacoes de flash. Se nao
        houver Download, retorna o primeiro encontrado (util para UI
        informar "aparelho em modo diag ÔÇö coloque em download").
        '''
        devices = self.scan()
        if not devices:
            return
        for d in devices:
            if d.is_spd_download:
                return d
        return devices[0]
    def wait_for_device(self, timeout: float=60.0, poll_interval: float=0.5, on_waiting=None) -> Optional[SPDDevice]:
        '''Aguarda ate um dispositivo SPD aparecer.
Args:
    timeout: tempo maximo de espera em segundos.
    poll_interval: intervalo entre scans em segundos.
    on_waiting: callback opcional chamado a cada iteracao (GUI).
Returns:
    SPDDevice se encontrado, None se timeout.
'''
        logger.info(f'Aguardando dispositivo SPD (timeout={timeout}s)...')
        start = time.time()
        while time.time() - start < timeout:
            device = self.find_one()
            if device:
                logger.info(f'Dispositivo encontrado: {device.port} ({device.mode_label})')
                return device
            if on_waiting:
                elapsed = time.time() - start
                on_waiting(elapsed, timeout)
            time.sleep(poll_interval)
        logger.warning('Timeout aguardando dispositivo SPD')
    @staticmethod
    def _resolve_mode(vid: int, pid: int) -> Tuple[str, str]:
        """Resolve (mode_code, mode_label) a partir de VID/PID.
        Nao-Unisoc ÔåÆ ('UNKNOWN', ''). Isso e defensivo: teoricamente o
        scan ja filtra por VID/keyword, mas se algum dia entrar aqui um
        VID diferente por causa de fallback de keyword, devolvemos algo
        neutro em vez de fingir que e Unisoc.
        """
        if vid != SPRD_VID:
            return ('UNKNOWN', '')
        entry = SPRD_PID_MAP.get(pid)
        if entry:
            return entry
        return 'UNKNOWN', f'Unknown 0x{pid:04X}'
    def _port_to_device(self, port_info) -> SPDDevice:
        '''Converte ListPortInfo do pyserial para SPDDevice com modo.'''
        vid = port_info.vid or 0
        pid = port_info.pid or 0
        mode, mode_label = self._resolve_mode(vid, pid)
        return SPDDevice(port=port_info.device, name=port_info.description or port_info.name or '', hwid=port_info.hwid or '', vid=vid, pid=pid, description=port_info.description or '', mode=mode, mode_label=mode_label)
    def _log_state_transition(self, devices: List[SPDDevice]) -> None:
        '''Loga em INFO apenas em transicao de estado (novo/sumiu).
        Snapshot = frozenset de (port, mode). Se mudou desde o ultimo
        scan, gera log de INFO com o diff. Caso contrario, cai em DEBUG.
        Isso resolve o Bug 6 (log spam com dezenas de linhas identicas
        `SPD detectado: COM16 ÔÇö SPRD U2S Diag`).
        '''
        snapshot = {(d.port, d.mode) for d in devices}
        if snapshot == self._last_logged_snapshot:
            if devices:
                logger.debug('SPD scan (estavel): %d dispositivo(s)', len(devices))
                return
            logger.debug('SPD scan (estavel): nenhum dispositivo')
            return
        added = snapshot - self._last_logged_snapshot
        removed = self._last_logged_snapshot - snapshot
        for port, _mode in sorted(removed):
            logger.info('SPD removido: %s', port)
        for dev in devices:
            if (dev.port, dev.mode) not in added:
                continue
            label = dev.mode_label or dev.name or '?'
            logger.info('SPD detectado: %s ÔÇö %s (VID=0x%04X PID=0x%04X)', dev.port, label, dev.vid, dev.pid)
        self._last_logged_snapshot = snapshot
    @property
    def last_devices(self) -> List[SPDDevice]:
        '''Retorna resultado do ultimo scan.'''
        return self._last_devices
