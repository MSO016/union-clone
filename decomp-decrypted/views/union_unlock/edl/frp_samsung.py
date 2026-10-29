import logging
import os
import time
from typing import (Callable, Dict, List, Optional, Tuple)
try:
    from app.views.union_unlock.edl import firehose_ops as fhops
    from app.views.union_unlock.edl.gpt_parser import parse_gpt_file, is_critical
except ImportError:
    import firehose_ops as fhops
    from gpt_parser import parse_gpt_file, is_critical
_logger = logging.getLogger('frp_samsung')
def _log(msg: str):
    _logger.debug(msg)
_MEM_MANUFACTURERS = {17: 'Toshiba/Kioxia', 19: 'Micron', 21: 'Samsung', 69: 'SanDisk/WD', 144: 'SK Hynix', 429: 'SK Hynix', 2715: 'YMTC'}
PARTICOES_SEGURAS = frozenset({'frp', 'config', 'persist', 'userdata', 'persistent'})
PARTICOES_PROIBIDAS = frozenset({'tz', 'abl', 'aop', 'cdt', 'ddr', 'fsc', 'fsg', 'hyp', 'rpm', 'ssd', 'xbl', 'tz_a', 'tz_b', 'abl_a', 'abl_b', 'aop_a', 'aop_b', 'hyp_a', 'hyp_b', 'modem', 'rpm_a', 'rpm_b', 'xbl_a', 'xbl_b', 'cmnlib', 'devcfg', 'modem_a', 'modem_b', 'cmnlib64', 'devcfg_a', 'devcfg_b', 'keystore', 'modemst1', 'modemst2', 'keymaster', 'xbl_config', 'keymaster_a', 'keymaster_b', 'NON-HLOS'})
def _validar_particao(part_name: str, todas_particoes: List[Dict]) -> Tuple[bool, str, Optional[Dict]]:
    lower = part_name.lower()
    if lower in PARTICOES_PROIBIDAS:
        return False, f"Particao '{part_name}' e PROIBIDA ÔÇö risco de brick", None
    if lower not in PARTICOES_SEGURAS:
        return False, f"Particao '{part_name}' nao esta na lista de seguras", None
    matches = [p for p in todas_particoes if p['name'].lower() == lower]
    if not matches:
        return False, f"Particao '{part_name}' nao encontrada no dispositivo", None
    if len(matches) > 1:
        return False, f"Multiplas particoes '{part_name}' encontradas ({len(matches)})", None
    part = matches[0]
    if part.get('start_lba', 0) == 0:
        return False, f"Particao '{part_name}' com setor inicial invalido", None
    if part.get('num_sectors', 0) == 0:
        return False, f"Particao '{part_name}' com tamanho zero", None
    return True, 'OK', part
def _smart_erase_partition(porta: str, mem_type: str, part_info: Dict, sector_size: int, log_cb: Optional[Callable[[str], None]]=None, progress_cb: Optional[Callable[[int], None]]=None) -> Tuple[bool, str]:
    name = part_info.get('name', 'unknown')
    lun = part_info.get('lun', 0)
    num_sectors = part_info.get('num_sectors', 0)
    if num_sectors > 20480:
        _log(f'Particao {name} grande ({num_sectors} setores) ÔÇö tentando erase direto')
        if log_cb:
            log_cb(f'Apagando {name.upper()}...')
        ok_erase, msg_erase = fhops.erase_partition(porta, mem_type, part_info, sector_size, lun=lun, log_cb=log_cb)
        if ok_erase:
            _log(f'{name} apagada via erase')
            return True, f'{name} apagada com sucesso (erase)'
        _log(f'Erase falhou para {name}: {msg_erase}')
    _log(f'Tentando gravar zeros em {name}')
    if log_cb:
        log_cb(f'Zerando {name.upper()} (program)...')
    ok_prog, msg_prog = fhops.program_partition(porta, mem_type, part_info, sector_size, lun=lun, log_cb=log_cb)
    if ok_prog:
        _log(f'{name} zerada via program')
        return True, f'{name} zerada com sucesso (program)'
    if msg_prog != 'NAK_PROGRAM':
        _log(f'Program falhou para {name}: {msg_prog}')
    _log(f'Ativando SMART mode para {name}')
    if log_cb:
        log_cb(f'Modo alternativo: zerando {name.upper()}...')
    ok_patch, msg_patch = fhops.patch_partition(porta, mem_type, part_info, sector_size, lun=lun, max_sectors=4, log_cb=log_cb, progress_cb=progress_cb, full_zero=False)
    if ok_patch:
        _log(f'{name} zerada via SMART mode')
        return True, f'{name} zerada com sucesso (SMART mode)'
    _log(f'SMART mode falhou para {name}: {msg_patch}')
    return False, f'Falha ao zerar {name}: {msg_patch}'
