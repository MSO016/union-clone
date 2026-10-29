'''
Wrapper de operacoes Firehose via QSaharaServer.exe + fh_loader.exe.
TECH UNION SOLUTIONS ÔÇö Modulo de operacoes de baixo nivel
Fluxo:
  1. QSaharaServer: upload do loader via Sahara
  2. Xiaomi EDL Auth: envio de <sig> + assinatura RSA (se necessario)
  3. fh_loader: operacoes no storage (GPT, erase, read, write, reset)
SEGURAN├çA: Nunca expor --erase=N (apaga LUN inteiro).
Sempre usar --sendxml com setores especificos.
'''
import logging
import os
import re
import sys
import subprocess
import tempfile
import threading
import time
import base64
from pathlib import Path
from typing import (List, Optional, Tuple, Callable)
try:
    from app.views.union_unlock.edl.config import (QSAHARA, FH_LOADER, TOOLS_DIR)
    from app.views.union_unlock.edl.gpt_parser import is_critical
    from app.views.union_unlock.edl.edl_auth import get_auth_signatures
except ImportError:
    from config import (QSAHARA, FH_LOADER, TOOLS_DIR)
    from gpt_parser import is_critical
    from edl_auth import get_auth_signatures
_CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
_logger = logging.getLogger('firehose_ops')
def _log(msg: str):
    _logger.debug(msg)
def _edl_tmp_base() -> str:
    '''Retorna diretorio oculto para temporarios EDL.
    Usa %LOCALAPPDATA%\\.union_edl\\ (Windows) ou /tmp/.union_edl/ (Linux).
    Garante que dados como GPT, port_trace e XMLs nao fiquem na temp publica.
    No Windows aplica atributo HIDDEN+SYSTEM para nao aparecer no Explorer.
    '''
    if sys.platform == 'win32':
        base = os.environ.get('LOCALAPPDATA', tempfile.gettempdir())
    else:
        base = tempfile.gettempdir()
    edl_dir = os.path.join(base, '.union_edl')
    os.makedirs(edl_dir, exist_ok=True)
    if sys.platform == 'win32':
        try:
            import ctypes
            attrs = ctypes.windll.kernel32.GetFileAttributesW(edl_dir)
            if attrs == -1 or not attrs & 2:
                ctypes.windll.kernel32.SetFileAttributesW(edl_dir, 8198)
        except Exception:
            pass
        return edl_dir
    return edl_dir
def _edl_mkdtemp(prefix: str='op_') -> str:
    '''Cria subdiretorio temporario dentro da pasta oculta EDL.'''
    return tempfile.mkdtemp(prefix=prefix, dir=_edl_tmp_base())
def _edl_cleanup_old(max_age_hours: int=12):
    '''Remove subdiretorios orfaos mais antigos que max_age_hours.'''
    try:
        base = _edl_tmp_base()
        now = time.time()
        cutoff = now - max_age_hours * 3600
        for entry in os.listdir(base):
            path = os.path.join(base, entry)
            if os.path.isdir(path):
                pass
        try:
            mtime = os.path.getmtime(path)
            if mtime < cutoff:
                import shutil
                shutil.rmtree(path, ignore_errors=True)
        except OSError:
            pass
    except OSError:
        return
_edl_cleanup_old()
def _cleanup_port_trace(directory: str):
    '''Remove port_trace.txt gerado pelo fh_loader para nao vazar caminhos.'''
    try:
        pt = os.path.join(directory, 'port_trace.txt')
        if os.path.exists(pt):
            os.remove(pt)
            return
    except OSError:
        pass
_BOXES_EDL = {'octoplus': 'Octoplus', 'octoplus_samsung': 'Octoplus Samsung', 'octoplus_qualcomm': 'Octoplus Qualcomm', 'umtv2': 'UMT Pro', 'nck_dongle': 'NCK Dongle', 'samfw_frp_tool': 'SamFW FRP Tool', 'samfw': 'SamFW Tool', 'qpst': 'QPST', 'qfil': 'QFIL', 'qfirehose': 'QFireHose', 'miflash': 'MiFlash', 'xiaomiflash': 'Xiaomi Flash Tool', 'easyjtag': 'Easy JTAG', 'medusa_pro': 'Medusa Pro', 'chimera': 'Chimera Tool', 'z3x': 'Z3X', 'miracle': 'Miracle Box'}
def detectar_boxes_ativas() -> list:
    '''Detecta ferramentas de terceiro que podem estar segurando a porta COM.
    Usa Get-Process para listar processos, sem abrir nenhuma porta.'''
    if sys.platform != 'win32':
        return []
    encontradas = []
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-Command', 'Get-Process | Select-Object -ExpandProperty ProcessName'], capture_output=True, text=True, timeout=5, creationflags=_CREATE_NO_WINDOW)
        nomes = set((n.strip().lower() for n in r.stdout.split('\n') if n.strip()))
        for chave, label in _BOXES_EDL.items():
            if chave in nomes:
                encontradas.append(label)
    except Exception:
        pass
    return encontradas
def firehose_auth(com_port: str, manufacturer: str='xiaomi', log_cb: Optional[Callable[[str], None]]=None) -> Tuple[bool, str]:
    '''
    Autentica sessao Firehose em dispositivos que exigem EDL Auth.
    Envia <sig> + assinatura RSA de 256 bytes via porta serial.
    Deve ser chamada APOS o Sahara upload e ANTES do fh_loader.
    As assinaturas sao carregadas de edl_auth.py (por fabricante).
    Retorna (sucesso, mensagem).
    '''
    auth_sigs = get_auth_signatures(manufacturer)
    if not auth_sigs:
        return (False, 'Autenticacao nao disponivel para este fabricante')
    try:
        import serial
    except ImportError:
        return (False, 'Componente de comunicacao nao instalado')
    port_path = f'\\\\.\\{com_port}' if not com_port.startswith('\\\\.\\') else com_port
    _log(f'EDL Auth ({manufacturer}): tentando autenticar em {com_port}')
    if log_cb:
        log_cb('Autenticando dispositivo...')
    try:
        ser = serial.Serial(port_path, baudrate=115200, timeout=2, write_timeout=2)
    except Exception as e:
        _log(f'Erro ao abrir porta {com_port}: {e}')
        return (False, 'Falha ao conectar com o dispositivo.\nVerifique o cabo USB e reconecte.')
    try:
        time.sleep(0.3)
        pending = ser.read(ser.in_waiting or 4096)
        if pending:
            _log(f'Auth: drenados {len(pending)} bytes iniciais')
        sig_xml = b'<?xml version="1.0" encoding="UTF-8"?><data><sig TargetName="sig" size_in_bytes="256" verbose="1"/></data>'
        for idx, sig_b64 in enumerate(auth_sigs):
            sig_bytes = base64.b64decode(sig_b64)
            if len(sig_bytes) != 256:
                continue
            nop_xml = b'<?xml version="1.0" encoding="UTF-8"?><data><NOP value="ping"/></data>'
            ser.write(nop_xml)
            time.sleep(0.2)
            ser.read(ser.in_waiting or 4096)
            ser.write(sig_xml)
            time.sleep(0.3)
            resp1 = ser.read(ser.in_waiting or 4096)
            resp1_text = resp1.decode('utf-8', errors='replace')
            _log(f'Auth: sig[{idx}] resp1={resp1_text[:200]}')
            if 'NAK' in resp1_text:
                _log(f'Auth: sig[{idx}] tag <sig> rejeitada')
                continue
            ser.write(sig_bytes)
            time.sleep(0.5)
            resp2 = ser.read(ser.in_waiting or 4096)
            resp2_text = resp2.decode('utf-8', errors='replace')
            _log(f'Auth: sig[{idx}] resp2={resp2_text[:200]}')
            if 'authenticated' in resp2_text.lower():
                _log(f'EDL Auth: SUCESSO com sig[{idx}]!')
                if log_cb:
                    log_cb('Autenticacao EDL concluida com sucesso!')
                ser.close()
                return (True, 'Autenticado')
            if 'ACK' not in resp2_text:
                continue
            if 'NAK' in resp2_text:
                continue
            _log(f'Auth: sig[{idx}] ACK recebido (possivel auth)')
            if log_cb:
                log_cb('Autenticacao EDL concluida!')
            ser.close()
            return (True, 'Autenticado (ACK)')
        try:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
        except Exception as e:
            try:
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                ser.close()
            except Exception:
                try:
                    try:
                        ser.close()
                    except Exception:
                        pass
                except Exception:
                    pass
            time.sleep(0.5)
            _log(f'Erro na autenticacao: {e}')
        else:
            ser.close()
            time.sleep(0.5)
            _log('EDL Auth: nenhuma assinatura aceita')
            if log_cb:
                log_cb('Verificacao concluida')
    except Exception as e:
        try:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            ser.close()
        except Exception:
            try:
                ser.close()
            except Exception:
                pass
        time.sleep(0.5)
        _log(f'Erro na autenticacao: {e}')
    return (False, 'Este modelo requer autenticacao especifica nao disponivel')
