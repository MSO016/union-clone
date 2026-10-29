import logging
import os
import subprocess
import time
from typing import (Callable, List, Optional, Tuple)
from app.views.union_unlock.exy.engine import _cfg
_log = logging.getLogger(__name__)
LogCb = Optional[Callable[[str], None]]
def _emit(cb: LogCb, msg: str):
    if cb:
        cb(msg)
def _run_adb(args: List[str], timeout: int=30) -> Tuple[int, str, str]:
    adb = str(_cfg.get_adb_path())
    cmd = [adb] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        _log.error('ADB nao encontrado: %s', adb)
        return (-1, '', 'Ferramenta de conexao nao encontrada')
    except subprocess.TimeoutExpired:
        _log.warning('ADB timeout (%ds): %s', timeout, args)
        return (-2, '', 'Tempo esgotado aguardando dispositivo')
    except Exception as exc:
        _log.error('_run_adb: %s', exc, exc_info=True)
        return (-3, '', 'Erro interno de comunicacao')
def wait_for_device(timeout: int=None, log_cb: LogCb=None, cancel_event=None, initial_delay: float=0) -> bool:
    timeout = timeout or _cfg.ADB_WAIT_TIMEOUT_S
    if initial_delay > 0:
        _emit(log_cb, f'Aguardando boot do dispositivo ({int(initial_delay)}s)...')
        time.sleep(initial_delay)
    start = time.monotonic()
    _emit(log_cb, f'Aguardando dispositivo ADB (max {timeout}s)...')
    while time.monotonic() - start < timeout:
        if cancel_event and cancel_event.is_set():
            _emit(log_cb, 'Cancelado')
            return False
        rc, out, _ = _run_adb(['devices'], timeout=10)
        if rc == 0:
            for line in out.splitlines():
                if '\tdevice' in line or '\trecovery' in line:
                    serial = line.split('\t')[0]
                    state = line.split('\t')[1] if '\t' in line else '?'
                    _emit(log_cb, f'Dispositivo ADB: {serial} [{state}]')
                    return True
                if 'unauthorized' in line:
                    _emit(log_cb, "Dispositivo unauthorized ÔÇö toque 'Permitir depuracao USB' no aparelho")
        elapsed = int(time.monotonic() - start)
        if elapsed % 15 == 0 and elapsed > 0:
            _emit(log_cb, f'Aguardando ADB... ({elapsed}s/{timeout}s)')
        time.sleep(3)
    _emit(log_cb, 'Timeout: nenhum dispositivo ADB detectado')
    return False
def adb_root(log_cb: LogCb=None) -> bool:
    _emit(log_cb, 'Elevando permissoes...')
    rc, out, err = _run_adb(['root'], timeout=15)
    msg = (out + err).strip()
    _log.debug('adb root: %s', msg)
    _emit(log_cb, 'Permissoes elevadas: %s' % ('OK' if 'already' in msg.lower() or rc == 0 else 'aguardando'))
    if rc != 0 and 'cannot' in msg.lower():
        _log.error('adb root falhou: %s', msg)
        return False
    _emit(log_cb, 'Aguardando permissoes (6s)...')
    time.sleep(6)
    return True
def list_partitions(log_cb: LogCb=None) -> List[str]:
    _emit(log_cb, 'Listando particoes...')
    rc, out, err = _run_adb(['shell', 'ls', '-al', '/dev/block/by-name/'], timeout=15)
    if rc != 0:
        _log.error('Erro particoes: %s', err)
        _emit(log_cb, 'Erro ao listar particoes do dispositivo')
        return []
    partitions = []
    for line in out.splitlines():
        line = line.strip()
        if '->' in line:
            parts = line.split('->')
            name_part = parts[0].strip().split()[-1] if parts[0].strip() else ''
            block_part = parts[1].strip() if len(parts) > 1 else ''
            if name_part:
                partitions.append(name_part)
    return partitions
def find_frp_partition(log_cb: LogCb=None) -> Tuple[str, str]:
    _emit(log_cb, 'Buscando particao de protecao...')
    rc, out, err = _run_adb(['shell', 'ls', '-al', '/dev/block/by-name/'], timeout=15)
    if rc != 0 or not out:
        _log.error('Erro particoes FRP: %s', err)
        _emit(log_cb, 'Erro ao listar particoes do dispositivo')
        return ('', '')
    lines = out.splitlines()
    import re
    for target in ('persistent', 'frp'):
        for line in lines:
            if re.search('\\b' + target + '\\b', line):
                block_path = ''
                for word in line.split():
                    word = word.strip()
                    if not word.startswith('/dev/block/'):
                        continue
                    block_path = word
                    break
                if block_path:
                    _emit(log_cb, 'Particao de protecao localizada')
                    return target, block_path
        if target == 'persistent':
            _emit(log_cb, 'Buscando particao alternativa...')
    _emit(log_cb, 'Particao de protecao nao encontrada no dispositivo')
    return ('', '')
