import logging
import os
import shutil
import tempfile
import time
from typing import (Callable, Dict, List, Optional, Tuple)
try:
    from app.views.union_unlock.edl import firehose_ops as fhops
    from app.views.union_unlock.edl.gpt_parser import parse_gpt_file
except ImportError:
    import firehose_ops as fhops
    from gpt_parser import parse_gpt_file
_logger = logging.getLogger('micloud_edl')
MODEM_SEARCH = b'CARDAPP'
MODEM_REPLACE = b'FARDAPP'
PERSIST_SEARCH = b'fdsd'
PERSIST_REPLACE = b'ftst'
SEARCH_PATTERN = MODEM_SEARCH
REPLACE_PATTERN = MODEM_REPLACE
MODEM_PARTITION_NAMES = ('modem', 'modem_a', 'modem_b', 'NON-HLOS')
PERSIST_PARTITION_NAMES = ('persist', 'persistbak')
ERASE_PARTITION_NAMES = ('frp', 'config')
_MEM_MANUFACTURERS = {17: 'Toshiba/Kioxia', 19: 'Micron', 21: 'Samsung', 69: 'SanDisk/WD', 144: 'SK Hynix', 429: 'SK Hynix', 2715: 'YMTC'}
def _log(msg: str):
    _logger.debug(msg)
def _backup_dir() -> str:
    try:
        if os.name == 'nt':
            import ctypes.wintypes
            buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf)
            docs = buf.value
        else:
            docs = os.path.expanduser('~/Documents')
    except Exception:
        docs = os.path.join(os.path.expanduser('~'), 'Documents')
    bkp = os.path.join(docs, 'UNION_Backups')
    os.makedirs(bkp, exist_ok=True)
    return bkp
def _patch_modem_data(data: bytes) -> Tuple[bytes, int]:
    count = data.count(MODEM_SEARCH)
    if count == 0:
        return data, 0
    patched = data.replace(MODEM_SEARCH, MODEM_REPLACE)
    return patched, count
def _patch_persist_data(data: bytes) -> Tuple[bytes, int]:
    count = data.count(PERSIST_SEARCH)
    if count == 0:
        return data, 0
    patched = data.replace(PERSIST_SEARCH, PERSIST_REPLACE)
    return patched, count
def _encontrar_modem(todas_particoes: List[Dict]) -> List[Dict]:
    encontrados = []
    for nome_alvo in MODEM_PARTITION_NAMES:
        for p in todas_particoes:
            if p.get('name', '').lower() == nome_alvo.lower():
                encontrados.append(p)
    return encontrados
def _encontrar_particoes(todas: List[Dict], nomes: tuple) -> List[Dict]:
    encontrados = []
    for nome in nomes:
        for p in todas:
            if p.get('name', '').lower() == nome.lower():
                encontrados.append(p)
    return encontrados
def _erase_particao(porta: str, mem_type: str, part: Dict, sector: int, log_cb) -> bool:
    name = part.get('name', '?')
    lun = part.get('lun', 0)
    _log(f'Apagando {name} LUN {lun}')
    ok, msg = fhops.erase_partition(porta, mem_type, part, sector, lun=lun, log_cb=log_cb)
    if not ok:
        _log(f'Erase {name} falhou: {msg} (continuando)')
    return ok