def firehose_auth_xiaomi(com_port: str, log_cb: Optional[Callable[[str], None]]=None) -> Tuple[bool, str]:
    """Wrapper de compatibilidade ÔÇö chama firehose_auth com manufacturer='xiaomi'."""
    return firehose_auth(com_port, manufacturer='xiaomi', log_cb=log_cb)
def firehose_vip_auth(com_port: str, digest_data: bytes, sign_data: bytes, log_cb: Optional[Callable[[str], None]]=None) -> Tuple[bool, str]:
    '''
    DESCONTINUADO ÔÇö VIP auth via serial raw nao funciona.
    O Firehose interpreta dados raw como XML e falha.
    Usar fh_loader --signeddigests=<path> ao inves (frp_oppo_vip.py).
    Mantido por compatibilidade ÔÇö retorna aviso.
    '''
    _log('firehose_vip_auth: DESCONTINUADO ÔÇö usar --signeddigests via fh_loader')
    return (False, 'VIP Auth via serial nao suportado.\nUse o fluxo FRP VIP (QSahara + fh_loader --signeddigests).')
def firehose_auth_oneplus(com_port: str, loader_path: str, projid: str='', log_cb: Optional[Callable[[str], None]]=None) -> Tuple[bool, str]:
    """
    Autentica sessao Firehose em dispositivos OnePlus via AES-CBC tokens.
    Diferente do auth Xiaomi (RSA sig), OnePlus usa setprojmodel (v1)
    ou setprocstart+setswprojmodel (v2/v3) via Firehose XML.
    Se projid nao for fornecido, tenta detectar via particao 'param'.
    Retorna (sucesso, mensagem).
    """
    try:
        from edl_auth_oneplus import (is_supported, get_model_name, get_auth_version, aplicar_auth_oneplus_via_fh, detectar_projid_via_param, DEVICE_CONFIG)
    except ImportError as e:
        _log(f'Modulo edl_auth_oneplus nao disponivel: {e}')
        return (False, 'Componente de autenticacao nao disponivel.\nVerifique a instalacao do programa.')
    fh_exe = str(FH_LOADER)
    if not projid:
        _log('OnePlus Auth: projid nao informado, tentando deteccao automatica...')
        if log_cb:
            log_cb('Detectando modelo...')
        projid = detectar_projid_via_param(fh_exe, com_port, loader_path, log_callback=log_cb)
    if not projid:
        _log('OnePlus Auth: projid nao detectado, tentando todos os conhecidos...')
        if log_cb:
            log_cb('Verificando compatibilidade...')
        for test_id in ('18821', '19821', '20886'):
            if log_cb:
                log_cb('Testando configuracao...')
            ok = aplicar_auth_oneplus_via_fh(fh_exe, com_port, loader_path, test_id, log_callback=log_cb)
            if ok:
                return (True, 'Autenticacao concluida')
        return (False, 'Modelo nao suportado para autenticacao automatica')
    if not is_supported(projid):
        _log(f'OnePlus Auth: projid {projid} nao suportado')
        return (False, 'Este modelo nao e suportado para autenticacao')
    model = get_model_name(projid)
    version = get_auth_version(projid)
    _log(f'OnePlus Auth: {model} (projid={projid}, v{version})')
    if log_cb:
        log_cb(f'Autenticando {model}...')
    ok = aplicar_auth_oneplus_via_fh(fh_exe, com_port, loader_path, projid, log_callback=log_cb)
    if ok:
        return True, f'Autenticacao concluida: {model}'
    return False, f'Falha na autenticacao: {model}.\nReconecte o dispositivo e tente novamente.'
def detectar_porta_com() -> Optional[str]:
    '''Detecta porta COM do QDLoader 9008 via WMI.'''
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-Command', "Get-WmiObject Win32_PnPEntity | Where-Object { $_.Name -match 'QDLoader' -or $_.Name -match '9008' } | Select-Object -ExpandProperty Name"], capture_output=True, text=True, timeout=10, creationflags=_CREATE_NO_WINDOW)
        for line in r.stdout.strip().split('\n'):
            m = re.search('COM(\\d+)', line)
            if m:
                return f'COM{m.group(1)}'
    except Exception:
        pass
    try:
        import serial.tools.list_ports
        for p in serial.tools.list_ports.comports():
            if '9008' in (p.description or ''):
                return p.device
            if p.vid != 1478:
                continue
            if not p.pid == 36872:
                continue
            return p.device
    except ImportError:
        return
def upload_loader(com_port: str, loader_path: str, log_cb: Optional[Callable[[str], None]]=None) -> Tuple[bool, str]:
    '''
    Fase 1 ÔÇö Sahara: upload do Firehose loader via QSaharaServer.
    Retorna (sucesso, mensagem).
    '''
    if not QSAHARA.exists():
        return (False, 'Componente nao encontrado.\nReinstale o programa ou entre em contato com o suporte.')
    if not os.path.exists(loader_path):
        return (False, 'Arquivo de suporte nao encontrado.\nReinstale o programa ou entre em contato com o suporte.')
    port_num = re.search('(\\d+)$', com_port)
    if not port_num:
        return False, f'Porta COM invalida: {com_port}'
    cmd = [str(QSAHARA), '-u', port_num.group(1), '-v', '0', '-s', f'13:{loader_path}']
    _log(f'Sahara: uploading loader via {com_port}')
    if log_cb:
        log_cb(f'Conectando ao dispositivo ({com_port})...')
    _SAHARA_TIMEOUT = 45
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=str(TOOLS_DIR), creationflags=_CREATE_NO_WINDOW)
        kill_timer = threading.Timer(_SAHARA_TIMEOUT, (lambda: proc.kill()))
        kill_timer.daemon = True
        kill_timer.start()
        output_lines = []
        success = False
        for line in iter(proc.stdout.readline, ''):
            stripped = line.rstrip()
            if stripped:
                output_lines.append(stripped)
                if log_cb:
                    _sanitize_and_log(stripped, log_cb)
                if 'successfully' in stripped.lower():
                    success = True
        kill_timer.cancel()
        proc.wait(timeout=10)
        _cleanup_port_trace(str(TOOLS_DIR))
        if proc.returncode == 0 or success:
            _log('Sahara: loader carregado com sucesso')
            return (True, 'Loader carregado')
        if proc.returncode and proc.returncode < 0:
            _log('Sahara: timeout ÔÇö processo encerrado')
            return (False, 'O dispositivo nao respondeu a tempo.\nReconecte em modo EDL e tente novamente.')
        err_msg = _extract_error(output_lines)
        _log(f'Sahara: falha ÔÇö {err_msg}')
        friendly = _sahara_friendly_error(output_lines)
        return False, friendly
    except subprocess.TimeoutExpired:
        proc.kill()
        _cleanup_port_trace(str(TOOLS_DIR))
        return (False, 'O dispositivo nao respondeu a tempo.\nReconecte e tente novamente.')
    except OSError:
        _cleanup_port_trace(str(TOOLS_DIR))
        return (False, 'Erro ao iniciar a comunicacao.\nVerifique a instalacao do programa.')
