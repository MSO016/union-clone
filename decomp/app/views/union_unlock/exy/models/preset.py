'''Ref: administrativo/documentacao/2026-08-30_exy_modulo.md'''
from dataclasses import dataclass, field
from typing import List
@dataclass
class ExynosPreset:
    '''Ref: administrativo/documentacao/2026-08-30_exy_modulo.md'''
    chipset: str = ''
    base: str = ''
    offset: str = ''
    usb_down_ram_base: str = ''
    cpdn_usb_buf_base: str = ''
    variants: List[str] = field(default_factory=list)
    variant_index: int = 0
    json_path: str = ''
    chipset_nome: str = ''
    dispositivos: str = ''
    @property
    def display_name(self) -> str:
        if self.chipset_nome:
            return self.chipset_nome
        name = self.chipset.replace('exynos', 'Exynos ').replace('W', ' W')
        return name.strip()
    @property
    def config_name(self) -> str:
        '''Ref: administrativo/documentacao/2026-08-30_exy_modulo.md'''
        return self.chipset
    @property
    def selected_variant(self) -> str:
        if self.variants:
            if 0 <= self.variant_index < len(self.variants):
                return self.variants[self.variant_index]
        return ''
    def is_valid(self) -> bool:
        return bool(self.chipset and self.base and self.offset)
