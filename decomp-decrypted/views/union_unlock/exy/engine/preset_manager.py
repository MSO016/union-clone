import json
import logging
import os
import re
from pathlib import Path
from typing import (Dict, List, Optional)
from app.views.union_unlock.exy.models.preset import ExynosPreset
from app.views.union_unlock.exy.engine import _cfg
_log = logging.getLogger(__name__)
def _sort_key(name: str) -> tuple:
    nums = re.findall('\\d+', name)
    if nums:
        return 0, int(nums[0]), name
    return 1, 0, name
class PresetManager:
    def __init__(self, presets_dir: Path=None):
        self._dir = presets_dir or Path(__file__).parent.parent / 'data' / 'presets'
        self._cache = {}
        self._sync = None
        try:
            from app.views.union_unlock.exy.engine.exynos_sync import get_sync
            self._sync = get_sync()
            return
        except Exception:
            _log.debug('ExynosSync indisponivel ÔÇö usando presets locais')
    @property
    def presets_dir(self) -> Path:
        return self._dir
    @property
    def usando_sync(self) -> bool:
        return self._sync is not None and self._sync.total_presets() > 0
    def sincronizar(self) -> bool:
        if not self._sync:
            return False
        if self._sync.pode_sincronizar():
            return self._sync.sincronizar()
        return True
    def list_chipsets(self) -> List[str]:
        if self._sync:
            dados = self._sync.listar_chipsets()
            if dados:
                return sorted([c['chipset_key'] for c in dados], key=_sort_key)
        if not self._dir.is_dir():
            _log.warning('Presets nao encontrados: sync vazio e %s inexistente', self._dir)
            return []
        chipsets = set()
        for f in self._dir.glob('*.json'):
            chipsets.add(f.stem)
        return sorted(chipsets, key=_sort_key)
    def load_preset(self, chipset: str) -> Optional[ExynosPreset]:
        if chipset in self._cache:
            return self._cache[chipset]
        data = None
        source = None
        if self._sync:
            data = self._sync.obter_preset_json(chipset)
            if data:
                source = 'sync'
        if not data:
            json_path = self._dir / f'{chipset}.json'
            if json_path.is_file():
                try:
                    with open(json_path, 'r', encoding='utf-8') as fh:
                        data = json.load(fh)
                    source = 'local'
                except (json.JSONDecodeError, OSError) as exc:
                    _log.error('Erro ao carregar preset local %s: %s', chipset, exc)
        if not data:
            _log.error('Preset %s nao encontrado (sync=%s, local=%s)', chipset, bool(self._sync), self._dir.is_dir())
            return
        info = None
        if self._sync and source == 'sync':
            info = self._sync.obter_preset_completo(chipset)
        preset = ExynosPreset(chipset=chipset, base=data.get('base', ''), offset=data.get('offset', ''), usb_down_ram_base=data.get('usbDownRamBase', ''), cpdn_usb_buf_base=data.get('cpdnUsbBufBase', ''), variants=data.get('variants', []), variant_index=data.get('variantIndex', 0), json_path='', chipset_nome=info.get('chipset_nome', '') if info else '', dispositivos=info.get('dispositivos', '') if info else '')
        if not preset.is_valid():
            _log.warning('Preset %s incompleto: base=%s offset=%s', chipset, preset.base, preset.offset)
        self._cache[chipset] = preset
        return preset
    def get_json_path(self, chipset: str) -> Optional[str]:
        preset = self.load_preset(chipset)
        if not preset:
            return
        if self._sync and self._sync.total_presets() > 0:
            data = self._sync.obter_preset_json(chipset)
            if data:
                engine_dir = str(_cfg.ENGINE_DIR)
                json_path = os.path.join(engine_dir, f'{chipset}.json')
                try:
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f)
                except OSError as exc:
                    _log.error('Erro ao gravar preset %s: %s', json_path, exc)
                return json_path
        local = self._dir / f'{chipset}.json'
        if local.is_file():
            return str(local)
    def limpar_preset_temporario(self, chipset: str):
        engine_dir = str(_cfg.ENGINE_DIR)
        json_path = os.path.join(engine_dir, f'{chipset}.json')
        try:
            if os.path.isfile(json_path):
                os.remove(json_path)
                return
        except OSError:
            pass
    def clear_cache(self):
        self._cache.clear()