def get_gpt(com_port: str, memory: str, lun: int=0, output_dir: Optional[str]=None, log_cb: Optional[Callable[[str], None]]=None, extra_args: Optional[List[str]]=None) -> Tuple[bool, str]:
    '''
    Fase 2a ÔÇö Firehose: obter tabela GPT.
    Gera gpt_main{lun}.bin e gpt_backup{lun}.bin no output_dir.
    Retorna (sucesso, caminho_do_gpt_main).
    extra_args: flags adicionais para fh_loader (ex: --signeddigests=).
    '''
    if not FH_LOADER.exists():
        return (False, 'Componente nao encontrado.\nReinstale o programa ou entre em contato com o suporte.')
    if output_dir is None:
        output_dir = _edl_mkdtemp(prefix='gpt_')
    port_arg = f'\\\\.\\{com_port}'
    mem_arg = memory.lower()
    if mem_arg not in ('emmc', 'ufs', 'nand'):
        mem_arg = 'emmc'
    cmd = [str(FH_LOADER), f'--port={port_arg}', '--noprompt', f'--memoryname={mem_arg}', f'--getgptmainbackup={lun}', '--loglevel=1']
    if extra_args:
        cmd.extend(extra_args)
    _log(f'fh_loader: getgptmainbackup lun={lun} mem={mem_arg}')
    if log_cb:
        log_cb(f'Lendo tabela de particoes (LUN {lun})...')
    _FH_TIMEOUT = 60
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=output_dir, creationflags=_CREATE_NO_WINDOW)
        kill_timer = threading.Timer(_FH_TIMEOUT, (lambda: proc.kill()))
        kill_timer.daemon = True
        kill_timer.start()
        output_lines = []
        auth_needed = False
        for line in iter(proc.stdout.readline, ''):
            stripped = line.rstrip()
            if not stripped:
                continue
            output_lines.append(stripped)
            if log_cb:
                _sanitize_and_log(stripped, log_cb)
            ll = stripped.lower()
            if 'before authentication' not in ll:
                if not 'only nop and sig' in ll:
                    continue
            auth_needed = True
            proc.kill()
            break
        kill_timer.cancel()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)
        else:
            _AUTH_MSG = 'Este modelo requer autenticacao especial.\nSelecione o modelo correto na aba "Marca/Modelo"\npara que a autenticacao seja aplicada automaticamente.'
            if auth_needed:
                _log(f'GPT LUN {lun}: autenticacao necessaria ÔÇö abortando')
                return False, _AUTH_MSG
            gpt_file = os.path.join(output_dir, f'gpt_main{lun}.bin')
            if os.path.exists(gpt_file):
                _log(f'GPT obtido: {gpt_file} ({os.path.getsize(gpt_file)} bytes)')
                return True, gpt_file
            full_out = ' '.join(output_lines).lower()
            if 'before authentication' in full_out or 'only nop and sig' in full_out:
                return False, _AUTH_MSG
            err_msg = _extract_error(output_lines)
    except subprocess.TimeoutExpired:
        proc.kill()
        return (False, 'O dispositivo nao respondeu a tempo.\nReconecte e tente novamente.')
    except OSError:
        return (False, 'Erro ao iniciar a comunicacao.\nVerifique a instalacao do programa.')
    return False, err_msg or 'Falha ao ler particoes do dispositivo'
def get_gpt_via_read(com_port: str, memory: str, lun: int=0, output_dir: Optional[str]=None, log_cb: Optional[Callable[[str], None]]=None) -> Tuple[bool, str]:
    """
    Le GPT via --sendxml <read> em vez de --getgptmainbackup.
    Necessario para loaders VIP OPPO onde o configure automatico do
    fh_loader falha com 'Mode= Invalid value' e o getgptmainbackup
    retorna 0 bytes. O <read> direto funciona pois o device ja esta
    autenticado e em modo W.
    """
    if not FH_LOADER.exists():
        return (False, 'Componente nao encontrado.')
    if output_dir is None:
        output_dir = _edl_mkdtemp(prefix='gpt_')
    gpt_filename = f'gpt_main{lun}.bin'
    xml_content = f'<?xml version="1.0" encoding="UTF-8" ?><data><read SECTOR_SIZE_IN_BYTES="512" num_partition_sectors="34" start_sector="0" label="PrimaryGPT" filename="{gpt_filename}" physical_partition_number="{lun}" /></data>'
    xml_path = os.path.join(output_dir, f'read_gpt_{lun}.xml')
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    _log(f'fh_loader: read GPT via sendxml lun={lun}')
    if log_cb:
        log_cb(f'Lendo tabela de particoes (LUN {lun})...')
    ok, msg = exec_fh_sendxml(com_port, memory, xml_path, output_dir=output_dir, log_cb=log_cb, timeout=30)
    gpt_file = os.path.join(output_dir, gpt_filename)
    if os.path.exists(gpt_file) and os.path.getsize(gpt_file) > 0:
        _log(f'GPT obtido via read: {gpt_file} ({os.path.getsize(gpt_file)} bytes)')
        return True, gpt_file
    if ok:
        _log('GPT read OK mas arquivo vazio ou ausente')
        return (False, 'GPT lido mas arquivo vazio')
    return False, msg or 'Falha ao ler GPT via read'
def get_storage_info(com_port: str, memory: str, lun: int=0, log_cb: Optional[Callable[[str], None]]=None, extra_args: Optional[List[str]]=None) -> Tuple[bool, dict]:
    '''Obtem informacoes do storage (tamanho de setor, total blocks, etc).
    Detecta automaticamente se e UFS ou eMMC pela resposta do dispositivo.
    Para UFS, ajusta sector_size=4096 e detecta num_luns.
    extra_args: flags adicionais para fh_loader (ex: --signeddigests=).
    '''
    if not FH_LOADER.exists():
        return False, {}
    port_arg = f'\\\\.\\{com_port}'
    mem_arg = memory.lower()
    cmd = [str(FH_LOADER), f'--port={port_arg}', '--noprompt', f'--memoryname={mem_arg}', f'--getstorageinfo={lun}', '--loglevel=1']
    if extra_args:
        cmd.extend(extra_args)
    _log(f'fh_loader: getstorageinfo lun={lun} mem={mem_arg}')
    _FH_SI_TIMEOUT = 30
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=str(TOOLS_DIR), creationflags=_CREATE_NO_WINDOW)
        kill_timer = threading.Timer(_FH_SI_TIMEOUT, (lambda: proc.kill()))
        kill_timer.daemon = True
        kill_timer.start()
        info = {'sector_size': 512, 'total_blocks': 0, 'num_luns': 1, 'memory_type': mem_arg}
        output_lines = []
        _json_parsed = False
        for line in iter(proc.stdout.readline, ''):
            stripped = line.rstrip()
            if not stripped:
                continue
            output_lines.append(stripped)
            if log_cb:
                _sanitize_and_log(stripped, log_cb)
            ll = stripped.lower()
            json_m = re.search('\\{.*"storage_info"\\s*:\\s*\\{.*\\}', stripped)
            if json_m:
                if not _json_parsed:
                    pass
        try:
            import json as _json
            obj = _json.loads(json_m.group(0))
            si = obj.get('storage_info', {})
            bs = si.get('block_size') or si.get('page_size')
            if bs and int(bs) >= 512:
                info['sector_size'] = int(bs)
            tb = si.get('total_blocks')
            if tb:
                info['total_blocks'] = int(tb)
            np_ = si.get('num_physical')
            if np_:
                info['num_luns'] = int(np_)
            mt = si.get('mem_type', '').lower()
            if mt:
                info['memory_type'] = 'ufs' if 'ufs' in mt else 'emmc'
                if info['memory_type'] == 'ufs' and info['sector_size'] < 4096:
                    info['sector_size'] = 4096
            mi = si.get('manufacturer_id')
            if mi is not None:
                info['manufacturer_id'] = int(mi)
            sn = si.get('serial_num')
            if sn is not None:
                info['serial_num'] = int(sn)
            fw = si.get('fw_version')
            if fw:
                info['fw_version'] = str(fw)
            pn = si.get('prod_name')
            if pn:
                info['prod_name'] = str(pn)
            _json_parsed = True
        except Exception:
            pass
        else:
            _json_parsed = None
            kv = re.search("'(\\w+)\\s*=\\s*(\\d+)'", stripped)
            if kv:
                key = kv.group(1).lower()
                val = int(kv.group(2))
                if key == 'sector_size_in_bytes' and val >= 512:
                    if not _json_parsed:
                        info['sector_size'] = val
                elif key == 'num_partition_sectors':
                    if not _json_parsed:
                        info['total_blocks'] = val
                elif key == 'num_physical_partitions' and not _json_parsed:
                    info['num_luns'] = val
            if 'bnumberlu' in ll:
                m = re.search('bnumberlu\\D*(\\d+)', ll)
                if m:
                    info['num_luns'] = int(m.group(1))
            if 'ufs inquiry' in ll or 'ufs erase block' in ll or 'ufs total active' in ll:
                info['memory_type'] = 'ufs'
                if info['sector_size'] < 4096:
                    info['sector_size'] = 4096
            if 'ufs total active lu' in ll:
                m = re.search('(\\d+)', ll.split('lu')[-1])
                if m:
                    info['num_luns'] = int(m.group(1))
            if 'failed to open the sdcc' not in ll:
                pass
            _log('getstorageinfo: SDCC falhou ÔÇö provavel UFS')
            info['memory_type'] = 'ufs'
            info['sector_size'] = 4096
            kill_timer.cancel()
            proc.wait(timeout=10)
            _cleanup_port_trace(str(TOOLS_DIR))
            _log(f'Storage info: type={info['memory_type']} sector={info['sector_size']} luns={info['num_luns']}')
            if info['sector_size'] > 0:
                return True, info
    except subprocess.TimeoutExpired:
        proc.kill()
        _cleanup_port_trace(str(TOOLS_DIR))
        return False, {}
    except OSError:
        _cleanup_port_trace(str(TOOLS_DIR))
        return False, {}
    return False, info