_FRP_DEFAULT_SIZE = 524288
_FRP_MAX_SIZE = 2097152
def _generate_frp_payload(block_path: str, log_cb: LogCb=None) -> Tuple[str, int]:
    import tempfile
    partition_size = _FRP_DEFAULT_SIZE
    try:
        rc, out, err = _run_adb(['shell', 'blockdev', '--getsize64', block_path], timeout=10)
        if rc == 0 and out.strip().isdigit():
            parsed = int(out.strip())
            if 0 < parsed <= _FRP_MAX_SIZE:
                partition_size = parsed
    except Exception:
        pass
    tmp = tempfile.NamedTemporaryFile(prefix='~', suffix='.tmp', delete=False, dir=os.environ.get('TEMP', os.environ.get('LOCALAPPDATA', None)))
    tmp.write(b'\x00' * partition_size)
    tmp.close()
    return tmp.name, partition_size
def push_frp(log_cb: LogCb=None, cancel_event=None) -> Tuple[bool, str]:
    _emit(log_cb, 'Preparando limpeza de dados...')
    partition_name, block_path = find_frp_partition(log_cb)
    if not block_path:
        return (False, 'Particao de protecao nao encontrada no dispositivo')
    if cancel_event and cancel_event.is_set():
        return (False, 'Cancelado')
    if not adb_root(log_cb):
        return (False, 'Falha ao elevar permissoes')
    if cancel_event and cancel_event.is_set():
        return (False, 'Cancelado')
    _emit(log_cb, 'Preparando dados de limpeza...')
    tmp_path = None
    try:
        tmp_path, size = _generate_frp_payload(block_path, log_cb)
    except Exception as exc:
        _log.error('Erro ao gerar payload: %s', exc)
        return (False, 'Erro interno. Tente novamente.')
    try:
        _emit(log_cb, 'Gravando dados na particao...')
        rc, out, err = _run_adb(['push', tmp_path, block_path], timeout=30)
        if rc != 0:
            _log.error('push: %s', (out + err).strip())
            _emit(log_cb, 'Erro ao gravar dados no dispositivo')
            if tmp_path:
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
                return (False, 'Erro ao gravar dados no dispositivo')
            return (False, 'Erro ao gravar dados no dispositivo')
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                return (False, 'Erro ao gravar dados no dispositivo')
    try:
        _emit(log_cb, 'Gravacao concluida')
        if cancel_event and cancel_event.is_set():
            if tmp_path:
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
                return (False, 'Cancelado')
            return (False, 'Cancelado')
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                return (False, 'Cancelado')
    try:
        _emit(log_cb, 'Reiniciando dispositivo...')
        rc, out, err = _run_adb(['reboot'], timeout=15)
        if rc != 0:
            _log.warning('reboot: %s', err)
            _emit(log_cb, 'Aviso: reinicializacao pode ter falhado')
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                return (True, 'Protecao removida com sucesso. Dispositivo reiniciando.')
    return (True, 'Protecao removida com sucesso. Dispositivo reiniciando.')
def sync_adb_key(engine_dir: str=None, log_cb: LogCb=None) -> bool:
    if engine_dir is None:
        engine_dir = str(_cfg.ENGINE_DIR)
    user_profile = os.environ.get('USERPROFILE', '')
    user_key_path = os.path.join(user_profile, '.android', 'adbkey.pub')
    exy_keys_path = os.path.join(engine_dir, 'ramdisks', 'adb_keys')
    if not os.path.isfile(user_key_path):
        _emit(log_cb, 'Chave de autenticacao nao encontrada ÔÇö confirme ADB no dispositivo se solicitado')
        return False
    if not os.path.isfile(exy_keys_path):
        _emit(log_cb, 'Diretorio de autenticacao nao encontrado')
        return False
    try:
        with open(user_key_path, 'r', encoding='utf-8', errors='replace') as f:
            user_key = f.read().strip()
        if not user_key:
            return False
        with open(exy_keys_path, 'r', encoding='utf-8', errors='replace') as f:
            existing = f.read()
        prefix = user_key[:40] if len(user_key) >= 40 else user_key
        if prefix in existing:
            _emit(log_cb, 'Autenticacao ja configurada')
            return True
        with open(exy_keys_path, 'a', encoding='utf-8') as f:
            f.write('\n' + user_key)
        _emit(log_cb, 'Autenticacao configurada')
    except Exception as exc:
        _log.warning('sync_adb_key: %s', exc)
        return False
    return True
def read_adb_device_info(log_cb: LogCb=None) -> dict:
    info = {}
    props = {'ro.product.model': 'Modelo', 'ro.product.brand': 'Fabricante', 'ro.build.version.release': 'Android', 'ro.build.version.security_patch': 'Patch seguranca', 'ro.build.display.id': 'Build', 'ro.serialno': 'Serial'}
    for prop, label in props.items():
        try:
            rc, out, _ = _run_adb(['shell', 'getprop', prop], timeout=5)
            val = out.strip() if rc == 0 else ''
            if val:
                info[prop] = val
                _emit(log_cb, f'{label}: {val}')
        except Exception:
            continue
    return info
def reboot_device(log_cb: LogCb=None) -> bool:
    _emit(log_cb, 'Reiniciando dispositivo...')
    rc, out, err = _run_adb(['reboot'], timeout=15)
    if rc == 0:
        _emit(log_cb, 'Comando de reboot enviado')
        return True
    _log.error('reboot: %s', err)
    _emit(log_cb, 'Erro ao reiniciar dispositivo')
    return False