def _read_patch_write(porta: str, mem_type: str, part: Dict, sector: int, patch_fn, search_pattern: bytes, tmp_dir: str, bkp_dir: str, ts: str, log_cb) -> Tuple[bool, int]:
    name = part.get('name', '?')
    lun = part.get('lun', 0)
    num_sectors = part.get('num_sectors', 0)
    size_mb = num_sectors * sector / 1048576
    _log(f'Lendo {name} LUN {lun} ({size_mb:.1f} MB)')
    read_path = os.path.join(tmp_dir, f'{name}_original.bin')
    ok_read, read_msg = fhops.read_partition(porta, mem_type, part, sector, output_path=read_path, lun=lun, log_cb=log_cb)
    if not ok_read:
        _log(f'read_partition {name} falhou: {read_msg}, tentando alternativo')
        ok_read, read_msg = fhops.read_partition_via_sendxml(porta, mem_type, part, sector, output_path=read_path, lun=lun, log_cb=log_cb)
    if not ok_read or not os.path.exists(read_path):
        _log(f'Leitura {name} falhou: {read_msg}')
        return (False, 0)
    file_size = os.path.getsize(read_path)
    if file_size == 0:
        _log(f'{name}: arquivo vazio')
        return (False, 0)
    with open(read_path, 'rb') as f:
        original = f.read()
    if search_pattern not in original:
        _log(f'{name}: padrao nao encontrado (ok, pulando)')
        return (True, 0)
    backup_path = os.path.join(bkp_dir, f'backup_{name}_{ts}.bin')
    try:
        shutil.copy2(read_path, backup_path)
        _log(f'Backup {name}: {backup_path}')
    except Exception as e:
        _logger.error('Backup %s falhou: %s', name, e)
        return (False, 0)
    patched, count = patch_fn(original)
    if len(patched) != len(original):
        _logger.error('Integridade %s: orig=%d mod=%d', name, len(original), len(patched))
        return (False, 0)
    patched_path = os.path.join(tmp_dir, f'{name}_modified.bin')
    with open(patched_path, 'wb') as f:
        f.write(patched)
    _log(f'Escrevendo {name} ({count} ocorrencia(s))...')
    ok_write, write_msg = fhops.write_partition(porta, mem_type, part, sector, image_path=patched_path, lun=lun, log_cb=log_cb)
    if not ok_write:
        _logger.error('Escrita %s falhou: %s', name, write_msg)
        return False, count
    _log(f'{name} concluido ({count} ocorrencia(s))')
    return True, count