def detect_storage_auto(com_port: str, log_cb: Optional[Callable[[str], None]]=None, memory_hint: Optional[str]=None, extra_fh_args: Optional[List[str]]=None) -> Tuple[str, int, int, dict]:
    """Detecta automaticamente tipo de storage, sector_size e num_luns.
    Se memory_hint for fornecido ('ufs' ou 'emmc'), come├ºa tentando com
    esse tipo ÔÇö evita interrogar o dispositivo com tipo errado (causa
    timeout e falhas de GPT). O hint geralmente vem do campo 'memoria'
    do loader no banco de dados.
    extra_fh_args: flags adicionais para fh_loader (ex: --signeddigests=).
    Retorna (memory_type, sector_size, num_luns, full_info).
    """
    hint = (memory_hint or '').lower().strip()
    start_with = hint if hint in ('ufs', 'emmc') else 'emmc'
    _log(f'detect_storage_auto: hint={hint or 'nenhum'} start_with={start_with}')
    ok, info = get_storage_info(com_port, start_with, 0, log_cb, extra_args=extra_fh_args)
    detected_type = info.get('memory_type', start_with)
    sector = info.get('sector_size', 4096 if start_with == 'ufs' else 512)
    num_luns = info.get('num_luns', 6 if start_with == 'ufs' else 1)
    needs_ufs_retry = detected_type == 'ufs' and start_with != 'ufs' or not ok and sector == 4096
    if needs_ufs_retry:
        _log('detect_storage_auto: UFS detectado, reconfigurando...')
        if log_cb:
            log_cb('Armazenamento UFS detectado ÔÇö ajustando configuracao...')
        ok2, info2 = get_storage_info(com_port, 'ufs', 0, log_cb, extra_args=extra_fh_args)
        if ok2:
            info = info2
            detected_type = 'ufs'
            sector = info2.get('sector_size', 4096)
            num_luns = info2.get('num_luns', 6)
        else:
            detected_type = 'ufs'
            sector = 4096
            num_luns = max(num_luns, 6)
    if start_with == 'ufs' and not ok:
        _log('detect_storage_auto: hint UFS falhou, tentando eMMC como fallback...')
        if log_cb:
            log_cb('Verificando tipo de armazenamento alternativo...')
        ok_fb, info_fb = get_storage_info(com_port, 'emmc', 0, log_cb, extra_args=extra_fh_args)
        if ok_fb:
            fb_type = info_fb.get('memory_type', 'emmc')
            if fb_type != 'ufs':
                info = info_fb
                detected_type = 'emmc'
                sector = info_fb.get('sector_size', 512)
                num_luns = info_fb.get('num_luns', 1)
                _log('detect_storage_auto: fallback eMMC confirmado')
            else:
                detected_type = 'ufs'
                sector = info_fb.get('sector_size', 4096)
                num_luns = info_fb.get('num_luns', 6)
    if detected_type == 'ufs' and num_luns < 2:
        num_luns = 6
    _log(f'detect_storage_auto: type={detected_type} sector={sector} luns={num_luns}')
    return detected_type, sector, num_luns, info
def get_all_gpt_ufs(com_port: str, num_luns: int=6, output_dir: Optional[str]=None, log_cb: Optional[Callable[[str], None]]=None, extra_args: Optional[List[str]]=None) -> List[Tuple[int, str]]:
    '''Le GPT de todas as LUNs UFS (0 a num_luns-1).
    Retorna lista de (lun, gpt_path) para LUNs que tem GPT valida.
    LUNs sem parti├º├úo (boot, RPMB) retornam vazio e s├úo ignoradas.
    extra_args: flags adicionais para fh_loader (ex: --signeddigests=).
    '''
    results = []
    for lun in range(num_luns):
        if log_cb:
            log_cb(f'Lendo particoes LUN {lun}/{num_luns - 1}...')
        ok, path = get_gpt(com_port, 'ufs', lun, output_dir, log_cb, extra_args=extra_args)
        if ok and os.path.exists(path) and os.path.getsize(path) > 0:
            _log(f'GPT LUN {lun}: {path} ({os.path.getsize(path)} bytes)')
            results.append((lun, path))
            continue
        if isinstance(path, str) and 'autenticacao' in path.lower():
            _log(f'GPT LUN {lun}: AUTH NECESSARIA ÔÇö abortando leitura')
            if log_cb:
                log_cb('Dispositivo requer autenticacao ÔÇö abortando leitura.')
            break
        _log(f'GPT LUN {lun}: sem particoes (normal para boot/RPMB)')
        continue
    return results
def generate_erase_xml(sector_size: int, start_sector: int, num_sectors: int, lun: int=0) -> str:
    '''Gera XML Firehose para erase de setores especificos.
    Tag em linha unica ÔÇö fh_loader v3 nao aceita newline dentro da tag.'''
    return f'<?xml version="1.0" ?>\n<data>\n  <erase SECTOR_SIZE_IN_BYTES="{sector_size}" num_partition_sectors="{num_sectors}" physical_partition_number="{lun}" start_sector="{start_sector}" />\n</data>'
def generate_read_xml(sector_size: int, start_sector: int, num_sectors: int, filename: str, lun: int=0) -> str:
    '''Gera XML Firehose para leitura (backup) de setores.
    Tag em linha unica ÔÇö fh_loader v3 nao aceita newline dentro da tag.'''
    return f'<?xml version="1.0" ?>\n<data>\n  <read SECTOR_SIZE_IN_BYTES="{sector_size}" filename="{filename}" num_partition_sectors="{num_sectors}" physical_partition_number="{lun}" start_sector="{start_sector}" />\n</data>'
def generate_write_xml(sector_size: int, start_sector: int, num_sectors: int, filename: str, lun: int=0) -> str:
    '''Gera XML Firehose para escrita (program) de setores.
    Tag em linha unica ÔÇö fh_loader v3 nao aceita newline dentro da tag.'''
    return f'<?xml version="1.0" ?>\n<data>\n  <program SECTOR_SIZE_IN_BYTES="{sector_size}" filename="{filename}" num_partition_sectors="{num_sectors}" physical_partition_number="{lun}" start_sector="{start_sector}" />\n</data>'
def generate_patch_xml(sector_size: int, start_sector: int, num_sectors: int, lun: int=0, full_zero: bool=False) -> str:
    '''
Gera XML Firehose com comandos <patch> para zerar uma particao
byte a byte.
full_zero=False (Samsung mode ÔÇö PCAP SamFW A235M):
  Cada <patch> escreve 4 bytes de zero com stride 8 (50% cobertura).
  Suficiente para invalidar metadados FRP em Samsung.
full_zero=True (OPPO/Honor/generico):
  Cada <patch> escreve 8 bytes de zero com stride 8 (100% cobertura).
  Necessario para OPPO/Honor onde FRP requer zeragem total.
'''
    lines = ['<?xml version="1.0" ?>']
    lines.append('<data>')
    if full_zero:
        patch_size = 8
        patch_value = '0000000000000000'
    else:
        patch_size = 4
        patch_value = '00000000'
    for sector_idx in range(num_sectors):
        current_sector = start_sector + sector_idx
        for offset in range(0, sector_size, 8):
            lines.append(f'  <patch SECTOR_SIZE_IN_BYTES="{sector_size}" byte_offset="{offset}" filename="DISK" physical_partition_number="{lun}" size_in_bytes="{patch_size}" start_sector="{current_sector}" value="{patch_value}" what="Update" />')
    lines.append('</data>')
    return '\n'.join(lines)
