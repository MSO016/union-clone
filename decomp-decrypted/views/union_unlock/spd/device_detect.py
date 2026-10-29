import logging
import time
from dataclasses import dataclass
from typing import (List, Optional, Tuple)
import serial.tools.list_ports
from .constants import SPRD_VID, SPRD_PID_MAP
logger = logging.getLogger(__name__)
@dataclass
class SPDDevice:
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
        return self.mode == 'SPD_DOWNLOAD'
class DeviceDetector:
    SPRD_KEYWORDS = ('SPRD', 'SPREADTRUM', 'UNISOC')
    def __init__(self):
        self._last_devices = []
        self._last_logged_snapshot = set()
    def scan(self) -> List[SPDDevice]:
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
        devices = self.scan()
        if not devices:
            return
        for d in devices:
            if d.is_spd_download:
                return d
        return devices[0]
    def wait_for_device(self, timeout: float=60.0, poll_interval: float=0.5, on_waiting=None) -> Optional[SPDDevice]:
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
        if vid != SPRD_VID:
            return ('UNKNOWN', '')
        entry = SPRD_PID_MAP.get(pid)
        if entry:
            return entry
        return 'UNKNOWN', f'Unknown 0x{pid:04X}'
    def _port_to_device(self, port_info) -> SPDDevice:
        vid = port_info.vid or 0
        pid = port_info.pid or 0
        mode, mode_label = self._resolve_mode(vid, pid)
        return SPDDevice(port=port_info.device, name=port_info.description or port_info.name or '', hwid=port_info.hwid or '', vid=vid, pid=pid, description=port_info.description or '', mode=mode, mode_label=mode_label)
    def _log_state_transition(self, devices: List[SPDDevice]) -> None:
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
        return self._last_devices
