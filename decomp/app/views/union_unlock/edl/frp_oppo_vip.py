'''
FRP OPPO/Realme com VIP Auth via QSaharaServer + fh_loader.
TECH UNION SOLUTIONS ÔÇö Modulo isolado
Fluxo VIP validado (PCAP Pandora + testes OPPO A3X/A40 SM6115):
  1. Detecta porta COM (EDL 9008)
  2. Upload loader VIP via QSaharaServer (Sahara protocol)
  3. VIP Auth completo (4 sub-etapas):
     a) fh_loader --signeddigests=digest.bin  -> "Signature Passed"
     b) fh_loader --sendxml=verify.xml        -> <verify EnableVip="0"/>
     c) fh_loader --signeddigests=sign.bin    -> "verify passed" + "disable VIP"
     d) fh_loader --sendxml=configure.xml     -> <configure MaxDigestTableSizeInBytes="0"/>
  4. Detecta storage (UFS/eMMC) SEM --signeddigests (device ja em modo W)
  5. Le GPT para localizar FRP
  6. Valida seguranca (blacklist + whitelist)
  7. Patch zeros nos primeiros setores do FRP (nao erase!)
  8. Reset
Apos VIP auth completo, NAO re-enviar --signeddigests nas chamadas subsequentes.
O device mantem o estado "W mode" e re-enviar digest causa re-handshake indesejado.
SEGURANCA: Nunca apaga por nome ÔÇö sempre por setor lido do GPT.
'''
import os
import tempfile
import time
from typing import (Callable, Dict, List, Optional, Tuple)
try:
    from app.views.union_unlock.edl import firehose_ops as fhops
    from app.views.union_unlock.edl.gpt_parser import parse_gpt_file
except ImportError:
    import firehose_ops as fhops
    from gpt_parser import parse_gpt_file
def _log(msg: str):
    print(f'[FRP_VIP] {msg}', flush=True)
PARTICOES_SEGURAS = frozenset({'frp', 'config', 'persist', 'userdata', 'persistent'})
PARTICOES_PROIBIDAS = frozenset({'tz', 'abl', 'aop', 'cdt', 'ddr', 'fsc', 'fsg', 'hyp', 'rpm', 'ssd', 'xbl', 'tz_a', 'tz_b', 'abl_a', 'abl_b', 'aop_a', 'aop_b', 'hyp_a', 'hyp_b', 'modem', 'rpm_a', 'rpm_b', 'xbl_a', 'xbl_b', 'cmnlib', 'devcfg', 'modem_a', 'modem_b', 'cmnlib64', 'devcfg_a', 'devcfg_b', 'keystore', 'modemst1', 'modemst2', 'keymaster', 'xbl_config', 'keymaster_a', 'keymaster_b', 'NON-HLOS'})
_FRP_MAX_PATCH_SECTORS = 4
def _validar_particao(part_name: str, todas_particoes: List[Dict]) -> Tuple[bool, str, Optional[Dict]]:
    '''Valida que a particao existe, e segura e unica.'''
    lower = part_name.lower()
    if lower in PARTICOES_PROIBIDAS:
        return False, f"Particao '{part_name}' e PROIBIDA", None
    if lower not in PARTICOES_SEGURAS:
        return False, f"Particao '{part_name}' nao esta na lista de seguras", None
    matches = [p for p in todas_particoes if p['name'].lower() == lower]
    if not matches:
        return False, f"Particao '{part_name}' nao encontrada", None
    if len(matches) > 1:
        return False, f"Multiplas '{part_name}' encontradas ({len(matches)})", None
    part = matches[0]
    if part.get('start_lba', 0) == 0:
        return False, f"Particao '{part_name}' com setor invalido", None
    if part.get('num_sectors', 0) == 0:
        return False, f"Particao '{part_name}' com tamanho zero", None
    return True, 'OK', part