def program_partition(com_port: str, memory: str, partition: dict, sector_size: int, lun: int=0, log_cb: Optional[Callable[[str], None]]=None) -> Tuple[bool, str]:
    '''
    Escreve zeros em uma particao via Firehose <program> (sendimage).
    Alternativa ao erase_partition para Samsung, onde <erase> e bloqueado
    mas <program> com payload de zeros e aceito.
    Cria um arquivo temporario preenchido com zeros do tamanho exato
    da particao e envia via fh_loader --sendimage.
    '''
    name = partition.get('name', '')
    if is_critical(name):
        msg = f'BLOQUEADO: particao "{name}" e critica e nao pode ser gravada'
        _log(msg)
        return False, msg
    start = partition.get('start_lba', 0)
    count = partition.get('num_sectors', 0)
    if start == 0 or count == 0:
        return (False, 'Dados de setor invalidos')
    total_bytes = count * sector_size
    _MAX_PROGRAM_BYTES = 52428800
    if total_bytes > _MAX_PROGRAM_BYTES:
        _log(f'Program: {name} muito grande ({total_bytes} bytes > {_MAX_PROGRAM_BYTES}). Use erase_partition para particoes grandes.')
        return (False, 'NAK_PROGRAM')
    _log(f'Program (zeros): {name} LBA {start}-{start + count - 1} ({count} setores, {total_bytes} bytes)')
    if log_cb:
        log_cb(f'Gravando zeros em {name} ({count} setores)...')
    tmp_dir = _edl_mkdtemp(prefix='prog_')
    zero_file = os.path.join(tmp_dir, 'zeros.bin')
    try:
        _CHUNK_SIZE = 1048576
        with open(zero_file, 'wb') as f:
            remaining = total_bytes
            while remaining > 0:
                chunk = min(remaining, _CHUNK_SIZE)
                f.write(b'\x00' * chunk)
                remaining -= chunk
    except Exception as e:
        _log(f'Erro ao criar arquivo de zeros: {e}')
        return (False, 'Erro ao preparar dados para gravacao')
    try:
        pass
    except Exception as e:
        _log(f'Erro ao criar arquivo de zeros: {e}')
        return (False, 'Erro ao preparar dados para gravacao')
    if not FH_LOADER.exists():
        return (False, 'Componente nao encontrado.\nReinstale o programa.')
    port_arg = f'\\\\.\\{com_port}'
    mem_arg = memory.lower()
    cmd = [str(FH_LOADER), f'--port={port_arg}', '--noprompt', f'--memoryname={mem_arg}', f'--sendimage={zero_file}', f'--start_sector={start}', f'--lun={lun}', '--showpercentagecomplete', '--zlpawarehost=1', '--loglevel=1']
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=tmp_dir, creationflags=_CREATE_NO_WINDOW)
        output_lines = []
        success = False
        nak_received = False
        for line in iter(proc.stdout.readline, ''):
            stripped = line.rstrip()
            if stripped:
                output_lines.append(stripped)
                if log_cb:
                    _sanitize_and_log(stripped, log_cb)
                ll = stripped.lower()
                if 'successfully' in ll:
                    success = True
                if 'nak' in ll or 'not allowed' in ll or 'readonly' in ll:
                    nak_received = True
        proc.wait(timeout=120)
        _cleanup_port_trace(tmp_dir)
        if proc.returncode == 0 or success:
            _log(f'Program (zeros) concluido: {name}')
            try:
                os.remove(zero_file)
                os.rmdir(tmp_dir)
            except OSError:
                pass
            return (True, 'Particao zerada com sucesso (program)')
        if nak_received:
            _log(f'Program NAK para {name} ÔÇö sera necessario SMART mode')
        try:
            os.remove(zero_file)
            os.rmdir(tmp_dir)
        except OSError:
            return (False, 'NAK_PROGRAM')
        else:
            return (False, 'NAK_PROGRAM')
    except subprocess.TimeoutExpired:
        proc.kill()
        _cleanup_port_trace(tmp_dir)
    try:
        os.remove(zero_file)
        os.rmdir(tmp_dir)
    except OSError:
        return
    return False, err_msg or 'Falha na gravacao (program)'
def patch_partition(com_port: str, memory: str, partition: dict, sector_size: int, lun: int=0, max_sectors: int=4, log_cb: Optional[Callable[[str], None]]=None, progress_cb: Optional[Callable[[int], None]]=None, extra_args: Optional[List[str]]=None, full_zero: bool=True) -> Tuple[bool, str]:
    '''
Zera uma particao via Firehose <patch>.
Envia uma sequencia de <patch> commands que escrevem zeros byte a byte
em cada setor da particao.
max_sectors limita quantos setores sao patcheados para evitar
timeout em particoes muito grandes. Para FRP (persistent),
zerar os primeiros 4 setores e suficiente para invalidar
a estrutura de metadados.
full_zero=True (padrao): 8 bytes por patch, 100% cobertura.
  Funciona para OPPO, Honor, e qualquer marca.
full_zero=False: 4 bytes por patch, 50% cobertura (modo Samsung PCAP).
'''
    name = partition.get('name', '')
    if is_critical(name):
        msg = f'BLOQUEADO: particao "{name}" e critica'
        _log(msg)
        return False, msg
    start = partition.get('start_lba', 0)
    count = partition.get('num_sectors', 0)
    if start == 0 or count == 0:
        return (False, 'Dados de setor invalidos')
    sectors_to_patch = min(count, max_sectors)
    patches_per_sector = sector_size // 8
    total_patches = sectors_to_patch * patches_per_sector
    _log(f'Patch: {name} LBA {start} ÔÇö {sectors_to_patch} setores, {total_patches} patches (full_zero={full_zero})')
    if log_cb:
        log_cb(f'Zerando {name} ({sectors_to_patch} setores)...')
    xml_content = generate_patch_xml(sector_size, start, sectors_to_patch, lun, full_zero=full_zero)
    tmp_dir = _edl_mkdtemp(prefix='patch_')
    xml_path = os.path.join(tmp_dir, 'smart_patch.xml')
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    patch_count = [0]
    last_pct = [0]
    def _on_raw_patch_line(raw_line: str):
        if 'handler for patch' in raw_line.lower():
            patch_count[0] += 1
            if progress_cb:
                if total_patches > 0:
                    pct = min(95, int(patch_count[0] * 100 / total_patches))
                    if pct > last_pct[0]:
                        last_pct[0] = pct
                        progress_cb(pct)
                        if log_cb:
                            if pct % 20 == 0:
                                log_cb(f'SMART mode: {pct}% concluido...')
    ok, msg = exec_fh_sendxml(com_port, memory, xml_path, extra_args=extra_args, output_dir=tmp_dir, log_cb=log_cb, timeout=300, on_raw_line=_on_raw_patch_line)
    try:
        os.remove(xml_path)
        os.rmdir(tmp_dir)
    except OSError:
        pass
    if ok:
        _log(f'SMART mode concluido: {name}')
        if progress_cb:
            progress_cb(100)
        return True, f'Particao {name} zerada via SMART mode'
    return False, msg
