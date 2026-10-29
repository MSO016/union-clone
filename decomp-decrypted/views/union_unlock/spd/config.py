import os
from pathlib import Path
_BASE_DIR = Path(__file__).resolve().parent
try:
    from app.utils.path_manager import PathManager
    _pm_tools = PathManager.get_unlock_tools_dir()
    _pm_img = PathManager.get_unlock_img_dir()
    _pm_svg = PathManager.get_resource_path(os.path.join('icons_svg', 'seta_down.svg'))
except Exception:
    _pm_tools = None
    _pm_img = None
    _pm_svg = None
_RAIZ = _BASE_DIR.parents[3]
_TOOLS_PROD = _RAIZ / 'app' / 'views' / 'union_unlock' / 'tools'
_TOOLS_DEV_PILOTO = _RAIZ / 'Estudos-2026' / 'desenvolvimento' / 'UNION 1.3.4' / 'union_unlockv2' / 'spd' / 'bin'
if _pm_tools and os.path.isdir(_pm_tools):
    TOOLS_DIR = Path(_pm_tools)
elif _TOOLS_PROD.exists():
    TOOLS_DIR = _TOOLS_PROD
elif _TOOLS_DEV_PILOTO.exists():
    TOOLS_DIR = _TOOLS_DEV_PILOTO
else:
    TOOLS_DIR = _TOOLS_PROD
IMG_DIR = str(_pm_img) if _pm_img and os.path.isdir(str(_pm_img)) else str(_RAIZ / 'app' / 'views' / 'union_unlock' / 'img')
SVG_SETA_DOWN = str(_pm_svg) if _pm_svg and os.path.isfile(str(_pm_svg)) else str(_RAIZ / 'app' / 'resources' / 'icons_svg' / 'seta_down.svg')
SPD_DUMP = TOOLS_DIR / 'spd_dump.exe'
CHANNEL9_DLL = TOOLS_DIR / 'Channel9.dll'
CHANNEL_INI = TOOLS_DIR / 'Channel.ini'
def tool_path(nome: str) -> str:
    return str(TOOLS_DIR / nome)
def img_path(nome: str) -> str:
    return os.path.join(IMG_DIR, nome)
def verificar_tools() -> bool:
    return SPD_DUMP.exists()
SPD_DUMP_PATH = str(SPD_DUMP) if SPD_DUMP.exists() else ''
BIN_DIR = str(TOOLS_DIR)
