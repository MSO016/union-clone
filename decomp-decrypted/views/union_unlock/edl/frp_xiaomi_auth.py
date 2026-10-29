import os
import time
from typing import (Callable, Dict, List, Optional, Tuple)
try:
    from app.views.union_unlock.edl import firehose_ops as fhops
    from app.views.union_unlock.edl.gpt_parser import parse_gpt_file, is_critical
except ImportError:
    import firehose_ops as fhops
    from gpt_parser import parse_gpt_file, is_critical
def _log(msg: str):
    print(f'[FRP_AUTH] {msg}', flush=True)
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
def executar_frp_auth(loader_path: str, memoria: str, particoes_alvo: List[str], log_cb: Optional[Callable[[str], None]]=None, progress_cb: Optional[Callable[[int], None]]=None, auth_manufacturer: str='xiaomi') -> Tuple[bool, str, Dict]:
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
    _lcb('Conectando ao dispositivo...')
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
    _pcb(25)
    _lcb('Autenticando dispositivo...')
    auth_ok, auth_msg = fhops.firehose_auth(porta, auth_manufacturer, log_cb=log_cb)
    device_data['auth_sucesso'] = auth_ok
    if auth_ok:
        _lcb('  Autenticacao concluida com sucesso')
    else:
        _lcb('  Verificacao concluida')
    _pcb(35)
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
            _pcb(45 + lun * 15 // max(num_luns, 1))
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
    _pcb(65)
    particoes_para_erase = []
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
        particoes_para_erase.append(part_info)
    if not particoes_para_erase:
        return False, 'Nenhuma particao valida para erase.', device_data
    _pcb(70)
    apagadas = []
    _PATCH_PARTITIONS = ('frp', 'persistent', 'config')
    for i, part_info in enumerate(particoes_para_erase):
        name = part_info['name']
        name_lower = name.lower()
        _lcb(f'Limpando {name.upper()}...')
        if name_lower in _PATCH_PARTITIONS:
            ok_op, msg_op = fhops.patch_partition(porta, mem_type, part_info, sector, lun=part_info.get('lun', 0), max_sectors=4, log_cb=log_cb, progress_cb=progress_cb, full_zero=True)
            if not ok_op:
                _lcb('  Patch falhou, tentando erase...')
                ok_op, msg_op = fhops.erase_partition(porta, mem_type, part_info, sector, lun=part_info.get('lun', 0), log_cb=log_cb)
        else:
            ok_op, msg_op = fhops.erase_partition(porta, mem_type, part_info, sector, lun=part_info.get('lun', 0), log_cb=log_cb)
            if not ok_op:
                _lcb('  Erase falhou, tentando patch...')
                ok_op, msg_op = fhops.patch_partition(porta, mem_type, part_info, sector, lun=part_info.get('lun', 0), max_sectors=4, log_cb=log_cb, progress_cb=progress_cb, full_zero=True)
        if not ok_op:
            _lcb(f'  Falha ao limpar {name}: {msg_op}')
            if name_lower == 'frp':
                return False, f'Falha ao limpar FRP: {msg_op}', device_data
            _lcb('  (continuando com as demais particoes)')
            continue
        _lcb(f'  {name.upper()} limpa com sucesso')
        apagadas.append(name)
        _pcb(70 + (i + 1) * 20 // len(particoes_para_erase))
        continue
    device_data['particoes_apagadas'] = apagadas
    if not apagadas:
        return False, 'Nenhuma particao foi apagada.', device_data
    _pcb(95)
    _lcb('Reiniciando dispositivo...')
    fhops.reset_device(porta, mem_type, log_cb=log_cb)
    _pcb(100)
    tempo = time.time() - t_inicio
    device_data['tempo_total'] = round(tempo, 1)
    _lcb('')
    _lcb('==========================================')
    _lcb('  FRP REMOVIDO COM SUCESSO!')
    _lcb('==========================================')
    _lcb('')
    _lcb('  1. O aparelho vai reiniciar')
    _lcb('  2. Configure normalmente')
    _lcb('')
    _lcb(f'  Tempo total: {tempo:.1f} segundos')
    return True, 'FRP removido com sucesso!', device_data
