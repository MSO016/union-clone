from dataclasses import dataclass, field
@dataclass
class DeviceInfo:
    model: str = ''
    com_port: str = ''
    usb_port: str = ''
    unique_id: str = ''
    build: str = ''
    vendor: str = ''
    firmware_ver: str = ''
    capacity: str = ''
    product: str = ''
    sales_code: str = ''
    provision: str = ''
    did: str = ''
    tmu_temp: str = ''
    mode: str = 'unknown'
    extra: dict = field(default_factory=dict)
    @property
    def is_download_mode(self) -> bool:
        return self.mode == 'download'
    @property
    def is_adb_mode(self) -> bool:
        return self.mode == 'adb'
    @property
    def display_name(self) -> str:
        parts = []
        if self.model:
            parts.append(self.model)
        if self.mode and self.mode != 'unknown':
            parts.append(f'[{self.mode.upper()}]')
        if parts:
            return ' '.join(parts)
        return 'Nenhum dispositivo'
    def reset(self):
        for fld in self.__dataclass_fields__:
            if fld == 'extra':
                self.extra = {}
            elif fld == 'mode':
                self.mode = 'unknown'
            else:
                setattr(self, fld, '')