def _salvar_vip_temp(digest_data: bytes, sign_data: bytes) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    '''Salva digest e sign em arquivos temporarios para fh_loader.
    Retorna (digest_path, sign_path, vip_dir).
    '''
    vip_dir = fhops._edl_mkdtemp(prefix='vip_')
    try:
        digest_path = os.path.join(vip_dir, 'vip_digest.bin')
        sign_path = os.path.join(vip_dir, 'vip_sign.bin')
        with open(digest_path, 'wb') as f:
            f.write(digest_data)
        with open(sign_path, 'wb') as f:
            f.write(sign_data)
    except Exception as e:
        _log(f'Erro ao salvar VIP temp: {e}')
        return (None, None, None)
    return digest_path, sign_path, vip_dir
def _executar_vip_auth(porta: str, memoria: str, digest_path: str, sign_path: str, log_cb: Optional[Callable[[str], None]]=None) -> Tuple[bool, str]:
    '''
Executa VIP Auth completo em 4 sub-etapas via fh_loader.
Fluxo validado (PCAP Pandora + testes OPPO A3X/A40 SM6115):
  1. fh_loader --signeddigests=digest.bin  -> "Signature Passed"
  2. fh_loader --sendxml -> <verify EnableVip="0"/>
  3. fh_loader --signeddigests=sign.bin    -> "verify passed" + "disable VIP"
  4. fh_loader --sendxml -> <configure MaxDigestTableSizeInBytes="0"/>
EnableVip="0" desabilita a verificacao VIP por operacao,
permitindo leitura/escrita completa de todas as particoes.
NAO re-enviar --signeddigests nas chamadas posteriores.
Retorna (sucesso, mensagem).
'''
    from app.views.union_unlock.edl.config import FH_LOADER
    import subprocess
    import threading
    _CREATE_NO_WINDOW = 134217728 if os.name == 'nt' else 0
    _STEP_TIMEOUT = 30
    port_arg = f'\\\\.\\{porta}'
    mem_arg = memoria.lower()
    if mem_arg not in ('emmc', 'ufs'):
        mem_arg = 'emmc'
    vip_dir = os.path.dirname(digest_path)
    def _run_fh(args: list, timeout: int=_STEP_TIMEOUT, label: str='') -> Tuple[int, str]:
        '''Executa fh_loader com timeout e retorna (returncode, output).'''
        try:
            proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=vip_dir, creationflags=_CREATE_NO_WINDOW)
            kill_timer = threading.Timer(timeout, (lambda: proc.kill()))
            kill_timer.daemon = True
            kill_timer.start()
            lines = []
            for line in iter(proc.stdout.readline, ''):
                stripped = line.rstrip()
                if stripped:
                    lines.append(stripped)
                    _log(f'  vip[{label}]: {stripped}')
            kill_timer.cancel()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        except Exception as e:
            _log(f'  vip[{label}] erro: {e}')
            return -1, str(e)
        return proc.returncode, '\n'.join(lines)
    def _write_xml(filename: str, content: str) -> str:
        '''Escreve XML temporario para sendxml.'''
        path = os.path.join(vip_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return path
    def _base_args() -> list:
        return [str(FH_LOADER), f'--port={port_arg}', '--noprompt', f'--memoryname={mem_arg}', '--zlpawarehost=1']
    try:
        _log('VIP Auth [1/4]: enviando digest table...')
        if log_cb:
            log_cb('VIP [1/4]: Enviando digest...')
        args = _base_args() + [f'--signeddigests={digest_path}']
        rc, out = _run_fh(args, label='digest')
        out_lower = out.lower()
        has_error = 'signature failed' in out_lower or 'hash of data' in out_lower or 'authentication of signed hash failed' in out_lower or 'digest table was rejected' in out_lower
        if has_error:
            return (False, 'Digest rejeitado pelo dispositivo.\nVerifique se o loader e os dados VIP sao compativeis.\nDetalhes no log acima.')
        sig_passed = 'signature' in out_lower and 'passed' in out_lower or 'signed digest sent' in out_lower
        vip_enabled = 'vip is enabled' in out_lower
        if not sig_passed and not vip_enabled and 'successfully' not in out_lower:
            return (False, 'Digest rejeitado pelo dispositivo.\nVerifique se o loader e os dados VIP sao compativeis.')
        _log('VIP Auth [1/4]: Digest aceito')
        time.sleep(0.5)
        _log('VIP Auth [2/4]: enviando verify EnableVip=0...')
        if log_cb:
            log_cb('VIP [2/4]: Verify...')
        verify_xml = _write_xml('vip_verify.xml', '<?xml version="1.0" encoding="UTF-8" ?><data><verify EnableVip="0"/></data>')
        args = _base_args() + [f'--sendxml={verify_xml}']
        rc, out = _run_fh(args, label='verify')
        _log('VIP Auth [2/4]: Verify enviado')
        time.sleep(0.5)
        _log('VIP Auth [3/4]: enviando sign.bin...')
        if log_cb:
            log_cb('VIP [3/4]: Assinatura...')
        args = _base_args() + [f'--signeddigests={sign_path}']
        rc, out = _run_fh(args, label='sign')
        out_lower = out.lower()
        sign_error = 'signature failed' in out_lower or 'hash of data' in out_lower or 'authentication of signed hash failed' in out_lower or 'sign rejected' in out_lower
        if sign_error:
            return (False, 'Assinatura VIP rejeitada.\nOs dados sign podem estar incorretos.')
        verify_passed = 'verify passed' in out_lower
        w_mode = 'w mode' in out_lower
        if not verify_passed and not w_mode and 'successfully' not in out_lower:
            return (False, 'Assinatura VIP rejeitada.\nOs dados sign podem estar incorretos.')
        _log('VIP Auth [3/4]: Sign aceito ÔÇö verify passed!')
        time.sleep(0.5)
        _log('VIP Auth [4/4]: enviando configure explicito...')
        if log_cb:
            log_cb('VIP [4/4]: Configure...')
        cfg_xml = _write_xml('vip_configure.xml', f'<?xml version="1.0" encoding="UTF-8" ?><data><configure MemoryName="{mem_arg}" Verbose="0" MaxDigestTableSizeInBytes="0" MaxPayloadSizeToTargetInBytes="1048576" ZlpAwareHost="1" SkipWrite="0" SkipStorageInit="0"/></data>')
        args = _base_args() + [f'--sendxml={cfg_xml}']
        rc, out = _run_fh(args, label='configure')
        _log('VIP Auth [4/4]: Configure concluido')
        _log('VIP Auth: SUCESSO ÔÇö dispositivo em modo W (escrita completa)!')
        if log_cb:
            log_cb('Autenticacao VIP concluida!')
        return (True, 'VIP Auth completo ÔÇö modo W ativo')
    except Exception as e:
        _log(f'VIP Auth erro: {e}')
        return False, f'Falha na autenticacao: {e}'
def executar_frp_vip(loader_path: str, memoria: str, digest_data: bytes, sign_data: bytes, particoes_alvo: Optional[List[str]]=None, log_cb: Optional[Callable[[str], None]]=None, progress_cb: Optional[Callable[[int], None]]=None) -> Tuple[bool, str, Dict]:
    """
Executa FRP com VIP Auth via QSaharaServer + fh_loader --signeddigests.
Parametros:
    loader_path: caminho do loader VIP ELF
    memoria: 'ufs' ou 'emmc' (hint do banco de dados)
    digest_data: bytes do VIP digest (do banco edl_auth_vip)
    sign_data: bytes do VIP sign (do banco edl_auth_vip)
    particoes_alvo: lista de nomes (default: ['frp'])
    log_cb: callback de log para UI
    progress_cb: callback de progresso (0-100) para UI
Retorna:
    (sucesso, mensagem, device_data)
"""
    if particoes_alvo is None:
        particoes_alvo = ['frp']
    def _lcb(msg: str):
        _log(msg)
        if log_cb:
            log_cb(msg)
    def _pcb(val: int):
        if progress_cb:
            progress_cb(val)
    device_data = {}
    t_inicio = time.time()
    vip_dir = None
    try:
        _pcb(5)
        _lcb('Conectando ao dispositivo...')
        porta = fhops.detectar_porta_com()
        if not porta:
            if vip_dir:
                if os.path.isdir(vip_dir):
                    for f in os.listdir(vip_dir):
                        try:
                            os.remove(os.path.join(vip_dir, f))
                        except OSError:
                            continue
                    try:
                        os.rmdir(vip_dir)
                    except OSError:
                        pass
                    return
                return
            return
    except:
        if os.path.isdir(vip_dir):
            for f in os.listdir(vip_dir):
                try:
                    try:
                        os.remove(os.path.join(vip_dir, f))
                    except OSError:
                        continue
                except OSError:
                    pass
    try:
        _lcb(f'  Porta EDL : {porta}')
        device_data['porta'] = porta
        _pcb(8)
        _lcb('Preparando dados de autenticacao...')
        vip_digest_path, vip_sign_path, vip_dir = _salvar_vip_temp(digest_data, sign_data)
        if not vip_digest_path:
            if vip_dir:
                if os.path.isdir(vip_dir):
                    for f in os.listdir(vip_dir):
                        try:
                            os.remove(os.path.join(vip_dir, f))
                        except OSError:
                            continue
                    try:
                        os.rmdir(vip_dir)
                    except OSError:
                        pass
                    return
                return
            return
    except:
        if os.path.isdir(vip_dir):
            for f in os.listdir(vip_dir):
                try:
                    try:
                        os.remove(os.path.join(vip_dir, f))
                    except OSError:
                        continue
                except OSError:
                    pass
    try:
        _lcb(f'  Digest: {len(digest_data)} bytes')
        _lcb(f'  Sign:   {len(sign_data)} bytes')
        _pcb(10)
        if not os.path.exists(loader_path):
            if vip_dir:
                if os.path.isdir(vip_dir):
                    for f in os.listdir(vip_dir):
                        try:
                            os.remove(os.path.join(vip_dir, f))
                        except OSError:
                            continue
                    try:
                        os.rmdir(vip_dir)
                    except OSError:
                        pass
                    return
                return
            return
    except:
        if os.path.isdir(vip_dir):
            for f in os.listdir(vip_dir):
                try:
                    try:
                        os.remove(os.path.join(vip_dir, f))
                    except OSError:
                        continue
                except OSError:
                    pass
    try:
        tamanho_kb = os.path.getsize(loader_path) // 1024
        _lcb(f'Enviando programador [{tamanho_kb} KB]...')
        ok, msg = fhops.upload_loader(porta, loader_path, log_cb=log_cb)
        if not ok:
            if vip_dir:
                if os.path.isdir(vip_dir):
                    for f in os.listdir(vip_dir):
                        try:
                            os.remove(os.path.join(vip_dir, f))
                        except OSError:
                            continue
                    try:
                        os.rmdir(vip_dir)
                    except OSError:
                        pass
                    return
                return
            return
    except:
        if os.path.isdir(vip_dir):
            for f in os.listdir(vip_dir):
                try:
                    try:
                        os.remove(os.path.join(vip_dir, f))
                    except OSError:
                        continue
                except OSError:
                    pass
    try:
        _lcb('  Programador carregado')
        _pcb(20)
        _lcb('Autenticando VIP...')
        ok_vip, msg_vip = _executar_vip_auth(porta, memoria, vip_digest_path, vip_sign_path, log_cb=log_cb)
        if not ok_vip:
            if vip_dir:
                if os.path.isdir(vip_dir):
                    for f in os.listdir(vip_dir):
                        try:
                            os.remove(os.path.join(vip_dir, f))
                        except OSError:
                            continue
                    try:
                        os.rmdir(vip_dir)
                    except OSError:
                        pass
                    return
                return
            return
    except:
        if os.path.isdir(vip_dir):
            for f in os.listdir(vip_dir):
                try:
                    try:
                        os.remove(os.path.join(vip_dir, f))
                    except OSError:
                        continue
                except OSError:
                    pass
    try:
        _pcb(30)
        _lcb('Configurando dispositivo...')
        mem_type, sector, num_luns, storage_info = fhops.detect_storage_auto(porta, log_cb=log_cb, memory_hint=memoria)
        device_data['mem_type'] = mem_type
        device_data['sector_size'] = sector
        device_data['num_luns'] = num_luns
        mem_upper = mem_type.upper()
        _lcb(f'  Memoria   : {mem_upper}')
        _lcb(f'  Setor     : {sector} bytes')
        _lcb(f'  LUNs      : {num_luns}')
        prod = storage_info.get('prod_name', '')
        if prod:
            _lcb(f'  Chip mem  : {prod}')
            device_data['storage_label'] = prod
        _pcb(45)
        _lcb('Lendo mapa de particoes...')
        todas_particoes = []
        if mem_type == 'ufs':
            gpt_results = []
            for lun_i in range(num_luns):
                ok_g, gp = fhops.get_gpt_via_read(porta, mem_type, lun_i, log_cb=log_cb)
                if ok_g:
                    gpt_results.append((lun_i, gp))
            for lun, gpt_path in gpt_results:
                gpt_data = parse_gpt_file(gpt_path, sector)
                if gpt_data.get('error'):
                    continue
                for p in gpt_data.get('partitions', []):
                    p['lun'] = lun
                todas_particoes.extend(gpt_data.get('partitions', []))
        else:
            ok_gpt, gpt_path = fhops.get_gpt_via_read(porta, mem_type, 0, log_cb=log_cb)
            if ok_gpt and gpt_path and os.path.getsize(gpt_path) > 0:
                gpt_data = parse_gpt_file(gpt_path, sector)
                if not gpt_data.get('error'):
                    for p in gpt_data.get('partitions', []):
                        p['lun'] = 0
                    todas_particoes.extend(gpt_data.get('partitions', []))
        total_parts = len(todas_particoes)
        device_data['total_particoes'] = total_parts
        _lcb(f'  Total: {total_parts} particoes em {num_luns} LUN(s)')
        if total_parts == 0:
            fail_msg = 'Nenhuma particao encontrada.\nVerifique se o loader e compativel com o dispositivo.'
            if vip_dir:
                if os.path.isdir(vip_dir):
                    for f in os.listdir(vip_dir):
                        try:
                            os.remove(os.path.join(vip_dir, f))
                        except OSError:
                            continue
                    try:
                        os.rmdir(vip_dir)
                    except OSError:
                        pass
                    return
                return
            return
    except:
        if os.path.isdir(vip_dir):
            for f in os.listdir(vip_dir):
                try:
                    try:
                        os.remove(os.path.join(vip_dir, f))
                    except OSError:
                        continue
                except OSError:
                    pass
    try:
        _pcb(60)
        particoes_para_patch = []
        for part_name in particoes_alvo:
            _lcb(f"Localizando '{part_name}'...")
            ok_val, msg_val, part_info = _validar_particao(part_name, todas_particoes)
            if not ok_val:
                _lcb(f'  {msg_val}')
                if part_name.lower() in ('userdata', 'config'):
                    _lcb(f'  ({part_name} opcional ÔÇö continuando)')
                    continue
                False, msg_val, device_data
                if vip_dir:
                    if os.path.isdir(vip_dir):
                        for f in os.listdir(vip_dir):
                            try:
                                os.remove(os.path.join(vip_dir, f))
                            except OSError:
                                continue
                        try:
                            os.rmdir(vip_dir)
                        except OSError:
                            pass
                        return
                    return
                return
            lun = part_info.get('lun', 0)
            start = part_info['start_lba']
            count = part_info['num_sectors']
            size_kb = count * sector // 1024
            _lcb(f'  Encontrada: LUN {lun}, setores {start}-{start + count - 1} ({size_kb} KB)')
            particoes_para_patch.append(part_info)
            continue
    except:
        if os.path.isdir(vip_dir):
            for f in os.listdir(vip_dir):
                try:
                    try:
                        os.remove(os.path.join(vip_dir, f))
                    except OSError:
                        continue
                except OSError:
                    pass
    if not particoes_para_patch:
        if vip_dir:
            if os.path.isdir(vip_dir):
                for f in os.listdir(vip_dir):
                    try:
                        os.remove(os.path.join(vip_dir, f))
                    except OSError:
                        continue
                try:
                    os.rmdir(vip_dir)
                except OSError:
                    pass
                return
            return
        return
    try:
        _pcb(70)
        patcheadas = []
        for i, part_info in enumerate(particoes_para_patch):
            name = part_info['name']
            _lcb(f'Zerando {name.upper()} via patch...')
            ok_patch, msg_patch = fhops.patch_partition(porta, mem_type, part_info, sector, lun=part_info.get('lun', 0), max_sectors=_FRP_MAX_PATCH_SECTORS, log_cb=log_cb, progress_cb=progress_cb)
            if not ok_patch:
                _lcb(f'  Patch falhou: {msg_patch}')
                _lcb('  Tentando erase como fallback...')
                ok_erase, msg_erase = fhops.erase_partition(porta, mem_type, part_info, sector, lun=part_info.get('lun', 0), log_cb=log_cb)
                if not ok_erase:
                    _lcb(f'  Erase tambem falhou: {msg_erase}')
                    if name.lower() == 'frp':
                        False, f'Falha ao limpar FRP: {msg_erase}', device_data
                        if vip_dir:
                            if os.path.isdir(vip_dir):
                                for f in os.listdir(vip_dir):
                                    try:
                                        os.remove(os.path.join(vip_dir, f))
                                    except OSError:
                                        continue
                                try:
                                    os.rmdir(vip_dir)
                                except OSError:
                                    pass
                                return
                            return
                        return
                _lcb(f'  {name.upper()} limpa via erase (fallback)')
                patcheadas.append(name)
                continue
            _lcb(f'  {name.upper()} zerada via patch')
            patcheadas.append(name)
            _pcb(70 + (i + 1) * 20 // len(particoes_para_patch))
            continue
    except:
        if os.path.isdir(vip_dir):
            for f in os.listdir(vip_dir):
                try:
                    try:
                        os.remove(os.path.join(vip_dir, f))
                    except OSError:
                        continue
                except OSError:
                    pass
    device_data['particoes_apagadas'] = patcheadas
    if not patcheadas:
        if vip_dir:
            if os.path.isdir(vip_dir):
                for f in os.listdir(vip_dir):
                    try:
                        os.remove(os.path.join(vip_dir, f))
                    except OSError:
                        continue
                try:
                    os.rmdir(vip_dir)
                except OSError:
                    pass
                return
            return
        return
    try:
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
    except:
        if os.path.isdir(vip_dir):
            for f in os.listdir(vip_dir):
                try:
                    try:
                        os.remove(os.path.join(vip_dir, f))
                    except OSError:
                        continue
                except OSError:
                    pass
    if vip_dir:
        if os.path.isdir(vip_dir):
            for f in os.listdir(vip_dir):
                try:
                    os.remove(os.path.join(vip_dir, f))
                except OSError:
                    continue
            try:
                os.rmdir(vip_dir)
            except OSError:
                return
# WARNING: Decompyle incomplete
