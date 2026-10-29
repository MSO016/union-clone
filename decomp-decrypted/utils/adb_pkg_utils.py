import json
import os
import re
import logging
logger = logging.getLogger(__name__)
_CRITICAL_PKGS = frozenset({'com.lawnchair', 'com.miui.home', 'com.android.phone', 'com.asus.launcher', 'com.bbk.launcher2', 'com.lge.launcher2', 'com.lge.launcher3', 'com.oppo.launcher', 'com.poco.launcher', 'com.vivo.launcher', 'com.heytap.launcher', 'com.sonymobile.home', 'com.anddoes.launcher', 'com.android.launcher', 'com.android.settings', 'com.android.systemui', 'com.coloros.launcher', 'com.niagara.launcher', 'com.nothing.launcher', 'com.oneplus.launcher', 'com.android.launcher2', 'com.android.launcher3', 'com.miui.securitycore', 'com.coloros.safecenter', 'com.lawnchair.launcher', 'com.microsoft.launcher', 'com.motorola.launcher3', 'com.asus.zenui.launcher', 'com.miui.securitycenter', 'org.lineageos.trebuchet', 'com.niagara.launcher.pro', 'com.teslacoilsw.launcher', 'com.transsion.hilauncher', 'com.cyanogenmod.trebuchet', 'com.transsion.XOSLauncher', 'com.android.server.telecom', 'com.google.android.launcher', 'com.huawei.android.launcher', 'com.motorola.launcherconfig', 'com.ontim.launcher3.overlay', 'com.actionlauncher.playstore', 'com.hihonor.android.launcher', 'com.sec.android.app.launcher', 'com.mi.android.globallauncher', 'com.motorola.launcher3overlay', 'com.android.providers.settings', 'com.sprd.powersavemodelauncher', 'com.android.providers.telephony', 'com.samsung.android.app.launcher', 'com.sec.android.emergencylauncher', 'com.transsion.XOSLauncher.upgrade', 'com.android.connectivity.resources', 'com.google.android.apps.nexuslauncher'})
_CRITICAL_PREFIXES = ('com.android.systemui', 'com.android.settings', 'com.android.providers.', 'com.android.phone', 'com.android.server.', 'com.android.inputmethod')
_uad_cache = None
_uad_unsafe_cache = None
def _carregar_uad():
    global _uad_cache
    if _uad_cache is not None:
        return _uad_cache
    caminhos = []
    try:
        from app.utils.path_manager import PathManager
        caminhos.append(PathManager.get_database_path('test.json'))
    except Exception:
        pass
    current_dir = os.path.dirname(os.path.abspath(__file__))
    caminhos.append(os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'app', 'database', 'test.json'))
    caminhos.append(os.path.join(os.path.dirname(current_dir), 'database', 'test.json'))
    for caminho in caminhos:
        try:
            if caminho and os.path.isfile(caminho):
                with open(caminho, 'r', encoding='utf-8') as f:
                    _uad_cache = json.load(f)
                logger.debug('UAD carregado: %d pacotes de %s', len(_uad_cache), caminho)
                return _uad_cache
        except Exception:
            continue
    logger.debug('UAD indisponivel ÔÇö usando apenas lista estatica')
    _uad_cache = {}
    return _uad_cache
def _obter_uad_unsafe():
    global _uad_unsafe_cache
    if _uad_unsafe_cache is not None:
        return _uad_unsafe_cache
    uad = _carregar_uad()
    unsafe = set()
    for pkg, info in uad.items():
        try:
            if isinstance(info, dict):
                if info.get('removal') == 'Unsafe':
                    unsafe.add(pkg)
        except Exception:
            continue
    _uad_unsafe_cache = frozenset(unsafe)
    logger.debug('UAD Unsafe: %d pacotes', len(_uad_unsafe_cache))
    return _uad_unsafe_cache
def consultar_uad(package_name):
    if not package_name:
        return
    uad = _carregar_uad()
    info = uad.get(package_name)
    if isinstance(info, dict):
        return {'removal': info.get('removal', 'Unknown'), 'list': info.get('list', 'Unknown'), 'description': info.get('description', '')}
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
def listar_launchers(adb_manager):
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
            logger.debug('%d launchers HOME detectados', len(resultado))
    except Exception:
        logger.debug('Falha ao listar launchers', exc_info=True)
    return frozenset(resultado)
def obter_protegidos(adb_manager=None):
    protegidos = set(_CRITICAL_PKGS)
    try:
        uad_unsafe = _obter_uad_unsafe()
        protegidos.update(uad_unsafe)
    except Exception:
        pass
    if adb_manager:
        try:
            ativo = detectar_launcher_ativo(adb_manager)
            if ativo:
                protegidos.add(ativo)
        except Exception:
            pass
        try:
            todos = listar_launchers(adb_manager)
            protegidos.update(todos)
        except Exception:
            pass
    return frozenset(protegidos)
def is_protegido(package_name, protegidos=None):
    if not package_name:
        return False
    if protegidos is None:
        protegidos = _CRITICAL_PKGS | _obter_uad_unsafe()
    if package_name in protegidos:
        return True
    if any((package_name.startswith(prefix) for prefix in _CRITICAL_PREFIXES)):
        return True
    uad_info = consultar_uad(package_name)
    if uad_info and uad_info.get('removal') == 'Unsafe':
        return True
    return False