def exec_fh_sendxml(com_port: str, memory: str, xml_path: str, extra_args: Optional[List[str]]=None, output_dir: Optional[str]=None, log_cb: Optional[Callable[[str], None]]=None, timeout: int=120, on_raw_line: Optional[Callable[[str], None]]=None) -> Tuple[bool, str]:
    '''
    Executa fh_loader com --sendxml.
    Usado para erase, read (com --convertprogram2read), e write.
    on_raw_line: callback chamado com CADA linha bruta antes de filtrar.
    '''
    if not FH_LOADER.exists():
        return (False, 'Componente nao encontrado.\nReinstale o programa ou entre em contato com o suporte.')
    port_arg = f'\\\\.\\{com_port}'
    mem_arg = memory.lower()
    cwd = output_dir or str(TOOLS_DIR)
    cmd = [str(FH_LOADER), f'--port={port_arg}', '--noprompt', f'--memoryname={mem_arg}', f'--sendxml={xml_path}', '--showpercentagecomplete', '--zlpawarehost=1', '--loglevel=1']
    if extra_args:
        cmd.extend(extra_args)
    _log(f'fh_loader: sendxml {os.path.basename(xml_path)}')
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=cwd, creationflags=_CREATE_NO_WINDOW)
        output_lines = []
        success = False
        for line in iter(proc.stdout.readline, ''):
            stripped = line.rstrip()
            if stripped:
                output_lines.append(stripped)
                if on_raw_line:
                    on_raw_line(stripped)
                if log_cb:
                    _sanitize_and_log(stripped, log_cb)
                ll = stripped.lower()
                if 'successfully' in ll:
                    success = True
        proc.wait(timeout=timeout)
        _cleanup_port_trace(cwd)
        if proc.returncode == 0 or success:
            return (True, 'Operacao concluida')
        err_msg = _extract_error(output_lines)
        return False, err_msg or 'Falha na operacao'
    except subprocess.TimeoutExpired:
        proc.kill()
        _cleanup_port_trace(cwd)
        return False, f'O dispositivo nao respondeu a tempo ({timeout}s).\nReconecte e tente novamente.'
    except OSError:
        _cleanup_port_trace(cwd)
        return (False, 'Erro ao iniciar a comunicacao.\nVerifique a instalacao do programa.')
def erase_partition(com_port: str, memory: str, partition: dict, sector_size: int, lun: int=0, log_cb: Optional[Callable[[str], None]]=None, extra_args: Optional[List[str]]=None) -> Tuple[bool, str]:
    '''
    Apaga uma particao especifica via XML com setores exatos.
    SEGURAN├çA: Valida contra blacklist antes de executar.
    extra_args: flags adicionais para fh_loader (ex: --signeddigests=).
    '''
    name = partition.get('name', '')
    if is_critical(name):
        msg = f'BLOQUEADO: particao "{name}" e critica e nao pode ser apagada'
        _log(msg)
        return False, msg
    start = partition.get('start_lba', 0)
    count = partition.get('num_sectors', 0)
    if start == 0 or count == 0:
        return (False, 'Dados de setor invalidos')
    xml_content = generate_erase_xml(sector_size, start, count, lun)
    tmp_dir = _edl_mkdtemp(prefix='erase_')
    xml_path = os.path.join(tmp_dir, 'erase_op.xml')
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    _log(f'Erase: {name} LBA {start}-{start + count - 1} ({count} setores)')
    if log_cb:
        log_cb(f'Apagando particao {name}...')
    ok, msg = exec_fh_sendxml(com_port, memory, xml_path, extra_args=extra_args, output_dir=tmp_dir, log_cb=log_cb)
    try:
        os.remove(xml_path)
        os.rmdir(tmp_dir)
    except OSError:
        pass
    return ok, msg
def read_partition(com_port: str, memory: str, partition: dict, sector_size: int, output_path: str, lun: int=0, log_cb: Optional[Callable[[str], None]]=None) -> Tuple[bool, str]:
    '''
    Le (backup) uma particao para arquivo local via fh_loader --sendimage.
    Usa --convertprogram2read + --sendimage + --start_sector + --num_sectors
    para leitura direta sem XML (mais confiavel que <read> via --sendxml,
    pois fh_loader nao reconhece a tag <read> ÔÇö apenas <program>).
    '''
    if not FH_LOADER.exists():
        return (False, 'Componente nao encontrado.\nReinstale o programa ou entre em contato com o suporte.')
    name = partition.get('name', '')
    start = partition.get('start_lba', 0)
    count = partition.get('num_sectors', 0)
    if start == 0 or count == 0:
        return (False, 'Dados de setor invalidos')
    out_dir = os.path.dirname(output_path) or '.'
    out_file = os.path.basename(output_path)
    port_arg = f'\\\\.\\{com_port}'
    mem_arg = memory.lower()
    cmd = [str(FH_LOADER), f'--port={port_arg}', '--noprompt', f'--memoryname={mem_arg}', '--convertprogram2read', f'--sendimage={out_file}', f'--start_sector={start}', f'--lun={lun}', f'--num_sectors={count}', '--showpercentagecomplete', '--zlpawarehost=1', '--loglevel=1']
    _log(f'Read: {name} ÔåÆ {out_file} ({count} setores, LBA {start})')
    if log_cb:
        log_cb(f'Lendo particao {name}...')
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=out_dir, creationflags=_CREATE_NO_WINDOW)
        output_lines = []
        success = False
        for line in iter(proc.stdout.readline, ''):
            stripped = line.rstrip()
            if stripped:
                output_lines.append(stripped)
                if log_cb:
                    _sanitize_and_log(stripped, log_cb)
                if 'successfully' in stripped.lower():
                    success = True
        proc.wait(timeout=600)
        _cleanup_port_trace(out_dir)
        if (proc.returncode == 0 or success) and os.path.exists(output_path):
            size = os.path.getsize(output_path)
            _log(f'Read concluido: {output_path} ({size} bytes)')
            return True, output_path
        if proc.returncode == 0 or success:
            candidates = [os.path.join(out_dir, out_file), os.path.join(out_dir, f'{out_file}.bin')]
            for c in candidates:
                if not os.path.exists(c):
                    continue
                if c != output_path:
                    import shutil
                    shutil.move(c, output_path)
                    return True, output_path
            return (False, 'O backup nao foi gerado.\nO dispositivo pode ter desconectado durante a operacao.')
        err_msg = _extract_error(output_lines)
        return False, err_msg or 'Falha ao ler particao'
    except subprocess.TimeoutExpired:
        proc.kill()
        _cleanup_port_trace(out_dir)
        return (False, 'O dispositivo nao respondeu a tempo.\nReconecte e tente novamente.')
    except OSError:
        _cleanup_port_trace(out_dir)
        return (False, 'Erro ao iniciar a comunicacao.\nVerifique a instalacao do programa.')
_READ_CHUNK_SECTORS = 256
def read_partition_via_sendxml(com_port: str, memory: str, partition: dict, sector_size: int, output_path: str, lun: int=0, log_cb: Optional[Callable[[str], None]]=None) -> Tuple[bool, str]:
    '''
    Le (backup) uma particao via --sendxml <read>.
    Necessario para loaders VIP OPPO onde --convertprogram2read falha
    porque o <configure> automatico do fh_loader gera erro.
    Particoes grandes (>256 setores) sao lidas em chunks de 256 setores
    (128 KB cada), validado via PCAP Pandora + testes OPPO A3X/A40.
    '''
    if not FH_LOADER.exists():
        return (False, 'Componente nao encontrado.')
    name = partition.get('name', '')
    start = partition.get('start_lba', 0)
    count = partition.get('num_sectors', 0)
    if start == 0 or count == 0:
        return (False, 'Dados de setor invalidos')
    out_dir = os.path.dirname(output_path) or '.'
    out_file = os.path.basename(output_path)
    if count <= _READ_CHUNK_SECTORS:
        return _read_single(com_port, memory, name, start, count, sector_size, lun, out_dir, out_file, output_path, log_cb)
    return _read_chunked(com_port, memory, name, start, count, sector_size, lun, out_dir, out_file, output_path, log_cb)
def _read_single(com_port: str, memory: str, name: str, start: int, count: int, sector_size: int, lun: int, out_dir: str, out_file: str, output_path: str, log_cb: Optional[Callable[[str], None]]) -> Tuple[bool, str]:
    '''Leitura direta (particoes pequenas <= 256 setores).'''
    xml_content = f'<?xml version="1.0" encoding="UTF-8" ?><data><read SECTOR_SIZE_IN_BYTES="{sector_size}" num_partition_sectors="{count}" start_sector="{start}" label="{name}" filename="{out_file}" physical_partition_number="{lun}" /></data>'
    xml_path = os.path.join(out_dir, f'read_{name}.xml')
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    _log(f'Read (sendxml): {name} ÔåÆ {out_file} ({count} setores, LBA {start})')
    if log_cb:
        log_cb(f'Lendo particao {name}...')
    ok, msg = exec_fh_sendxml(com_port, memory, xml_path, output_dir=out_dir, log_cb=log_cb, timeout=600)
    try:
        os.remove(xml_path)
    except OSError:
        pass
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        size = os.path.getsize(output_path)
        _log(f'Read concluido: {output_path} ({size} bytes)')
        return True, output_path
    if ok:
        return (False, 'Read OK mas arquivo vazio')
    return False, msg or 'Falha ao ler particao'
