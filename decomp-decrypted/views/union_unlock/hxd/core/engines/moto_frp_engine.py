import logging
import os
import tempfile
import time
from typing import Callable
from .moto_frp_sync import MotoFrpSync
_logger = logging.getLogger(__name__)
def _get_adb():
    from app.utils.adb_manager import ADBManager
    return ADBManager()
def _fb_cmd(adb, cmd: str, timeout: int=30) -> tuple:
    _adb_logger = logging.getLogger('app.utils.adb_manager')
    _prev_level = _adb_logger.level
    _adb_logger.setLevel(logging.CRITICAL)
    try:
        out = adb.execute_fastboot_command(cmd, timeout=timeout)
    except Exception:
        _adb_logger.setLevel(_prev_level)
        return (False, '')
    finally:
        _adb_logger.setLevel(_prev_level)
    return True, (out or '').strip()
def _getvar(adb, var: str) -> str:
    ok, out = _fb_cmd(adb, f'getvar {var}')
    if not ok:
        return ''
    for line in out.splitlines():
        if f'{var}:' in line:
            val = line.split(f'{var}:', 1)[1].strip()
            if 'FAILED' in val or 'error' in val.lower():
                return ''
            return val
    return ''
def _get_usb_serial(adb) -> str:
    try:
        ok, out = _fb_cmd(adb, 'devices')
        if ok and out:
            for line in out.splitlines():
                parts = line.split()
                if not len(parts) >= 2:
                    continue
                if 'fastboot' in parts[1].lower():
                    s = parts[0].strip()
                    if not s:
                        continue
                    if not '?' not in s:
                        continue
                    return s
    except Exception:
        pass
    return ''
def _device_present(adb, expected_serial: str='') -> bool:
    try:
        serial = _get_usb_serial(adb)
        if not serial:
            return False
        if expected_serial and serial != expected_serial:
            return False
    except Exception:
        return False
    return True
