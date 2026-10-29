import logging
import os
import sys
from pathlib import Path
_log = logging.getLogger(__name__)
def _exe_acessivel(path: Path) -> bool:
    try:
        with open(path, 'rb') as f:
            f.read(2)
    except (PermissionError, OSError):
        return False
    return True
def _resolve_engine_dir() -> Path:
    exe = 'ExynosBridgeHost.exe'
    try:
        from app.views.union_unlock.exy.engine.exynos_tools_loader import get_engine_dir, cli_disponivel
        if cli_disponivel():
            p = Path(get_engine_dir())
            if _exe_acessivel(p / exe):
                return p
    except Exception:
        pass
    try:
        from app.utils.path_manager import PathManager
        exy_dir = PathManager.get_exy_dir()
        if exy_dir:
            candidate = Path(exy_dir)
            if (candidate / exe).is_file() and _exe_acessivel(candidate / exe):
                return candidate
    except Exception:
        pass
    if getattr(sys, 'frozen', False):
        base = Path(sys.executable).parent
        candidates = [base / '_internal' / 'app' / 'views' / 'union_unlock' / 'exy', base / 'app' / 'views' / 'union_unlock' / 'exy']
        for c in candidates:
            if not (c / exe).is_file():
                continue
            if not _exe_acessivel(c / exe):
                continue
            return c
        return candidates[0]
    return Path(__file__).resolve().parent.parent
ENGINE_DIR = _resolve_engine_dir()
CLI_EXE = 'ExynosBridgeHost.exe'
CLI_EXE_PATH = ENGINE_DIR / CLI_EXE
try:
    from app.utils._app_cfg import REFS
    CLI_PASSWORD = REFS.EXY_CLI_KEY
except ImportError:
    _log.warning('_app_cfg indisponivel ÔÇö CLI_PASSWORD sera vazio')
    CLI_PASSWORD = ''
EXIT_CODES = {0: 'Sucesso', 1: 'Falha na configuracao', 2: 'Falha ao iniciar componente', 3: 'Falha na comunicacao com o dispositivo', 4: 'Falha ao preparar o dispositivo', 5: 'Cancelado pelo usuario'}
BOOT_TIMEOUT_S = 900
ADB_WAIT_TIMEOUT_S = 120
AT_HANDSHAKE_TIMEOUT_S = 30
SERIAL_BAUDRATE = 115200
ADB_EXE = 'adb.exe'
def get_adb_path() -> Path:
    try:
        from app.utils.path_manager import PathManager
        adb = PathManager.get_adb_path()
        if adb and os.path.isfile(adb):
            return Path(adb)
    except Exception:
        pass
    return Path(ADB_EXE)