def _detect_chunk_success(output: str, chunk_path: str) -> bool:
    '''Detecta sucesso real de leitura de chunk (replica logica do tester validado).
    Ignora erros nao-fatais do auto-configure do fh_loader (Mode= Invalid value)
    e verifica indicadores reais de sucesso.
    '''
    out_lower = output.lower()
    has_real_error = 'error: failed to open' in out_lower or 'error: please see log' in out_lower or 'error: read failed' in out_lower or 'nand_error' in out_lower
    has_nak = 'nak' in out_lower and 'nand' not in out_lower
    if has_real_error or has_nak:
        return False
    has_success_banner = '======= success =======' in out_lower
    has_all_finished = 'all finished successfully' in out_lower
    has_handler_read = 'calling handler for read' in out_lower
    file_ok = os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 0
    if has_success_banner and has_handler_read:
        if has_all_finished or file_ok:
            return True
    if file_ok and has_all_finished:
        return True
    return False
def _read_chunked(com_port: str, memory: str, name: str, start: int, count: int, sector_size: int, lun: int, out_dir: str, out_file: str, output_path: str, log_cb: Optional[Callable[[str], None]]) -> Tuple[bool, str]:
    '''Leitura em chunks de 256 setores (particoes grandes ÔÇö fluxo Pandora).
    Usa chamada direta ao fh_loader (sem exec_fh_sendxml) replicando
    exatamente o fluxo validado no edl_vip_tester.py:
    - Argumentos minimos (sem --showpercentagecomplete, sem --loglevel)
    - Modo binario no stdout (sem text=True)
    - proc.communicate() para captura completa
    - _detect_chunk_success para ignorar erros do auto-configure
    '''
    total_chunks = (count + _READ_CHUNK_SECTORS - 1) // _READ_CHUNK_SECTORS
    total_mb = count * sector_size / 1048576
    _log(f'Read chunked: {name} ÔÇö {total_mb:.1f} MB, {total_chunks} chunks de {_READ_CHUNK_SECTORS} setores')
    if log_cb:
        log_cb(f'Lendo {name} ({total_mb:.1f} MB em {total_chunks} partes)...')
    chunk_dir = _edl_mkdtemp(prefix=f'read_{name}_')
    port_arg = f'\\\\.\\{com_port}'
    mem_arg = memory.lower()
    if mem_arg not in ('emmc', 'ufs'):
        mem_arg = 'emmc'
    success_count = 0
    consecutive_fails = 0
    try:
        for i in range(total_chunks):
            chunk_start = start + i * _READ_CHUNK_SECTORS
            remaining = count - i * _READ_CHUNK_SECTORS
            this_chunk = min(_READ_CHUNK_SECTORS, remaining)
            chunk_filename = f'chunk_{i:06d}.bin'
            xml_content = f'<?xml version="1.0" encoding="UTF-8" ?><data><read SECTOR_SIZE_IN_BYTES="{sector_size}" num_partition_sectors="{this_chunk}" start_sector="{chunk_start}" label="PrimaryGPT" filename="{chunk_filename}" physical_partition_number="{lun}" /></data>'
            xml_path = os.path.join(chunk_dir, 'read_chunk.xml')
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            if i % 100 == 0 or i == total_chunks - 1:
                pct = int(i / total_chunks * 100)
                if log_cb:
                    log_cb(f'Lendo {name}: {pct}% ({i + 1}/{total_chunks})')
            cmd = [str(FH_LOADER), f'--port={port_arg}', f'--sendxml={xml_path}', '--noprompt', '--zlpawarehost=1', f'--memoryname={mem_arg}']
            out_text = ''
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=chunk_dir, creationflags=_CREATE_NO_WINDOW)
            kill_timer = threading.Timer(120, proc.kill)
            kill_timer.daemon = True
            kill_timer.start()
            stdout_bytes, _ = proc.communicate()
            kill_timer.cancel()
            out_text = stdout_bytes.decode('utf-8', errors='replace')
        except Exception as e:
            _log(f'Read chunk {i + 1} excecao: {e}')
        else:
            chunk_path = os.path.join(chunk_dir, chunk_filename)
            chunk_ok = _detect_chunk_success(out_text, chunk_path)
            if chunk_ok:
                success_count += 1
                consecutive_fails = 0
            consecutive_fails += 1
            _log(f'Read chunk {i + 1}/{total_chunks} falhou (setor {chunk_start})')
            if not consecutive_fails >= 3:
                pass
            _log('3+ falhas consecutivas em chunks ÔÇö abortando')
            if success_count == 0:
                pass
    except OSError:
        pass
    try:
        os.makedirs(out_dir, exist_ok=True)
        total_written = success_count + consecutive_fails
        with open(output_path, 'wb') as fout:
            for i in range(total_written):
                cp = os.path.join(chunk_dir, f'chunk_{i:06d}.bin')
                if not os.path.exists(cp):
                    continue
                if os.path.getsize(cp) > 0:
                    with open(cp, 'rb') as fin:
                        fout.write(fin.read())
    except OSError:
        pass
    try:
        size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        _log(f'Read chunked concluido: {output_path} ({size} bytes, {success_count}/{total_chunks} chunks)')
        if consecutive_fails == 0 and success_count == total_chunks:
            if log_cb:
                log_cb(f'Leitura de {name} concluida ({size // 1024} KB)')
            for f in os.listdir(chunk_dir):
                try:
                    os.remove(os.path.join(chunk_dir, f))
                except OSError:
                    continue
            try:
                os.rmdir(chunk_dir)
            except OSError:
                pass
            return
    except OSError:
        pass
    try:
        if log_cb:
            log_cb(f'Leitura parcial de {name} ({success_count}/{total_chunks} chunks)')
    except OSError:
        pass
    for f in os.listdir(chunk_dir):
        try:
            os.remove(os.path.join(chunk_dir, f))
        except OSError:
            continue
    try:
        os.rmdir(chunk_dir)
    except OSError:
        return
def write_partition(com_port: str, memory: str, partition: dict, sector_size: int, image_path: str, lun: int=0, log_cb: Optional[Callable[[str], None]]=None) -> Tuple[bool, str]:
    '''
    Escreve (grava) imagem em uma particao via fh_loader --sendimage.
    Usado para restaurar backups. NAO permite escrever em particoes criticas.
    '''
    name = partition.get('name', '')
    if is_critical(name):
        msg = f'BLOQUEADO: particao "{name}" e critica e nao pode ser gravada'
        _log(msg)
        return False, msg
    if not os.path.exists(image_path):
        return (False, 'Arquivo de imagem nao encontrado')
    start = partition.get('start_lba', 0)
    if start == 0:
        return (False, 'Setor inicial invalido')
    if not FH_LOADER.exists():
        return (False, 'Componente nao encontrado.\nReinstale o programa ou entre em contato com o suporte.')
    port_arg = f'\\\\.\\{com_port}'
    mem_arg = memory.lower()
    cmd = [str(FH_LOADER), f'--port={port_arg}', '--noprompt', f'--memoryname={mem_arg}', f'--sendimage={image_path}', f'--start_sector={start}', f'--lun={lun}', '--showpercentagecomplete', '--zlpawarehost=1', '--loglevel=1']
    _log(f'Write: {name} ÔåÉ {os.path.basename(image_path)} (LBA {start})')
    if log_cb:
        log_cb(f'Gravando particao {name}...')
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=str(TOOLS_DIR), creationflags=_CREATE_NO_WINDOW)
        output_lines = []
        success = False
        for line in iter(proc.stdout.readline, ''):
            stripped = line.rstrip()
            if stripped:
                output_lines.append(stripped)
                if log_cb:
                    _sanitize_and_log(stripped, log_cb)
                if 'successfully' in stripped.lower():
                    success = True
        proc.wait(timeout=600)
        _cleanup_port_trace(str(TOOLS_DIR))
        if proc.returncode == 0 or success:
            _log(f'Write concluido: {name}')
            return (True, 'Particao gravada com sucesso')
        err_msg = _extract_error(output_lines)
        return False, err_msg or 'Falha ao gravar particao'
    except subprocess.TimeoutExpired:
        proc.kill()
        _cleanup_port_trace(str(TOOLS_DIR))
        return (False, 'O dispositivo nao respondeu a tempo.\nReconecte e tente novamente.')
    except OSError:
        _cleanup_port_trace(str(TOOLS_DIR))
        return (False, 'Erro ao iniciar a comunicacao.\nVerifique a instalacao do programa.')
