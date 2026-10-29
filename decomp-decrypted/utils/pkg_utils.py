import json
import os
import re
import logging
from app.utils.path_manager import PathManager
logger = logging.getLogger(__name__)
_CRITICAL_PACKAGES = frozenset({'com.lawnchair', 'com.miui.home', 'com.android.phone', 'com.asus.launcher', 'com.bbk.launcher2', 'com.lge.launcher2', 'com.lge.launcher3', 'com.oppo.launcher', 'com.poco.launcher', 'com.vivo.launcher', 'com.heytap.launcher', 'com.sonymobile.home', 'com.anddoes.launcher', 'com.android.launcher', 'com.android.settings', 'com.android.systemui', 'com.coloros.launcher', 'com.niagara.launcher', 'com.nothing.launcher', 'com.oneplus.launcher', 'com.android.launcher2', 'com.android.launcher3', 'com.miui.securitycore', 'com.motorola.systemui', 'com.coloros.safecenter', 'com.lawnchair.launcher', 'com.microsoft.launcher', 'com.motorola.launcher3', 'com.asus.zenui.launcher', 'com.miui.securitycenter', 'org.lineageos.trebuchet', 'com.niagara.launcher.pro', 'com.teslacoilsw.launcher', 'com.transsion.hilauncher', 'com.cyanogenmod.trebuchet', 'com.transsion.XOSLauncher', 'com.google.android.launcher', 'com.huawei.android.launcher', 'com.motorola.launcherconfig', 'com.ontim.launcher3.overlay', 'com.actionlauncher.playstore', 'com.hihonor.android.launcher', 'com.sec.android.app.launcher', 'com.mi.android.globallauncher', 'com.motorola.launcher3overlay', 'com.android.providers.settings', 'com.sprd.powersavemodelauncher', 'com.samsung.android.app.launcher', 'com.sec.android.emergencylauncher', 'com.transsion.XOSLauncher.upgrade', 'com.google.android.apps.nexuslauncher'})
_CRITICAL_PREFIXES = ('com.android.systemui', 'com.android.settings', 'com.android.providers.', 'com.android.phone', 'com.android.server.', 'com.android.inputmethod')
_ref_cache = {'loaded': False, 'unsafe': frozenset()}
def _load_ref_unsafe():
    if _ref_cache['loaded']:
        return _ref_cache['unsafe']
    unsafe = set()
    try:
        json_path = PathManager.get_database_path('test.json')
        if json_path and os.path.isfile(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                for pkg_name, info in data.items():
                    if isinstance(info, dict):
                        removal = info.get('removal', '')
                        if removal == 'Unsafe':
                            unsafe.add(pkg_name)
            logger.debug('pkg_utils: %d pacotes Unsafe carregados', len(unsafe))
    except Exception:
        logger.debug('pkg_utils: falha ao carregar test.json', exc_info=True)
    result = frozenset(unsafe)
    _ref_cache['unsafe'] = result
    _ref_cache['loaded'] = True
    return result
def detectar_ativo(adb_manager):
    try:
        adb_path = getattr(adb_manager, 'adb_path', None)
        if not adb_path:
            return
        output = adb_manager._run_adb_command([adb_path, 'shell', 'cmd', 'package', 'resolve-activity', '-c', 'android.intent.category.HOME', '-a', 'android.intent.action.MAIN'], timeout=15)
        if not output:
            return
        match = re.search('packageName=([a-zA-Z][a-zA-Z0-9_.]+)', output)
        if match:
            pkg = match.group(1)
            if pkg != 'android':
                logger.debug('pkg_utils: launcher ativo = %s', pkg)
                return pkg
    except Exception:
        logger.debug('pkg_utils: falha ao detectar launcher ativo', exc_info=True)
def listar_home(adb_manager):
    resultado = set()
    try:
        adb_path = getattr(adb_manager, 'adb_path', None)
        if not adb_path:
            return frozenset()
        output = adb_manager._run_adb_command([adb_path, 'shell', 'cmd', 'package', 'query-activities', '--brief', '-a', 'android.intent.action.MAIN', '-c', 'android.intent.category.HOME'], timeout=30)
        if not output:
            return frozenset()
        for match in re.finditer('([a-zA-Z][a-zA-Z0-9_.]+)/', output):
            pkg = match.group(1)
            if not pkg:
                continue
            if len(pkg) > 3:
                resultado.add(pkg)
        if resultado:
            logger.debug('pkg_utils: %d HOME launchers no device', len(resultado))
    except Exception:
        logger.debug('pkg_utils: falha ao listar HOME launchers', exc_info=True)
    return frozenset(resultado)
def obter_protegidos(adb_manager=None):
    protegidos = set(_CRITICAL_PACKAGES)
    try:
        protegidos.update(_load_ref_unsafe())
    except Exception:
        pass
    if adb_manager:
        try:
            ativo = detectar_ativo(adb_manager)
            if ativo:
                protegidos.add(ativo)
        except Exception:
            pass
        try:
            todos = listar_home(adb_manager)
            protegidos.update(todos)
        except Exception:
            pass
    return frozenset(protegidos)
def is_protegido(package_name, protegidos=None):
    if not package_name:
        return False
    lista = protegidos if protegidos is not None else _CRITICAL_PACKAGES
    if package_name in lista:
        return True
    if any((package_name.startswith(p) for p in _CRITICAL_PREFIXES)):
        return True
    if protegidos is None:
        unsafe = _load_ref_unsafe()
        if package_name in unsafe:
            return True
    return False
def consultar_ref(package_name):
    try:
        json_path = PathManager.get_database_path('test.json')
        if not json_path or not os.path.isfile(json_path):
            return
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict) and package_name in data:
            return data[package_name]
    except Exception:
        logger.debug('pkg_utils: falha ao consultar %s', package_name, exc_info=True)
