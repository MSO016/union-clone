'''
Configuracao centralizada de paths e constantes do modulo EDL.
TECH UNION SOLUTIONS
Todos os caminhos sao resolvidos via PathManager (fonte unica de verdade).
Fallback local mantido para dev mode (edl/tools/).
'''
import os
from pathlib import Path
_BASE_DIR = Path(__file__).resolve().parent
try:
    from app.utils.path_manager import PathManager
    _pm_tools = PathManager.get_unlock_tools_dir()
    _pm_img = PathManager.get_unlock_img_dir()
    _pm_edl_v2 = PathManager.get_edl_v2_dir()
    _pm_img_dir = PathManager.get_unlock_img_dir()
    _pm_logo = os.path.join(_pm_img_dir, 'tech_union_256.png') if _pm_img_dir and os.path.isfile(os.path.join(_pm_img_dir, 'tech_union_256.png')) else None
    _pm_svg = PathManager.get_resource_path(os.path.join('icons_svg', 'seta_down.svg'))
except Exception:
    _pm_tools = None
    _pm_img = None
    _pm_edl_v2 = None
    _pm_logo = None
    _pm_svg = None
_TOOLS_LOCAL = _BASE_DIR / 'tools'
_RAIZ = _BASE_DIR.parents[3]
_TOOLS_PROD = _RAIZ / 'app' / 'views' / 'union_unlock' / 'tools'
if _pm_tools and os.path.isdir(_pm_tools):
    TOOLS_DIR = Path(_pm_tools)
elif _TOOLS_LOCAL.exists():
    TOOLS_DIR = _TOOLS_LOCAL
else:
    TOOLS_DIR = _TOOLS_PROD
IMG_DIR = str(_pm_img) if _pm_img and os.path.isdir(str(_pm_img)) else str(_RAIZ / 'app' / 'views' / 'union_unlock' / 'img')
if _pm_edl_v2 and os.path.isdir(_pm_edl_v2):
    _EDL_V2 = Path(_pm_edl_v2)
else:
    _EDL_V2 = TOOLS_DIR / 'edl_v2'
EDL_NG = TOOLS_DIR / 'edl-ng.exe'
FRP_EDL = TOOLS_DIR / 'FRP_EDL.exe'
EMMCDL = TOOLS_DIR / 'emmcdl.exe'
QCOMVIEW = TOOLS_DIR / 'qcomview.exe'
if _EDL_V2.exists():
    QSAHARA = _EDL_V2 / 'QSaharaServer.exe'
    FH_LOADER = _EDL_V2 / 'fh_loader.exe'
else:
    QSAHARA = TOOLS_DIR / 'QSaharaServer.exe'
    FH_LOADER = TOOLS_DIR / 'fh_loader.exe'
LOGO_PATH = str(_pm_logo) if _pm_logo and os.path.isfile(str(_pm_logo)) else str(_BASE_DIR.parent / 'img' / 'tech_union_256.png')
SVG_SETA_DOWN = str(_pm_svg) if _pm_svg and os.path.isfile(str(_pm_svg)) else str(_RAIZ / 'app' / 'resources' / 'icons_svg' / 'seta_down.svg')
def tool_path(nome: str) -> str:
    '''Resolve path de ferramenta.'''
    return str(TOOLS_DIR / nome)
def img_path(nome: str) -> str:
    '''Resolve path de imagem na pasta img de producao.'''
    return os.path.join(IMG_DIR, nome)
def verificar_tools() -> bool:
    '''Verifica se as tools minimas estao disponiveis.'''
    return EDL_NG.exists()
