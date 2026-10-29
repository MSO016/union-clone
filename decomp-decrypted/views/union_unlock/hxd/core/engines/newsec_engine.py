import os
import re
import time
import logging
from typing import (Tuple, Optional, Callable)
logger = logging.getLogger(__name__)
_RE_OWNER_ATIVO = re.compile('Device Owner.*?admin=ComponentInfo\\{([^}]+)\\}', re.DOTALL)
_OTA_POR_MARCA = {'realme': ['com.nearme.romupdate', 'com.coloros.sau', 'com.oplus.ota'], 'oppo': ['com.nearme.romupdate', 'com.coloros.sau', 'com.oplus.ota'], 'samsung': ['com.wssyncmldm', 'com.sec.android.soagent'], 'xiaomi': ['com.android.updater'], 'motorola': ['com.motorola.ccc.ota'], 'tecno': ['com.transsion.systemupdate', 'com.transsion.plat.appupdate', 'com.transsion.overlaysuw.resoverlay', 'com.android.mms.service'], 'infinix': ['com.transsion.systemupdate', 'com.transsion.plat.appupdate', 'com.transsion.overlaysuw.resoverlay', 'com.android.mms.service']}
_OTA_GENERICOS = ['com.google.android.configupdater', 'com.android.dynsystem']
_MDM_ALVOS = ['com.scorpio.securitycom', 'com.heytap.cloud', 'com.android.proxyhandlr']
_KG_CLIENT = 'com.samsung.android.kgclient'
_KG_APPOPS_DENY = ['RUN_IN_BACKGROUND', 'RUN_ANY_IN_BACKGROUND', 'WAKE_LOCK', 'POST_NOTIFICATION', 'ACCESS_RESTRICTED_SETTINGS', 'SCHEDULE_EXACT_ALARM', 'BLUETOOTH_CONNECT', 'SYSTEM_EXEMPT_FROM_DISMISSIBLE_NOTIFICATIONS']
_SAMSUNG_SECURITY_PKGS = ['com.samsung.klmsagent', 'com.sec.enterprise.knox.cloudmdm.smdms', 'com.sec.android.app.SecSetupWizard', 'com.samsung.android.app.omcagent', 'com.samsung.android.themecenter', 'com.samsung.android.themestore', 'com.samsung.android.sdm.config', 'com.samsung.android.cidmanager', 'com.samsung.android.gru', 'com.aura.oobe.samsung.gl', 'com.samsung.android.app.updatecenter']
_SCORPIO_SECURITY = 'com.scorpio.securitycom'
_PKG = 'com.techunion.deviceadmin'
_RCV = f'{_PKG}/.MyAdminReceiver'
_ACT_BLOCK = f'{_PKG}/.DisableFactoryReset'
_ACT_DNS = f'{_PKG}/.newd'
_DNS_KEY = '4641d586b3d0c165a1c5d52a4372545e'
_APK_NAME = 'techunion_admin.apk'
_DNS_SEGURO = 'a687f8.dns.nextdns.io'
class NewsecEngine:
    def __init__(self, adb_manager):
        self._adb = adb_manager
    def _cmd(self, args, timeout: int=15) -> Optional[str]:
        try:
            return self._adb.execute_adb_command(args, timeout=timeout)
        except Exception:
            return
    def _cmd_silent(self, args, timeout: int=8) -> Optional[str]:
        adb_logger = logging.getLogger('app.utils.adb_manager')
        original_level = adb_logger.level
        adb_logger.setLevel(logging.CRITICAL)
        try:
            return self._adb.execute_adb_command(args, timeout=timeout)
        except Exception:
            adb_logger.setLevel(original_level)
            return
        finally:
            adb_logger.setLevel(original_level)
    def _prop(self, chave: str) -> str:
        val = self._cmd(f'shell getprop {chave}', timeout=5)
        return (val or '').strip()
    def _conectado(self) -> bool:
        try:
            return self._adb.is_device_connected()
        except Exception:
            return False
    def _apk_path(self) -> Optional[str]:
        try:
            from app.utils.path_manager import PathManager
            found = PathManager.get_apk_path(_APK_NAME)
            if found:
                return found
        except Exception:
            pass
        try:
            if self._adb.adb_path and os.path.isfile(self._adb.adb_path):
                p = os.path.join(os.path.dirname(self._adb.adb_path), _APK_NAME)
                if os.path.isfile(p):
                    return p
        except Exception:
            pass
    def _tem_owner_real(self) -> Tuple[bool, str]:
        dp = self._cmd('shell dumpsys device_policy', timeout=10) or ''
        m = _RE_OWNER_ATIVO.search(dp)
        if m:
            return True, m.group(1).split('/')[0]
        return (False, '')
    def _kg_bypass(self, log_cb: Callable[[str, str], None]=None):
        def _log(tipo, msg=''):
            if log_cb:
                try:
                    log_cb(tipo, msg)
                    return
                except Exception:
                    pass
        kg = _KG_CLIENT
        self._cmd_silent(f'shell am set-inactive {kg} true')
        self._cmd_silent(f'shell am kill {kg}')
        self._cmd_silent(f'shell am crash {kg}')
        self._cmd_silent(f'shell am stop-app {kg}')
        _log('ok', 'KG bypass Method #1 : OK')
        self._cmd_silent(f'shell pm uninstall-system-updates {kg}')
        self._cmd_silent(f'shell pm disable-user --user 0 {kg}')
        self._cmd_silent(f'shell pm enable --user 0 {kg}')
        self._cmd_silent(f'shell pm uninstall-system-updates {kg}')
        self._cmd_silent(f'shell pm suspend {kg}')
        self._cmd_silent(f'shell pm uninstall --user 0 {kg}')
        self._cmd_silent(f'shell pm install-existing --restrict-permissions --user 0 {kg}')
        _log('ok', 'KG bypass Method #2 : OK')
        for op in _KG_APPOPS_DENY:
            self._cmd_silent(f'shell cmd appops set {kg} {op} deny')
        _log('ok', 'KG bypass Method #3 : OK')
        self._cmd_silent(f'shell pm suspend {kg}')
        self._cmd_silent(f'shell am set-inactive {kg} true')
        self._cmd_silent(f'shell am kill {kg}')
        self._cmd_silent(f'shell am crash {kg}')
        self._cmd_silent(f'shell am stop-app {kg}')
        _log('ok', 'KG bypass Method #4 : OK')
    def _scorpio_bypass(self):
        sc = _SCORPIO_SECURITY
        self._cmd_silent(f'shell am set-inactive {sc}')
        self._cmd_silent(f'shell am kill {sc}')
        self._cmd_silent(f'shell am crash {sc}')
        self._cmd_silent(f'shell am stop-app {sc}')
        self._cmd_silent(f'shell pm uninstall-system-updates {sc}')
        self._cmd_silent(f'shell pm disable-user --user 0 {sc}')
        self._cmd_silent(f'shell pm suspend {sc}')
        self._cmd_silent(f'shell cmd appops set {sc} RUN_IN_BACKGROUND ignore')
        self._cmd_silent('shell pm disable-user --user 0 com.transsion.overlaysuw')
    def executar(self, log_cb: Callable[[str, str], None]) -> Tuple[bool, str]:
        t0 = time.time()
        def _log(tipo, msg=''):
            try:
                log_cb(tipo, msg)
                return
            except Exception:
                return
        _log('separador')
        _log('info', 'Phone Mode: ADB Debugging')
        _log('info', 'Operation: SPD/MTK New Sec 2026')
        _log('info', 'Check Authority: OK')
        if not self._conectado():
            _log('erro', 'Nenhum dispositivo conectado.')
            return (False, 'Nenhum dispositivo conectado.')
        _log('ok', 'Waiting ADB devices... OK')
        _log('ok', 'Starting server... OK')
        _log('ok', 'Waiting ADB Server... OK')
        _log('info', 'Fetch Data... OK')
        serial = self._prop('ro.serialno')
        plataforma = self._prop('ro.board.platform')
        cpu_abi = self._prop('ro.product.cpu.abi')
        fabricante = self._prop('ro.product.manufacturer')
        board = self._prop('ro.product.board')
        brand = self._prop('ro.product.brand')
        modelo = self._prop('ro.product.model')
        build_id = self._prop('ro.build.display.id')
        versao = self._prop('ro.build.version.release')
        build_date = self._prop('ro.build.date')
        patch = self._prop('ro.build.version.security_patch')
        description = self._prop('ro.build.description')
        _log('dados', f' SN : {serial}')
        _log('dados', f' Platform : {plataforma}')
        _log('dados', f' Cpu Abi : {cpu_abi}')
        _log('dados', f' Manufacturer : {fabricante}')
        _log('dados', f' Board : {board}')
        _log('dados', f' Brand : {brand}')
        _log('dados', f' Model : {modelo}')
        _log('dados', f' Build Id : {build_id}')
        _log('dados', f' Version : {versao}')
        _log('dados', f' Build Date: {build_date}')
        _log('dados', f' Security Patch : {patch}')
        _log('dados', f' Description : {description}')
        if not self._conectado():
            _log('erro', 'Dispositivo desconectado.')
            return (False, 'Dispositivo desconectado durante opera├º├úo.')
        _log('ok', 'Check Connection... OK')
        marca = (brand or fabricante or '').lower()
        pkgs_ota = _OTA_POR_MARCA.get(marca, []) + _OTA_GENERICOS
        for pkg in pkgs_ota:
            self._cmd_silent(f'shell pm uninstall -k --user 0 {pkg}')
        _log('ok', 'Block OTA : OK')
        if marca == 'samsung':
            self._kg_bypass(log_cb=_log)
        else:
            self._scorpio_bypass()
        if not self._conectado():
            _log('erro', 'Dispositivo desconectado.')
            return (False, 'Dispositivo desconectado durante opera├º├úo.')
        _log('ok', 'Check Connection... OK')
        for mdm in _MDM_ALVOS:
            self._cmd_silent(f'shell pm clear {mdm}')
            self._cmd_silent(f'shell pm uninstall -k --user 0 {mdm}')
        for pkg in _SAMSUNG_SECURITY_PKGS:
            self._cmd_silent(f'shell pm uninstall --user 0 {pkg}')
        _log('ok', 'Remove MDM : OK')
        tem_owner, owner_pkg = self._tem_owner_real()
        if tem_owner and owner_pkg == _PKG:
            _log('ok', 'Protection already active : OK')
        elif tem_owner:
            _log('aviso', 'Existing protection detected ÔÇö attempting override')
            self._cmd_silent(f'shell pm clear {owner_pkg}')
            self._cmd_silent(f'shell pm uninstall -k --user 0 {owner_pkg}')
            _log('ok', 'Clear existing protection : OK')
            _log('info', 'Reboot: preparing...')
            self._cmd('reboot', timeout=10)
            time.sleep(15)
            for _ in range(12):
                if self._conectado():
                    break
                time.sleep(5)
            if not self._conectado():
                _log('erro', 'Dispositivo n├úo reconectou ap├│s rein├¡cio.')
                return (False, 'Dispositivo n├úo reconectou ap├│s rein├¡cio.')
            _log('ok', 'Reboot : OK')
        tem_owner_pre, owner_pre = self._tem_owner_real()
        ja_nosso = tem_owner_pre and owner_pre == _PKG
        if ja_nosso:
            _log('ok', 'Install Component : OK (already installed)')
            _log('ok', 'Register Protection : OK (already set)')
        else:
            apk = self._apk_path()
            if not apk:
                _log('erro', 'Falha ao conectar ao servidor de prote├º├úo.')
                return (False, 'Falha ao conectar ao servidor de prote├º├úo.')
            r = self._cmd(['install', '-r', apk], timeout=30)
            if r is not None:
                if 'success' not in (r or '').lower():
                    logger.error('Falha install APK: %s', (r or '')[:80])
                    _log('erro', 'Falha na instala├º├úo do componente.')
                    return (False, 'Falha na instala├º├úo do componente de prote├º├úo.')
            _log('ok', 'Install Component : OK')
            tem_owner_agora, pkg_agora = self._tem_owner_real()
            if tem_owner_agora and pkg_agora == _PKG:
                _log('ok', 'Register Protection : OK (already set)')
            else:
                r = self._cmd(f'shell dpm set-device-owner {_RCV}', timeout=15)
                if r is not None:
                    if 'success' not in (r or '').lower():
                        logger.error('Falha dpm: %s', (r or '')[:80])
                        _log('erro', 'N├úo foi poss├¡vel registrar prote├º├úo.')
                        _log('info', 'Remova todas as contas (Google, Samsung)')
                        _log('info', 'e desative Administradores em')
                        _log('info', 'Configura├º├Áes > Seguran├ºa > Admins')
                        self._cmd_silent(f'shell pm uninstall {_PKG}')
                        return (False, 'Remova as contas e desative Administradores do dispositivo.')
                _log('ok', 'Register Protection : OK')
        self._cmd(f'shell am start -n {_ACT_BLOCK}', timeout=10)
        time.sleep(1)
        _log('ok', 'DisableFactoryReset : OK')
        self._cmd_silent('shell settings put global private_dns_mode hostname')
        self._cmd_silent(f'shell settings put global private_dns_specifier {_DNS_SEGURO}')
        self._cmd(f'shell am start -n {_ACT_DNS} --es key {_DNS_KEY}', timeout=10)
        _log('ok', 'Configure DNS : OK')
        tem_final, _ = self._tem_owner_real()
        _log('separador')
        if tem_final:
            _log('ok', 'Factory reset not allowed!..')
        else:
            _log('ok', 'Operation completed ÔÇö reboot device to verify.')
        elapsed = int(time.time() - t0)
        _log('info', f'Elapsed Time : {elapsed} Seconds')
        _log('separador')
        return (True, 'Prote├º├úo ativada com sucesso.')
    def fix_playstore(self, log_cb: Callable[[str, str], None]) -> Tuple[bool, str]:
        t0 = time.time()
        def _log(tipo, msg=''):
            try:
                log_cb(tipo, msg)
                return
            except Exception:
                return
        _log('separador')
        _log('info', 'Operation: Fix Play Store')
        if not self._conectado():
            _log('erro', 'Nenhum dispositivo conectado.')
            return (False, 'Nenhum dispositivo conectado.')
        _log('ok', 'Waiting ADB devices... OK')
        brand = self._prop('ro.product.brand')
        modelo = self._prop('ro.product.model')
        _log('dados', f' Brand : {brand}')
        _log('dados', f' Model : {modelo}')
        marca = (brand or '').lower()
        fabricante = self._prop('ro.product.manufacturer').lower()
        marca_ref = marca or fabricante
        if marca_ref == 'samsung':
            self._kg_bypass(log_cb=_log)
        else:
            self._scorpio_bypass()
        if not self._conectado():
            _log('erro', 'Dispositivo desconectado.')
            return (False, 'Dispositivo desconectado durante opera├º├úo.')
        _log('ok', 'Check Connection... OK')
        self._cmd_silent('shell cmd -w wifi set-wifi-enabled disabled')
        _log('ok', 'WiFi disabled : OK')
        self._cmd_silent('shell pm clear com.google.android.gms')
        _log('ok', 'Clear GMS data : OK')
        self._cmd_silent('shell pm disable-user com.google.android.gms')
        self._cmd_silent('shell input keyevent KEYCODE_WAKEUP')
        _supervision_pkgs = ['com.google.android.gms.supervision', 'com.google.android.devicelockcontroller', 'com.google.android.apps.safetyhub', 'com.google.android.configupdater', 'com.android.managedprovisioning', 'com.google.android.apps.restore', 'com.google.android.as.oss']
        for pkg in _supervision_pkgs:
            self._cmd_silent(f'shell pm uninstall --user 0 {pkg}')
        for pkg in _SAMSUNG_SECURITY_PKGS:
            self._cmd_silent(f'shell pm uninstall --user 0 {pkg}')
        _log('ok', 'Remove supervision : OK')
        self._cmd_silent('shell pm clear com.google.android.gms')
        self._cmd_silent('shell input keyevent KEYCODE_WAKEUP')
        self._cmd_silent('shell cmd -w wifi set-wifi-enabled disabled')
        self._cmd_silent('shell pm uninstall --user 0 com.google.android.gms')
        r = self._cmd('shell cmd package install-existing --user 0 com.google.android.gms', timeout=15)
        self._cmd('shell pm enable com.google.android.gms', timeout=10)
        _log('ok', 'Reinstall GMS : OK')
        self._cmd_silent('shell content insert --uri content://settings/secure --bind name:s:user_setup_complete --bind value:s:1')
        _log('ok', 'Setup complete : OK')
        self._cmd_silent('shell settings put global private_dns_mode hostname')
        self._cmd_silent(f'shell settings put global private_dns_specifier {_DNS_SEGURO}')
        _log('ok', 'Configure DNS : OK')
        self._cmd('shell cmd -w wifi set-wifi-enabled enabled', timeout=10)
        self._cmd_silent('shell input keyevent KEYCODE_WAKEUP')
        _log('ok', 'WiFi enabled : OK')
        _log('separador')
        gms_path = self._cmd('shell pm path com.google.android.gms', timeout=10)
        if gms_path:
            if 'package:' in (gms_path or ''):
                _log('ok', 'Play Services : Active')
            else:
                _log('aviso', 'Play Services : Verify manually')
        elapsed = int(time.time() - t0)
        _log('info', f'Elapsed Time : {elapsed} Seconds')
        _log('separador')
        return (True, 'Play Store restaurada com sucesso.')
    def dns_status(self) -> dict:
        result = {'connected': False, 'mode': '', 'specifier': ''}
        if not self._conectado():
            return result
        result['connected'] = True
        mode = (self._cmd_silent('shell settings get global private_dns_mode') or '').strip()
        spec = (self._cmd_silent('shell settings get global private_dns_specifier') or '').strip()
        result['mode'] = '' if mode in ('null', '') else mode
        result['specifier'] = '' if spec in ('null', '') else spec
        return result
    def dns_apply(self, hostname: str, log_cb: Callable[[str, str], None]) -> Tuple[bool, str]:
        t0 = time.time()
        def _log(tipo, msg=''):
            try:
                log_cb(tipo, msg)
                return
            except Exception:
                return
        _log('separador')
        _log('info', 'Operation: DNS Setup')
        if not self._conectado():
            _log('erro', 'Nenhum dispositivo conectado.')
            return (False, 'Dispositivo n├úo conectado.')
        _log('ok', 'Device connected : OK')
        hostname = hostname.strip()
        if not hostname or ' ' in hostname or len(hostname) > 253:
            _log('erro', 'Configura├º├úo inv├ílida.')
            return (False, 'Configura├º├úo inv├ílida.')
        tem_owner, owner_pkg = self._tem_owner_real()
        if tem_owner and owner_pkg == _PKG:
            _log('info', 'Prote├º├úo ativa detectada')
        self._cmd_silent('shell settings put global private_dns_mode hostname')
        self._cmd_silent(f'shell settings put global private_dns_specifier {hostname}')
        _log('ok', 'Apply DNS : OK')
        time.sleep(1)
        check_spec = (self._cmd_silent('shell settings get global private_dns_specifier') or '').strip()
        if check_spec == hostname:
            _log('ok', 'DNS Protected : Active')
            elapsed = int(time.time() - t0)
            _log('info', f'Elapsed Time : {elapsed} Seconds')
            _log('separador')
            return (True, 'DNS configurado.')
        if tem_owner:
            _log('info', 'Dispositivo gerenciado ÔÇö opera├º├úo n├úo permitida')
            elapsed = int(time.time() - t0)
            _log('info', f'Elapsed Time : {elapsed} Seconds')
            _log('separador')
            return (False, 'Dispositivo gerenciado.')
        _log('ok', 'DNS applied ÔÇö verify on device')
        elapsed = int(time.time() - t0)
        _log('info', f'Elapsed Time : {elapsed} Seconds')
        _log('separador')
        return (True, 'DNS aplicado.')
    def dns_remove(self, log_cb: Callable[[str, str], None]) -> Tuple[bool, str]:
        t0 = time.time()
        def _log(tipo, msg=''):
            try:
                log_cb(tipo, msg)
                return
            except Exception:
                return
        _log('separador')
        _log('info', 'Operation: DNS Remove')
        if not self._conectado():
            _log('erro', 'Nenhum dispositivo conectado.')
            return (False, 'Dispositivo n├úo conectado.')
        _log('ok', 'Device connected : OK')
        tem_owner, owner_pkg = self._tem_owner_real()
        if tem_owner and owner_pkg == _PKG:
            _log('info', 'Prote├º├úo ativa detectada')
        self._cmd_silent('shell settings put global private_dns_mode off')
        _log('ok', 'DNS Mode : off')
        time.sleep(1)
        check = (self._cmd_silent('shell settings get global private_dns_mode') or '').strip()
        if check == 'off':
            _log('ok', 'DNS removed : OK')
        elif tem_owner:
            _log('info', 'Dispositivo gerenciado ÔÇö DNS restaurado')
        else:
            _log('ok', 'DNS removed')
        elapsed = int(time.time() - t0)
        _log('info', f'Elapsed Time : {elapsed} Seconds')
        _log('separador')
        return (True, 'DNS removido.')
    def dns_test(self, hostname: str, log_cb: Callable[[str, str], None]) -> Tuple[bool, str]:
        t0 = time.time()
        def _log(tipo, msg=''):
            try:
                log_cb(tipo, msg)
                return
            except Exception:
                return
        _log('separador')
        _log('info', 'Operation: DNS Test')
        if not self._conectado():
            _log('erro', 'Nenhum dispositivo conectado.')
            return (False, 'Dispositivo n├úo conectado.')
        _log('ok', 'Device connected : OK')
        hostname = hostname.strip()
        if not hostname or ' ' in hostname or len(hostname) > 253:
            _log('erro', 'Configura├º├úo inv├ílida.')
            return (False, 'Configura├º├úo inv├ílida.')
        modo_ant = (self._cmd_silent('shell settings get global private_dns_mode') or '').strip()
        dns_ant = (self._cmd_silent('shell settings get global private_dns_specifier') or '').strip()
        _log('ok', 'Current state saved : OK')
        self._cmd_silent('shell settings put global private_dns_mode hostname')
        self._cmd_silent(f'shell settings put global private_dns_specifier {hostname}')
        _log('ok', 'DNS applied : OK')
        _log('info', 'Checking connection...')
        time.sleep(5)
        resolveu = False
        r = self._cmd_silent('shell nslookup google.com', timeout=8)
        if r and 'Address' in r and "can't" not in r.lower():
            resolveu = True
        if not resolveu:
            r2 = self._cmd_silent('shell ping -c 1 -W 4 google.com', timeout=10) or ''
            if '1 received' in r2 or 'bytes from' in r2:
                resolveu = True
        if not resolveu:
            r3 = self._cmd_silent('shell ping -c 1 -W 3 8.8.8.8', timeout=8) or ''
            if '1 received' not in r3 and 'bytes from' not in r3:
                _log('aviso', 'Dispositivo sem internet')
                elapsed = int(time.time() - t0)
                _log('info', f'Elapsed Time : {elapsed} Seconds')
                _log('separador')
                return (False, 'Sem internet.')
        if resolveu:
            _log('ok', 'DNS resolution : OK')
            _log('ok', 'DNS Test : PASS')
            elapsed = int(time.time() - t0)
            _log('info', f'Elapsed Time : {elapsed} Seconds')
            _log('separador')
            return (True, 'DNS v├ílido.')
        _log('info', 'Restoring previous state...')
        if modo_ant and modo_ant not in ('null', ''):
            self._cmd_silent(f'shell settings put global private_dns_mode {modo_ant}')
            if dns_ant and dns_ant not in ('null', ''):
                self._cmd_silent(f'shell settings put global private_dns_specifier {dns_ant}')
        else:
            self._cmd_silent('shell settings put global private_dns_mode off')
        _log('ok', 'Previous state restored : OK')
        _log('aviso', 'N├úo foi poss├¡vel concluir a opera├º├úo')
        elapsed = int(time.time() - t0)
        _log('info', f'Elapsed Time : {elapsed} Seconds')
        _log('separador')
        return (False, 'N├úo foi poss├¡vel concluir a opera├º├úo.')