def executar_micloud_edl(loader_path: str, memoria: str, log_cb: Optional[Callable[[str], None]]=None, progress_cb: Optional[Callable[[int], None]]=None, auth_manufacturer: str='xiaomi') -> Tuple[bool, str, Dict]:
    def _lcb(msg: str):
        _log(msg)
        if log_cb:
            log_cb(msg)
    def _pcb(val: int):
        if progress_cb:
            progress_cb(val)
    device_data = {}
    t_inicio = time.time()
    tmp_dir = None
    try:
        _pcb(3)
        _lcb('Conectando ao dispositivo...')
        porta = fhops.detectar_porta_com()
        if not porta:
            if tmp_dir:
                if os.path.isdir(tmp_dir):
                    try:
                        shutil.rmtree(tmp_dir, ignore_errors=True)
                    except Exception:
                        return
                    return False, 'Dispositivo nao encontrado.\nConecte em modo EDL e tente novamente.', device_data
                return
            return
    except Exception as e:
        _logger.error('executar_micloud_edl: %s', e, exc_info=True)
    try:
        _log(f'Porta EDL: {porta}')
        device_data['porta'] = porta
        _pcb(6)
        if not os.path.exists(loader_path):
            if tmp_dir:
                if os.path.isdir(tmp_dir):
                    try:
                        shutil.rmtree(tmp_dir, ignore_errors=True)
                    except Exception:
                        return
                    return False, 'Componente nao disponivel.\nAtualize o sistema e tente novamente.', device_data
                return
            return
    except Exception as e:
        _logger.error('executar_micloud_edl: %s', e, exc_info=True)
    try:
        tamanho_kb = os.path.getsize(loader_path) // 1024
        _lcb(f'Enviando programador [{tamanho_kb} KB]...')
        ok, msg = fhops.upload_loader(porta, loader_path, log_cb=log_cb)
        if not ok:
            _logger.error('Sahara falhou: %s', msg)
            if tmp_dir:
                if os.path.isdir(tmp_dir):
                    try:
                        shutil.rmtree(tmp_dir, ignore_errors=True)
                    except Exception:
                        return
                    return False, 'Falha na comunicacao com o dispositivo.\n\nReconecte em modo EDL e tente novamente.', device_data
                return
            return
    except Exception as e:
        _logger.error('executar_micloud_edl: %s', e, exc_info=True)
    try:
        _lcb('  Programador carregado')
        _pcb(12)
        _lcb('Verificando dispositivo...')
        auth_ok, _ = fhops.firehose_auth(porta, auth_manufacturer, log_cb=log_cb)
        device_data['auth_sucesso'] = auth_ok
        _lcb('  Verificacao concluida')
        _pcb(16)
        _lcb('Analisando dispositivo...')
        mem_type, sector, num_luns, storage_info = fhops.detect_storage_auto(porta, log_cb=log_cb, memory_hint=memoria)
        device_data['mem_type'] = mem_type
        device_data['sector_size'] = sector
        device_data['num_luns'] = num_luns
        _log(f'Storage: {mem_type} sector={sector} luns={num_luns}')
        _pcb(20)
        _lcb('Lendo informacoes do aparelho...')
        todas_particoes = []
        if mem_type == 'ufs':
            gpt_results = fhops.get_all_gpt_ufs(porta, num_luns, log_cb=log_cb)
            for lun, gpt_path in gpt_results:
                gpt_data = parse_gpt_file(gpt_path, sector)
                if gpt_data.get('error'):
                    continue
                for p in gpt_data.get('partitions', []):
                    p['lun'] = lun
                todas_particoes.extend(gpt_data.get('partitions', []))
        else:
            ok_gpt, gpt_path = fhops.get_gpt(porta, mem_type, 0, log_cb=log_cb)
            if ok_gpt and gpt_path:
                gpt_data = parse_gpt_file(gpt_path, sector)
                if not gpt_data.get('error'):
                    for p in gpt_data.get('partitions', []):
                        p['lun'] = 0
                    todas_particoes.extend(gpt_data.get('partitions', []))
        total_parts = len(todas_particoes)
        device_data['total_particoes'] = total_parts
        _log(f'{total_parts} particoes encontradas')
        if total_parts == 0:
            if tmp_dir:
                if os.path.isdir(tmp_dir):
                    try:
                        shutil.rmtree(tmp_dir, ignore_errors=True)
                    except Exception:
                        return
                    return False, 'Nao foi possivel ler o dispositivo.\n\nReconecte em modo EDL e tente novamente.', device_data
                return
            return
    except Exception as e:
        _logger.error('executar_micloud_edl: %s', e, exc_info=True)
    try:
        modems = _encontrar_modem(todas_particoes)
        persists = _encontrar_particoes(todas_particoes, PERSIST_PARTITION_NAMES)
        erases = _encontrar_particoes(todas_particoes, ERASE_PARTITION_NAMES)
    except Exception as e:
        _logger.error('executar_micloud_edl: %s', e, exc_info=True)
    try:
        _log(f'Modem: {[m['name'] for m in modems]}')
    except Exception as e:
        _logger.error('executar_micloud_edl: %s', e, exc_info=True)
    try:
        _log(f'Persist: {[p['name'] for p in persists]}')
    except Exception as e:
        _logger.error('executar_micloud_edl: %s', e, exc_info=True)
    try:
        _log(f'Erase: {[e['name'] for e in erases]}')
        if not modems:
            _log(f'Modem nao encontrado. Parts: {[p.get('name') for p in todas_particoes[:20]]}')
            if tmp_dir:
                if os.path.isdir(tmp_dir):
                    try:
                        shutil.rmtree(tmp_dir, ignore_errors=True)
                    except Exception:
                        return
                    return False, 'Este modelo nao e compativel\ncom esta funcionalidade.', device_data
                return
            return
    except Exception as e:
        _logger.error('executar_micloud_edl: %s', e, exc_info=True)
    try:
        tmp_dir = tempfile.mkdtemp(prefix='micloud_')
        bkp_dir = _backup_dir()
        ts = time.strftime('%Y%m%d_%H%M%S')
        _pcb(28)
        _lcb('Preparando dispositivo...')
        for erase_part in erases:
            ename = erase_part.get('name', '')
            _log(f'Apagando {ename}...')
            _erase_particao(porta, mem_type, erase_part, sector, log_cb=log_cb)
            device_data[f'{ename}_erased'] = True
        _pcb(35)
        _lcb('Processando... aguarde')
        _lcb('  Isso pode levar alguns minutos...')
        total_modem_patches = 0
        for modem_part in modems:
            mname = modem_part.get('name', '')
            msize_mb = modem_part.get('num_sectors', 0) * sector / 1048576
            _log(f'Processando {mname} ({msize_mb:.0f} MB)...')
            ok_m, count_m = _read_patch_write(porta, mem_type, modem_part, sector, _patch_modem_data, MODEM_SEARCH, tmp_dir, bkp_dir, ts, log_cb=log_cb)
            if ok_m and count_m > 0:
                total_modem_patches += count_m
                device_data[f'{mname}_patches'] = count_m
            else:
                if ok_m:
                    continue
                _logger.warning('Falha no processamento de %s', mname)
        device_data['total_modem_patches'] = total_modem_patches
        if total_modem_patches == 0:
            _log('Nenhum padrao encontrado em nenhuma particao modem')
            if tmp_dir:
                if os.path.isdir(tmp_dir):
                    try:
                        shutil.rmtree(tmp_dir, ignore_errors=True)
                    except Exception:
                        return
                    return False, 'Este modelo nao e compativel com esta funcionalidade.\n\nPossiveis causas:\n  - A conta ja foi removida anteriormente\n  - O modelo usa outro metodo de verificacao\n\nNenhuma alteracao foi feita no dispositivo.', device_data
                return
            return
    except Exception as e:
        _logger.error('executar_micloud_edl: %s', e, exc_info=True)
    try:
        _pcb(75)
        _lcb('Finalizando operacao...')
        total_persist_patches = 0
        for persist_part in persists:
            pname = persist_part.get('name', '')
            psize_mb = persist_part.get('num_sectors', 0) * sector / 1048576
            _log(f'Processando {pname} ({psize_mb:.1f} MB)...')
            ok_p, count_p = _read_patch_write(porta, mem_type, persist_part, sector, _patch_persist_data, PERSIST_SEARCH, tmp_dir, bkp_dir, ts, log_cb=log_cb)
            if ok_p and count_p > 0:
                total_persist_patches += count_p
                device_data[f'{pname}_patches'] = count_p
            else:
                if ok_p:
                    continue
                _logger.warning('Falha no processamento de %s', pname)
        device_data['total_persist_patches'] = total_persist_patches
        _pcb(90)
        _lcb('Reiniciando dispositivo...')
        fhops.reset_device(porta, mem_type, log_cb=log_cb)
        _pcb(100)
        tempo = time.time() - t_inicio
        device_data['tempo_total'] = round(tempo, 1)
        _lcb('')
        _lcb('OPERACAO CONCLUIDA COM SUCESSO!')
        _lcb('')
        _lcb(f'  Tempo total: {tempo:.1f} segundos')
        _lcb('')
        _lcb('  1. Aguarde o aparelho reiniciar')
        _lcb('  2. A conta Mi Cloud sera desativada')
        _lcb('  3. Configure normalmente')
    except Exception as e:
        _logger.error('executar_micloud_edl: %s', e, exc_info=True)
    if tmp_dir:
        if os.path.isdir(tmp_dir):
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                return
            return True, 'Mi Cloud removido com sucesso!', device_data
# WARNING: Decompyle incomplete