def _wait_for_device(adb, max_wait: int=60, interval: int=5, expected_serial: str='') -> bool:
    for _ in range(max_wait // interval):
        time.sleep(interval)
        if _device_present(adb, expected_serial):
            return True
    return False
_SYNC_DEBOUNCE_S = 120
_BL_PREFIX_MAP = {'W': 16, 'V': 15, 'U': 14, 'T': 13, 'S': 12, 'R': 11, 'Q': 10}
def _extrair_android_de_bl(val: str) -> int:
    if not val or not val.strip() or val.strip().lower() == 'done':
        return 0
    s = val.strip()
    first = s[0].upper()
    if first in _BL_PREFIX_MAP and len(s) > 1 and s[1].isdigit():
        return _BL_PREFIX_MAP[first]
    for seg in reversed(s.replace('-', ' ').replace('_', ' ').split()):
        if not seg:
            continue
        if not len(seg) > 1:
            continue
        if seg[0].upper() not in _BL_PREFIX_MAP:
            continue
        if seg[1].isdigit():
            return _BL_PREFIX_MAP[seg[0].upper()]
    return 0
def _extrair_android_de_fp(fp: str) -> int:
    if not fp or ':' not in fp or '/' not in fp:
        return 0
    try:
        for part in fp.split('/'):
            if ':' in part:
                av_str = part.split(':')[-1].strip()
                if av_str.isdigit():
                    if 10 <= int(av_str) <= 20:
                        return int(av_str)
    except Exception:
        pass
    return 0
def _detectar_android(adb) -> int:
    ok, raw = _fb_cmd(adb, 'getvar version-bootloader', timeout=10)
    if ok and raw:
        for line in raw.splitlines():
            if 'version-bootloader' not in line:
                continue
            if ':' in line:
                val = line.split(':', 1)[1].strip()
                v = _extrair_android_de_bl(val)
                if not v:
                    continue
                return v
    try:
        _, all_out = _fb_cmd(adb, 'getvar all', timeout=15)
        if all_out:
            for line in all_out.splitlines():
                if 'version-bootloader' not in line:
                    continue
                if ':' in line:
                    val = line.split(':', 1)[1].strip()
                    v = _extrair_android_de_bl(val)
                    if not v:
                        continue
                    return v
            fp_parts = []
            for line in all_out.splitlines():
                if 'ro.build.fingerprint' not in line:
                    continue
                if ':' in line:
                    fp_parts.append(line.split(':', 1)[1].strip())
            if fp_parts:
                fp_full = ''.join(fp_parts)
                v = _extrair_android_de_fp(fp_full)
                if v:
                    return v
    except Exception:
        pass
    return 0
_SYNC_REFRESH_S = 86400
class MotoFrpEngine:
    def __init__(self):
        self._sync = MotoFrpSync()
        self._synced = False
        self._last_sync_ts = 0.0
        self._sync_ok_ts = 0.0
    def _ensure_sync(self) -> tuple:
        now = time.time()
        if self._synced and now - self._sync_ok_ts < _SYNC_REFRESH_S:
            return (True, 'OK')
        self._synced = False
        ok, msg = self._sync.sincronizar(force=False)
        if ok:
            self._synced = True
            self._sync_ok_ts = now
        return ok, msg
    def sync(self, force: bool=False) -> tuple:
        ok, msg = self._sync.sincronizar(force=force)
        if ok:
            self._synced = True
        return ok, msg
    def listar_marcas(self) -> list:
        return self._sync.listar_marcas()
    def listar_modelos(self, marca: str) -> list:
        return self._sync.listar_modelos(marca)
    def get_android_lote(self, codename: str) -> int:
        return self._sync.get_android_version(codename)
    def try_sync_debounce(self) -> tuple:
        now = time.time()
        if now - self._last_sync_ts < _SYNC_DEBOUNCE_S:
            return (False, 'OK')
        ok, msg = self._sync.sincronizar(force=True)
        if ok:
            self._last_sync_ts = now
            self._synced = True
        return ok, msg
    def read_info(self, log_cb: Callable=None) -> dict:
        info = {'serial': '', 'product': '', 'codename': '', 'secure': '', 'unlocked': '', 'frp_state': '', 'cpu': '', 'slot': ''}
        def _log(msg):
            if log_cb:
                log_cb(msg)
        try:
            adb = _get_adb()
        except Exception:
            _log('Erro: ferramenta de comunicacao indisponivel')
            return info
        if not _device_present(adb):
            _log('Nenhum dispositivo em fastboot detectado')
            return info
        _log('Dispositivo detectado em fastboot')
        varmap = {'serialno': 'serial', 'product': 'codename', 'secure': 'secure', 'unlocked': 'unlocked', 'frp-state': 'frp_state', 'cpu': 'cpu', 'current-slot': 'slot', 'sku': 'sku'}
        for fvar, key in varmap.items():
            val = _getvar(adb, fvar)
            if val:
                info[key] = val
        if info['codename']:
            info['product'] = info['codename']
        av = _detectar_android(adb)
        if av:
            info['android'] = str(av)
        elif info.get('codename'):
            av_lote = self._sync.get_android_version(info['codename'])
            if av_lote:
                info['android'] = str(av_lote)
                info['android_source'] = 'lote'
        android_display = info.get('android', '')
        if android_display and info.get('android_source') == 'lote':
            android_display = f'~{android_display} (esperado)'
        display_map = [('Modelo', info.get('sku', '')), ('Codename', info['codename']), ('Android', android_display), ('Serial', info['serial']), ('CPU', info['cpu']), ('Secure State', info['secure']), ('Unlocked', info['unlocked']), ('FRP State', info['frp_state']), ('Slot', info['slot'])]
        for label, val in display_map:
            if val:
                _log(f'  {label}: {val}')
        return info
    def executar_frp(self, codename: str, serial_len: int=10, log_cb: Callable=None, cancel_check: Callable=None) -> tuple:
        def _log(msg):
            if log_cb:
                log_cb(msg)
        def _cancelado() -> bool:
            if cancel_check:
                return cancel_check()
            return False
        try:
            adb = _get_adb()
        except Exception:
            return (False, 'Ferramenta de comunicacao indisponivel')
        self._ensure_sync()
        _log('[Etapa 1/5] Verificacao pre-operacao...')
        if not _device_present(adb):
            return (False, 'Nenhum dispositivo em fastboot')
        serial_dev = _get_usb_serial(adb)
        if not serial_dev:
            return (False, 'Conexao instavel ÔÇö reconecte o cabo USB')
        _log(f'  Dispositivo: {serial_dev}')
        product = _getvar(adb, 'product')
        if not product or len(product) > 30 or not product.replace('_', '').isalnum():
            time.sleep(3)
            product = _getvar(adb, 'product')
        if not product or len(product) > 30 or not product.replace('_', '').isalnum():
            return (False, 'Nao foi possivel identificar o dispositivo')
        _log(f'  Codename: {product}')
        lote_cn = self._sync.get_lote_codename(codename)
        cn_validos = {codename.lower()}
        if lote_cn:
            cn_validos.add(lote_cn.lower())
        cn_base = codename.split('-')[0].split('_')[0].lower()
        if cn_base:
            cn_validos.add(cn_base)
        if product.lower() not in cn_validos:
            return (False, 'Dispositivo incompativel')
        frp_before = _getvar(adb, 'frp-state') or 'ÔÇö'
        secure = _getvar(adb, 'securestate') or 'ÔÇö'
        slot_raw = _getvar(adb, 'current-slot') or 'a'
        slot = slot_raw.strip().lower()
        if slot not in ('a', 'b'):
            slot = 'a'
        lk_partition = f'lk_{slot}'
        _log(f'  FRP State: {frp_before}')
        _log(f'  Secure State: {secure}')
        _log(f'  Slot: {slot}')
        if 'no protection' in frp_before.lower():
            _log('  Dispositivo sem protecao FRP ÔÇö operacao desnecessaria')
            return (False, 'Dispositivo sem protecao FRP')
        android_dev = _detectar_android(adb)
        if android_dev:
            _log(f'  Android: {android_dev}')
        av_lote = self._sync.get_android_version(codename)
        if android_dev > 0 and av_lote > 0:
            if android_dev < av_lote:
                _log(f'  BLOQUEADO: Dispositivo com Android {android_dev}')
                _log(f'  Esta operacao requer Android {av_lote} ou superior')
                _log('  Atualize o software do dispositivo e tente novamente')
                return False, f'Versao incompativel ÔÇö Android {android_dev} detectado, necessario {av_lote}. Atualize o software do dispositivo.'
            if android_dev > av_lote:
                _log(f'  Aviso: Testado em Android {av_lote}, dispositivo com {android_dev}')
        elif android_dev == 0 and av_lote > 0:
            _log('  Aviso: Nao foi possivel verificar versao Android')
            _log(f'  Operacao testada em Android {av_lote} ÔÇö prosseguindo com cautela')
        serialno = _getvar(adb, 'serialno') or serial_dev
        if not serialno or len(serialno) < serial_len:
            return (False, 'Serial do dispositivo invalido')
        _log(f'  Serial: {serialno}')
        if _cancelado():
            _log('  Operacao cancelada pelo usuario')
            return (False, 'Operacao cancelada')
        _log('[Etapa 2/5] Preparando dados...')
        _log('  Obtendo dados do servidor (pode levar alguns segundos)...')
        lk_mod, _ = self._sync.download_lk(codename, 'lk_mod')
        if not lk_mod:
            return (False, 'Falha ao obter dados do servidor')
        _log('  Dados recebidos')
        _log('  Enviando dados ao dispositivo...')
        if not _device_present(adb, serial_dev):
            return (False, 'Conexao perdida ÔÇö verifique o cabo USB')
        tmp_mod = None
        try:
            tmp_mod = tempfile.NamedTemporaryFile(delete=False, suffix='.tmp')
            tmp_mod.write(lk_mod)
            tmp_mod.close()
            ok_f, _ = _fb_cmd(adb, f'flash {lk_partition} {tmp_mod.name}', timeout=45)
            if not ok_f:
                if tmp_mod:
                    try:
                        os.unlink(tmp_mod.name)
                    except Exception:
                        pass
                    return (False, 'Falha na comunicacao com o dispositivo')
                return (False, 'Falha na comunicacao com o dispositivo')
        except Exception:
            if tmp_mod:
                try:
                    os.unlink(tmp_mod.name)
                    return (False, 'Falha na comunicacao com o dispositivo')
                except Exception:
                    return (False, 'Falha na comunicacao com o dispositivo')
            return (False, 'Falha na comunicacao com o dispositivo')
        try:
            _log('  Dados aceitos pelo dispositivo')
        except Exception:
            if tmp_mod:
                try:
                    os.unlink(tmp_mod.name)
                    return (False, 'Falha na comunicacao com o dispositivo')
                except Exception:
                    return (False, 'Falha na comunicacao com o dispositivo')
            return (False, 'Falha na comunicacao com o dispositivo')
        if tmp_mod:
            try:
                os.unlink(tmp_mod.name)
            except Exception:
                pass
        if _cancelado():
            _log('  Operacao cancelada ÔÇö restaurando...')
            self._restaurar(adb, codename, lk_partition, log_cb, expected_serial=serial_dev)
            return (False, 'Operacao cancelada')
        _log('[Etapa 3/5] Reiniciando dispositivo...')
        ok_rb, data_rb = _fb_cmd(adb, 'reboot-bootloader', timeout=10)
        if not ok_rb:
            if 'status read failed' in (data_rb or '').lower():
                _log('  Reinicio em andamento...')
            else:
                _log('  Aviso: resposta inesperada do dispositivo')
        else:
            _log('  Comando de reinicio aceito')
        _log('  Aguardando reconexao...')
        reconectou = False
        for _ in range(9):
            if _cancelado():
                _log('  Operacao cancelada ÔÇö aguardando dispositivo para restaurar...')
                if _wait_for_device(adb, max_wait=30, interval=5, expected_serial=serial_dev):
                    self._restaurar(adb, codename, lk_partition, log_cb, expected_serial=serial_dev)
                return (False, 'Operacao cancelada')
            time.sleep(5)
            if not _device_present(adb, serial_dev):
                continue
            reconectou = True
            break
        if not reconectou:
            _log('  Dispositivo nao reconectou ÔÇö verifique o cabo USB')
            return (False, 'Dispositivo desconectou ÔÇö reconecte o cabo USB')
        _log('  Dispositivo reconectado')
        _log('[Etapa 4/5] Processando...')
        if _cancelado():
            _log('  Operacao cancelada ÔÇö restaurando...')
            self._restaurar(adb, codename, lk_partition, log_cb, expected_serial=serial_dev)
            return (False, 'Operacao cancelada')
        if not _device_present(adb, serial_dev):
            return (False, 'Dispositivo diferente detectado ÔÇö operacao abortada')
        try:
            from . import _mfk
            _sid = self._sync.get_srv_id(codename)
            _key = _mfk.gerar(serialno[:serial_len], lote=_sid)
        except Exception:
            self._restaurar(adb, codename, lk_partition, log_cb, expected_serial=serial_dev)
            return (False, 'Dispositivo incompativel')
        if not _key:
            self._restaurar(adb, codename, lk_partition, log_cb, expected_serial=serial_dev)
            return (False, 'Dispositivo incompativel')
        _log('  Enviando dados processados...')
        if not _device_present(adb, serial_dev):
            self._restaurar(adb, codename, lk_partition, log_cb, expected_serial=serial_dev)
            return (False, 'Dispositivo diferente detectado ÔÇö operacao abortada')
        _log('  Executando operacao...')
        ok_u, data_u = _fb_cmd(adb, f'oem unlock {_key}', timeout=60)
        if not ok_u or 'failure' in data_u.lower():
            _log('  Operacao rejeitada ÔÇö restaurando...')
            self._restaurar(adb, codename, lk_partition, log_cb, expected_serial=serial_dev)
            return (False, 'Operacao nao suportada neste dispositivo')
        _log('  Operacao aceita')
        if 'already unlocked' in data_u.lower():
            _log('  Dispositivo ja desbloqueado ÔÇö tentando via alternativa...')
            ok_e, _ = _fb_cmd(adb, 'erase frp', timeout=30)
            if not ok_e:
                _log('  Aviso: metodo alternativo falhou')
        _log('  Verificando resultado...')
        time.sleep(5)
        if not _device_present(adb, serial_dev):
            _log('  Aguardando dispositivo estabilizar...')
            _wait_for_device(adb, max_wait=30, interval=5, expected_serial=serial_dev)
        frp_after = 'ÔÇö'
        if _device_present(adb, serial_dev):
            frp_after = _getvar(adb, 'frp-state') or 'ÔÇö'
            _log(f'  FRP State: {frp_after}')
        else:
            _log('  Dispositivo em reinicio ÔÇö resultado sera verificado apos restauracao')
        _log('[Etapa 5/5] Finalizando...')
        is_primary = product.lower() == lote_cn.lower()
        self._restaurar(adb, codename, lk_partition, log_cb, expected_serial=serial_dev)
        reboot_ok = False
        for _r in range(3):
            if not _device_present(adb, serial_dev):
                time.sleep(3)
                if not _device_present(adb, serial_dev):
                    continue
            ok_final, data_final = _fb_cmd(adb, 'reboot', timeout=10)
            if not ok_final:
                if 'status read failed' in (data_final or '').lower():
                    reboot_ok = True
                    break
            time.sleep(5)
        if reboot_ok:
            _log('  Reiniciando dispositivo...')
        else:
            _log('  Reinicie o dispositivo manualmente (segure botao power 15s)')
        if 'no protection' in frp_after.lower():
            _log('Operacao concluida com sucesso!')
            if is_primary:
                return (True, 'Operacao concluida')
            _log('Passe o software para restaurar o sistema completo do dispositivo')
            return (True, 'Operacao concluida ÔÇö modelo secundario')
        _log('Nao foi possivel confirmar a operacao ÔÇö verifique o dispositivo')
        return (False, 'Nao foi possivel confirmar a operacao')
    def _restaurar(self, adb, codename: str, lk_partition: str='lk_a', log_cb: Callable=None, expected_serial: str=''):
        def _log(msg):
            if log_cb:
                log_cb(msg)
        if not _device_present(adb, expected_serial):
            _log('  Aguardando dispositivo para restauracao...')
            if not _wait_for_device(adb, max_wait=20, interval=3, expected_serial=expected_serial):
                _log('  Restauracao indisponivel ÔÇö passe o software para restaurar')
                return
        if expected_serial and _get_usb_serial(adb) != expected_serial:
            _log('  Dispositivo diferente detectado ÔÇö restauracao cancelada')
            return
        lk_clean, _ = self._sync.download_lk(codename, 'lk_clean')
        if not lk_clean:
            _log('  Aviso: dados originais indisponiveis')
            return
        tmp = None
        try:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.tmp')
            tmp.write(lk_clean)
            tmp.close()
            restaurado = False
            for tentativa in range(3):
                if _device_present(adb, expected_serial) or _wait_for_device(adb, max_wait=15, interval=3, expected_serial=expected_serial):
                    ok, _ = _fb_cmd(adb, f'flash {lk_partition} {tmp.name}', timeout=30)
                    if ok:
                        restaurado = True
                        break
                    time.sleep(5)
            if restaurado:
                _log('  Estado original restaurado')
            else:
                _log('  Falha na finalizacao ÔÇö reinicie o dispositivo manualmente')
        except Exception:
            _log('  Falha na finalizacao ÔÇö reinicie o dispositivo manualmente')
        finally:
            if tmp:
                try:
                    os.unlink(tmp.name)
                except Exception:
                    pass