def reset_device(com_port: str, memory: str, log_cb: Optional[Callable[[str], None]]=None, extra_args: Optional[List[str]]=None) -> Tuple[bool, str]:
    '''
    Reinicia o dispositivo via XML <power value="reset"/>.
    Usa --sendxml com power ao inves de --reset direto, que e mais
    seguro e controlado (nao interfere com GPT).
    extra_args: flags adicionais para fh_loader (ex: --signeddigests=).
    '''
    if not FH_LOADER.exists():
        return (False, 'Componente nao encontrado.\nReinstale o programa ou entre em contato com o suporte.')
    _log('fh_loader: power reset via XML')
    if log_cb:
        log_cb('Reiniciando dispositivo...')
    xml_content = '<?xml version="1.0" ?>\n<data>\n  <power value="reset" />\n</data>'
    tmp_dir = _edl_mkdtemp(prefix='reset_')
    xml_path = os.path.join(tmp_dir, 'power_reset.xml')
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    ok, msg = exec_fh_sendxml(com_port, memory, xml_path, extra_args=extra_args, output_dir=tmp_dir, log_cb=log_cb, timeout=30)
    try:
        os.remove(xml_path)
        os.rmdir(tmp_dir)
    except OSError:
        pass
    return ok, 'Dispositivo reiniciado' if ok else msg
_LOG_BLOCK_PATTERNS = ('System.', 'at ', 'Exception:', '.dll', 'StackTrace', '\\AppData\\', '\\Users\\', '\\Temp\\', 'QSAHARASERVER CALLED', 'FH_LOADER WAS CALLED', 'Current working dir', 'fh_loader.exe --', 'QSaharaServer.exe', 'Sahara mappings:', '.mbn', 'amss.mbn', 'apps.mbn', 'dsp1.mbn', 'dsp2.mbn', 'dsp3.mbn', 'dbl.mbn', 'osbl.mbn', 'sbl1.mbn', 'sbl2.mbn', 'rpm.mbn', 'tz.mbn', 'mba.mbn', 'wdt.mbn', 'acdb.mbn', 'efs1.mbn', 'efs2.mbn', 'efs3.mbn', 'Requested ID 13', 'EVENT: STATE', 'EVENT: SENDING', 'EVENT: RECEIVED', 'SAHARA_WAIT', 'SAHARA_READ_DATA', 'SAHARA_HELLO', 'SAHARA_END_IMAGE', 'SAHARA_DONE', 'Sahara protocol completed', 'Successfully uploaded', 'bytes transferred in', 'port_trace.txt', 'fopen(', 'AccessMode=', 'Calling handler for', 'handler for configure', 'handler for patch', 'handler for program', 'handler for read', 'handler for power', 'Sorting TAGS', 'Sending <configure>', 'Sending <power>', 'MaxPayloadSize', 'Unrecognized tag', 'Showing network', 'network mappings', 'loglevel=', 'semi-verbose', 'seconds to open port', 'User wants to talk to port', 'Output Dir Already', 'Files used and their paths', 'NOTE: There were', 'deprecated and scheduled', "Couldn't find the file", 'In handleRead(', 'Looking for file', 'handleRead(', 'Writing log, might', '__      __', '\\ \\ /\\', '\\ V  V', '\\_/\\_/', '__/ |', '|___/', '| |__', '|  __|', '|  ___', '\\____', '_____', '(done)', '| |', '__|', 'Binary build date:', 'Base Version:', 'Incremental Build', 'logbuf@', 'smart_erase:', 'detect_storage_auto:', 'fh_loader:', 'Program (zeros)', 'Program NAK', 'SMART mode:', 'SMART mode concluido', 'GPT obtido:', 'GPT LUN', 'Storage info:', 'Sahara: uploading', 'Sahara: loader', 'fh_loader: sendxml', 'fh_loader: power', 'fh_loader: getgptmainbackup', 'fh_loader: getstorageinfo', 'Overall to target', 'percent files transferred', 'Total to be tansferd', 'TARGET SAID:', 'Storage type set to', '{ERROR:', 'Please see log', 'start_sector=', 'num_sectors=', 'not allowed', 'through EDL Flash', 'gpt_main', 'gpt_backup', '<read>', 'NUM_DISK_SECTORS', 'Time measurement too small', 'Took ', '0.0 seconds', 'Finished sector address', 'num_partition_sectors', 'SECTOR_SIZE_IN_BYTES', 'num_physical_partitions', 'Product name=', 'storage_info', 'total_blocks', 'block_size', 'manufacturer_id', 'UFS ', 'eMMC', 'fInitialized', 'Current LUN', 'Active LU', 'wManufacturerID', 'Boot Partition', 'Raw Device', 'Min Block Size', 'Erase Block Size', 'Allocation Unit', 'RPMB ReadWrite', 'Logical Block', 'Provisioning Type', 'LU Write Protect', 'Boot LUN', 'Memory Type', 'LU Total Blocks', 'Supported Memory', 'Enhanced', 'MaxNAllocU', 'CapAdjFac', 'LUN Enable', 'bConfigDescrLock', 'iManufacturer', 'iProductName', 'iSerialNumber', 'iOemID', 'Inquiry Command', 'Supported Functions', 'End of supported functions', 'MFR_ID=', 'OEM_ID=', 'Chip serial num')
def _sanitize_and_log(line: str, log_cb: Callable[[str], None]):
    '''Filtra informa├º├Áes t├®cnicas internas antes de enviar ao log do usu├írio.'''
    stripped = line.strip()
    if not stripped:
        return
    if any((p in stripped for p in _LOG_BLOCK_PATTERNS)):
        return
    stripped = re.sub('[A-Za-z]:\\\\[^\\s]+\\\\([^\\s\\\\]+)', '\\1', stripped)
    log_cb(stripped)
def _sahara_friendly_error(lines: List[str]) -> str:
    '''Traduz erros internos para mensagens amigaveis ao usuario.'''
    full = '\n'.join(lines).lower()
    if 'reading from com port' in full or 'sahara protocol error' in full:
        had_read_data = 'sahara_read_data' in full
        if had_read_data:
            return 'Modelo nao suportado ou variante incompativel.\n\nO dispositivo rejeitou a comunicacao.\nVerifique se o modelo esta correto e tente novamente.'
        return 'Falha na comunicacao com o dispositivo.\n\nVerifique o cabo USB e a conexao.\nReconecte o aparelho em modo EDL e tente novamente.'
    if 'invalid' in full and 'hash' in full:
        return 'Modelo nao suportado.\n\nEste dispositivo nao e compativel com os dados disponiveis.\nVerifique se o modelo esta correto.'
    if 'timeout' in full or 'timed out' in full:
        return 'O dispositivo nao respondeu a tempo.\n\nReconecte o aparelho em modo EDL e tente novamente.\nUse um cabo USB direto (sem hub).'
    if 'uploading' in full and 'failed' in full:
        return 'Falha na comunicacao com o dispositivo.\n\nO modelo pode nao ser suportado nesta versao.\nReconecte o aparelho e tente novamente.'
    return 'Falha na comunicacao com o dispositivo.\nReconecte e tente novamente.'
def _extract_error(lines: List[str]) -> str:
    '''Extrai mensagem de erro relevante da saida do processo.'''
    for line in reversed(lines):
        ll = line.lower()
        if any((k in ll for k in ('error', 'fail', 'unable', 'cannot'))):
            return re.sub('[A-Za-z]:\\\\[^\\s]+', '...', line)
    return ''
# WARNING: Decompyle incomplete