def executar_frp_samsung(loader_path: str, memoria: str, particoes_alvo: Optional[List[str]]=None, log_cb: Optional[Callable[[str], None]]=None, progress_cb: Optional[Callable[[int], None]]=None) -> Tuple[bool, str, Dict]:
    if particoes_alvo is None:
        particoes_alvo = ['persistent']
    def _lcb(msg: str):
        _log(msg)
        if log_cb:
            log_cb(msg)
    def _pcb(val: int):
        if progress_cb:
            progress_cb(val)
    device_data = {}
    t_inicio = time.time()
    _pcb(5)
    _lcb('Conectando ao dispositivo Samsung...')
    porta = fhops.detectar_porta_com()
    if not porta:
        return False, 'Dispositivo EDL nao encontrado.\nConecte em modo EDL e tente novamente.', device_data
    _lcb(f'  Porta EDL : {porta}')
    device_data['porta'] = porta
    _pcb(15)
    if not os.path.exists(loader_path):
        return False, 'Arquivo de suporte nao encontrado.', device_data
    tamanho_kb = os.path.getsize(loader_path) // 1024
    _lcb(f'Enviando programador [{tamanho_kb} KB]...')
    ok, msg = fhops.upload_loader(porta, loader_path, log_cb=log_cb)
    if not ok:
        return False, f'Falha na comunicacao: {msg}', device_data
    _lcb('  Programador carregado')
    _pcb(30)
    _lcb('Configurando dispositivo...')
    mem_type, sector, num_luns, storage_info = fhops.detect_storage_auto(porta, log_cb=log_cb, memory_hint=memoria)
    device_data['mem_type'] = mem_type
    device_data['sector_size'] = sector
    device_data['num_luns'] = num_luns
    device_data['storage_info'] = storage_info
    mem_upper = mem_type.upper()
    _lcb(f'  Memoria   : {mem_upper}')
    _lcb(f'  Setor     : {sector} bytes')
    _lcb(f'  LUNs      : {num_luns}')
    prod = storage_info.get('prod_name', '')
    mfr_id = storage_info.get('manufacturer_id')
    if prod:
        mfr_name = _MEM_MANUFACTURERS.get(mfr_id, '') if mfr_id else ''
        storage_label = f'{mfr_name} {prod}'.strip() if mfr_name else prod
        _lcb(f'  Chip mem  : {storage_label}')
        device_data['storage_label'] = storage_label
    total_blocks = storage_info.get('total_blocks', 0)
    if total_blocks and sector:
        cap_gb = total_blocks * sector / 1073741824
        if cap_gb > 0:
            _lcb(f'  Capacidade: ~{cap_gb:.0f} GB')
            device_data['capacidade_gb'] = round(cap_gb, 1)
    _pcb(45)
    _lcb('Lendo mapa de particoes...')
    todas_particoes = []
    if mem_type == 'ufs':
        gpt_results = fhops.get_all_gpt_ufs(porta, num_luns, log_cb=log_cb)
        for lun, gpt_path in gpt_results:
            _pcb(45 + lun * 10 // max(num_luns, 1))
            gpt_data = parse_gpt_file(gpt_path, sector)
            if gpt_data.get('error'):
                _lcb(f'  LUN {lun}: {gpt_data['error']}')
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
    _lcb(f'  Total: {total_parts} particoes em {num_luns} LUN(s)')
    if total_parts == 0:
        return False, 'Nenhuma particao encontrada no dispositivo.', device_data
    _pcb(60)
    particoes_para_zerar = []
    for part_name in particoes_alvo:
        _lcb(f"Localizando '{part_name}'...")
        ok_val, msg_val, part_info = _validar_particao(part_name, todas_particoes)
        if not ok_val:
            _lcb(f'  {msg_val}')
            if part_name.lower() == 'userdata':
                _lcb('  (userdata opcional ÔÇö continuando sem ela)')
                continue
            return False, msg_val, device_data
        lun = part_info.get('lun', 0)
        start = part_info['start_lba']
        count = part_info['num_sectors']
        size_kb = count * sector // 1024
        _lcb(f'  Encontrada: LUN {lun}, setores {start}-{start + count - 1} ({size_kb} KB)')
        particoes_para_zerar.append(part_info)
    if not particoes_para_zerar:
        return False, 'Nenhuma particao valida encontrada.', device_data
    _pcb(70)
    zeradas = []
    def _smart_progress(pct: int):
        mapped = 70 + int(pct * 20 / 100)
        _pcb(min(mapped, 90))
    for i, part_info in enumerate(particoes_para_zerar):
        name = part_info['name']
        ok_smart, msg_smart = _smart_erase_partition(porta, mem_type, part_info, sector, log_cb=log_cb, progress_cb=_smart_progress)
        if not ok_smart:
            _lcb(f'  Falha ao zerar {name}: {msg_smart}')
            if name.lower() == 'persistent':
                return False, f'Falha ao remover FRP: {msg_smart}', device_data
            _lcb('  (continuando com as demais particoes)')
            continue
        _lcb(f'  {name.upper()} zerada com sucesso')
        zeradas.append(name)
        _pcb(70 + (i + 1) * 20 // len(particoes_para_zerar))
    device_data['particoes_apagadas'] = zeradas
    if not zeradas:
        return False, 'Nenhuma particao foi zerada.', device_data
    _pcb(95)
    _lcb('Reiniciando dispositivo...')
    fhops.reset_device(porta, mem_type, log_cb=log_cb)
    _pcb(100)
    tempo = time.time() - t_inicio
    device_data['tempo_total'] = round(tempo, 1)
    _lcb('')
    _lcb('==========================================')
    _lcb('  FRP SAMSUNG REMOVIDO COM SUCESSO!')
    _lcb('==========================================')
    _lcb('')
    _lcb('  1. O aparelho vai reiniciar')
    _lcb('  2. Configure normalmente')
    _lcb('')
    _lcb(f'  Tempo total: {tempo:.1f} segundos')
    return True, 'FRP removido com sucesso!', device_data
