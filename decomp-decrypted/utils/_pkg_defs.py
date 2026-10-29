import json
import re
import logging
import os
logger = logging.getLogger(__name__)
_STATIC_PROTECTED = frozenset({'com.lawnchair', 'com.miui.home', 'com.android.phone', 'com.asus.launcher', 'com.bbk.launcher2', 'com.lge.launcher2', 'com.lge.launcher3', 'com.oppo.launcher', 'com.poco.launcher', 'com.vivo.launcher', 'com.heytap.launcher', 'com.sonymobile.home', 'com.anddoes.launcher', 'com.android.launcher', 'com.android.settings', 'com.android.systemui', 'com.coloros.launcher', 'com.niagara.launcher', 'com.nothing.launcher', 'com.oneplus.launcher', 'com.android.launcher2', 'com.android.launcher3', 'com.miui.securitycore', 'com.motorola.systemui', 'com.coloros.safecenter', 'com.lawnchair.launcher', 'com.microsoft.launcher', 'com.motorola.launcher3', 'com.asus.zenui.launcher', 'com.miui.securitycenter', 'org.lineageos.trebuchet', 'com.niagara.launcher.pro', 'com.teslacoilsw.launcher', 'com.transsion.hilauncher', 'com.cyanogenmod.trebuchet', 'com.transsion.XOSLauncher', 'com.google.android.launcher', 'com.huawei.android.launcher', 'com.motorola.launcherconfig', 'com.ontim.launcher3.overlay', 'com.actionlauncher.playstore', 'com.hihonor.android.launcher', 'com.sec.android.app.launcher', 'com.mi.android.globallauncher', 'com.motorola.launcher3overlay', 'com.android.providers.settings', 'com.sprd.powersavemodelauncher', 'com.samsung.android.app.launcher', 'com.sec.android.emergencylauncher', 'com.transsion.XOSLauncher.upgrade', 'com.google.android.apps.nexuslauncher'})
_PROTECTED_PREFIXES = ('com.android.systemui', 'com.android.settings', 'com.android.providers.', 'com.android.phone', 'com.android.server.', 'com.android.inputmethod')
MANUFACTURER_ADWARE = frozenset({'com.miui.daemon', 'com.xiaomi.joyose', 'com.miui.analytics', 'com.miui.bugreport', 'com.xiaomi.mipicks', 'com.miui.msa.global', 'com.miui.yellowpage', 'com.miui.systemAdSolution'})
def _load_unsafe_from_json():
    try:
        from app.utils.path_manager import PathManager
        json_path = PathManager.get_database_path('test.json')
        if not json_path or not os.path.isfile(json_path):
            logger.debug('Dados de referencia nao encontrados via PathManager')
            return frozenset()
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        unsafe = set()
        for pkg_name, info in data.items():
            removal = info.get('removal', '')
            if removal in ('Unsafe', 'Expert'):
                unsafe.add(pkg_name)
        logger.debug('Definicoes de referencia carregadas: %d entradas', len(unsafe))
    except Exception:
        logger.debug('Falha ao carregar definicoes de referencia', exc_info=True)
        return frozenset()
    return frozenset(unsafe)
_unsafe_cache = None
def _get_unsafe_packages():
    global _unsafe_cache
    if _unsafe_cache is None:
        _unsafe_cache = _load_unsafe_from_json()
    return _unsafe_cache
def detectar_launcher_ativo(adb_manager):
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
                logger.debug('Launcher ativo detectado: %s', pkg)
                return pkg
    except Exception:
        logger.debug('Falha ao detectar launcher ativo', exc_info=True)
def listar_todos_launchers(adb_manager):
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
    except Exception:
        logger.debug('Falha ao listar launchers instalados', exc_info=True)
    return frozenset(resultado)
def obter_pacotes_protegidos(adb_manager=None):
    protegidos = set(_STATIC_PROTECTED)
    protegidos.update(_get_unsafe_packages())
    protegidos -= MANUFACTURER_ADWARE
    if adb_manager:
        try:
            ativo = detectar_launcher_ativo(adb_manager)
            if ativo:
                if ativo in _STATIC_PROTECTED or ativo in _get_unsafe_packages():
                    protegidos.add(ativo)
                elif ativo:
                    logger.warning("Launcher ativo '%s' nao e conhecido ÔÇö possivel sequestro de home screen.", ativo)
        except Exception:
            pass
    return frozenset(protegidos)
def is_pacote_protegido(package_name, pacotes_protegidos=None):
    if not package_name:
        return False
    if pacotes_protegidos is None:
        pacotes_protegidos = _STATIC_PROTECTED | _get_unsafe_packages()
    if package_name in pacotes_protegidos:
        return True
    if any((package_name.startswith(prefix) for prefix in _PROTECTED_PREFIXES)):
        return True
    return False
def is_manufacturer_adware(package_name):
    if package_name:
        return package_name in MANUFACTURER_ADWARE
    return False
