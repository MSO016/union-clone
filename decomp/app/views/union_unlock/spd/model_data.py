'''
Containers de configuracao de modelo.
Ver: alan/documentacao/16-08-2026-ARQUITETURA-SPD-INTERNA/01_MAPA_REFERENCIAS_INTERNAS.md
'''
import logging
from dataclasses import dataclass, field
from typing import (Dict, List, Optional)
logger = logging.getLogger(__name__)
@dataclass
class ModelConfig:
    '''Configuracao de um modelo ÔÇö populada em memoria pelo modulo de sync.'''
    brand: str
    model: str
    chipset: str = ''
    fdl1_addr: int = 0
    fdl2_addr: int = 0
    exec_addr: Optional[int] = None
    fdl1_file: str = 'fdl1-sign.bin'
    fdl2_file: str = 'fdl2-sign.bin'
    persist_file: str = ''
    operations: List[str] = field(default_factory=list)
    data_dir: str = ''
class ModelDatabase:
    '''Cache em memoria de modelos organizados por marca.'''
    def __init__(self):
        self._models = {}
    def add_model(self, config: ModelConfig) -> None:
        brand = config.brand.upper()
        if brand not in self._models:
            self._models[brand] = []
        self._models[brand].append(config)
    def get_brands(self) -> List[str]:
        return sorted(self._models.keys())
    def get_models(self, brand: str) -> List[ModelConfig]:
        return self._models.get(brand.upper(), [])
    def find_model(self, brand: str, model: str) -> Optional[ModelConfig]:
        for m in self.get_models(brand):
            if not m.model.upper() == model.upper():
                continue
            return m
