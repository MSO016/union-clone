'''
=============================================================================
ADWARE CSI - Crime Scene Investigation
=============================================================================
M├│dulo de investiga├º├úo forense inteligente de adware/PUA.
Baseado em pesquisas cient├¡ficas:
- BPFroid (arxiv.org/abs/2105.14344) - Monitoramento comportamental
- MadDroid (arxiv.org/abs/2002.01656) - Detec├º├úo de ads maliciosos
- FraudDroid (arxiv.org/abs/1709.01213) - Fraude em an├║ncios
Funcionalidades:
1. Detec├º├úo de instala├º├úo recente (Ôëñ10 dias)
2. An├ílise de abuso de foreground/bateria
3. Varredura de logcat para padr├Áes de SDKs de ads
4. Sistema de pontua├º├úo inteligente
5. Triagem baseada em evid├¬ncias comportamentais
Autor: TECH UNION SOLUTIONS
Data: 2024
=============================================================================
'''
import os
import re
import time
import logging
import traceback
from datetime import datetime, timezone
logger = logging.getLogger(__name__)
class AdwareCSI:
    '''
    Crime Scene Investigation para Adware/PUA.
    Implementa triagem inteligente baseada em comportamento e evid├¬ncias.
    '''
    def __init__(self, adb_manager):
        '''
Inicializa o investigador CSI.
Args:
    adb_manager: Inst├óncia do ADBManager para comunica├º├úo com dispositivo
'''
        self.adb = adb_manager
        if not self.adb:
            logger.error('AdwareCSI: ADBManager n├úo fornecido!')
            raise ValueError('ADBManager ├® obrigat├│rio para AdwareCSI')
        self.config = {'recent_days_threshold': 10, 'min_score_threshold': 4, 'logcat_capture_seconds': 12, 'max_results': 50}
        self.foreground_abuse_permissions = ['android.permission.FOREGROUND_SERVICE', 'android.permission.FOREGROUND_SERVICE_DATA_SYNC', 'android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK', 'android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS', 'android.permission.WAKE_LOCK', 'android.permission.REQUEST_COMPANION_RUN_IN_BACKGROUND']
        self.overlay_permissions = ['android.permission.SYSTEM_ALERT_WINDOW', 'android.permission.BIND_ACCESSIBILITY_SERVICE']
        self.persistence_permissions = ['android.permission.RECEIVE_BOOT_COMPLETED']
        self.logcat_patterns = {'critical': ['(?i)(SYSTEM_ALERT_WINDOW|TYPE_APPLICATION_OVERLAY)', '(?i)(force.*click|auto.*click|simulate.*touch)', '(?i)(inject.*event|dispatchTouchEvent)'], 'high': ['(?i)(admob|doubleclick|googlesyndication|googleads)', '(?i)(facebook.*ads|fb.*audience|fban)', '(?i)(unity.*ads|unityservices)', '(?i)(applovin|maxmediation|maxsdk)', '(?i)(ironsource|supersonic)', '(?i)(intent.*VIEW.*http|openUrl.*http)'], 'medium': ['(?i)(vungle|chartboost|inmobi|mopub|startapp|adcolony)', '(?i)(show.*ad|load.*ad|request.*ad|display.*ad)', '(?i)(market://details|play\\.google\\.com/store)', '(?i)(interstitial|rewarded.*ad|banner.*ad)'], 'low': ['(?i)(analytics|tracking|pixel|telemetry)', '(?i)(ad.*request|ad.*response|ad.*loaded)']}
        self.dangerous_combinations = [{'permissions': ['SYSTEM_ALERT_WINDOW', 'REQUEST_IGNORE_BATTERY_OPTIMIZATIONS'], 'bonus': 20, 'reason': 'ÔÜá´©Å Combo: Overlay + Ignora Bateria (pop-ups persistentes)'}, {'permissions': ['RECEIVE_BOOT_COMPLETED', 'FOREGROUND_SERVICE', 'REQUEST_IGNORE_BATTERY_OPTIMIZATIONS'], 'bonus': 25, 'reason': 'ÔÜá´©Å Combo: Boot + Foreground + Bateria (servi├ºo persistente)'}, {'permissions': ['BIND_ACCESSIBILITY_SERVICE', 'SYSTEM_ALERT_WINDOW'], 'bonus': 30, 'reason': 'ÔÜá´©Å Combo: Acessibilidade + Overlay (pode clicar automaticamente)'}, {'permissions': ['RECEIVE_BOOT_COMPLETED', 'SYSTEM_ALERT_WINDOW'], 'bonus': 15, 'reason': 'ÔÜá´©Å Combo: Boot + Overlay (ads no boot)'}]
        self.trusted_packages = ['com.android.', 'com.google.android.', 'com.samsung.', 'com.miui.', 'com.xiaomi.', 'com.huawei.', 'com.oppo.', 'com.vivo.', 'com.sec.android.', 'com.qualcomm.', 'com.mediatek.']
    def investigate(self, callback=None):
        '''
Executa investiga├º├úo forense completa do dispositivo.
Args:
    callback: Fun├º├úo para atualizar progresso na UI (opcional)
Returns:
    dict: Resultados da investiga├º├úo com suspeitos e evid├¬ncias
'''
        if callback:
            callback('­ƒöì [CSI] Iniciando investiga├º├úo forense...')
        if not self.adb.is_device_connected():
            if callback:
                callback('ÔØî Nenhum dispositivo conectado!')
            return {'error': 'Nenhum dispositivo conectado', 'suspects': []}
        results = {'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'device_info': self._get_device_info(), 'suspects': [], 'statistics': {'total_apps_analyzed': 0, 'total_suspects': 0, 'critical_risk': 0, 'high_risk': 0, 'medium_risk': 0, 'low_risk': 0}, 'phases': {}}
        try:
            if callback:
                callback('[ ÔÜí ] SIMPLES: iniciando...')
                callback('ÔÇó Captura ao vivo...')
            logcat_hits = self._capture_logcat_live(callback)
            results['phases']['logcat'] = {'hits': len(logcat_hits), 'packages': list(logcat_hits.keys())[:10]}
            if callback:
                callback('ÔÇó Obtendo apps instalados...')
            user_apps = self._get_user_apps()
            results['statistics']['total_apps_analyzed'] = len(user_apps)
            if callback:
                callback(f'ÔÇó Candidatos: {len(user_apps)} | Omitidos: 0')
            if callback:
                callback(f'[­ƒö¼] COMPLETO: peneira fina (Ôëñ{self.config['recent_days_threshold']} dias, evid├¬ncias)...')
            suspects = []
            recent_count = 0
            for i, pkg in enumerate(user_apps):
                if self._is_trusted(pkg):
                    continue
                analysis = self._analyze_package(pkg, logcat_hits)
                if analysis['is_recent']:
                    recent_count += 1
                if analysis['score'] >= self.config['min_score_threshold']:
                    suspects.append(analysis)
                if not callback:
                    continue
                if i % 20 != 0:
                    continue
                if i > 0:
                    callback(f'  ÔåÆ Analisando... {i}/{len(user_apps)}')
            if callback:
                callback(f'ÔÇó F2R: recentes (Ôëñ{self.config['recent_days_threshold']}d) ÔåÆ triagem...')
        except Exception as e:
            logger.error(f'Erro na investiga├º├úo CSI: {str(e)}')
            logger.error(traceback.format_exc())
            if callback:
                callback(f'ÔØî Erro na investiga├º├úo: {str(e)}')
            return {'error': str(e), 'suspects': []}
        try:
            recent_suspects = [s for s in suspects if s.get('is_recent')]
            safe_omitted = recent_count - len(recent_suspects)
            if callback:
                callback(f'  ÔåÆ Triagem recentes: +{len(recent_suspects)} | omitidos seguros: {safe_omitted}')
            if callback:
                callback('ÔÇó Ordenar flags...')
            suspects.sort(key=(lambda x: x['score']), reverse=True)
            suspects = suspects[:self.config['max_results']]
            for suspect in suspects:
                score = suspect['score']
                if score >= 50:
                    suspect['risk_level'] = 'CR├ìTICO'
                    results['statistics']['critical_risk'] += 1
                elif score >= 30:
                    suspect['risk_level'] = 'ALTO'
                    results['statistics']['high_risk'] += 1
                elif score >= 15:
                    suspect['risk_level'] = 'M├ëDIO'
                    results['statistics']['medium_risk'] += 1
                else:
                    suspect['risk_level'] = 'BAIXO'
                    results['statistics']['low_risk'] += 1
            results['suspects'] = suspects
            results['statistics']['total_suspects'] = len(suspects)
            if callback:
                callback('')
                callback('============================================================')
                callback('Ô£à [CSI] Investiga├º├úo conclu├¡da!')
                callback(f'­ƒôè Apps analisados: {results['statistics']['total_apps_analyzed']}')
                callback(f'­ƒÜ¿ Suspeitos encontrados: {results['statistics']['total_suspects']}')
                if results['statistics']['critical_risk'] > 0:
                    callback(f'   ­ƒö┤ Cr├¡tico: {results['statistics']['critical_risk']}')
                if results['statistics']['high_risk'] > 0:
                    callback(f'   ­ƒƒá Alto: {results['statistics']['high_risk']}')
                if results['statistics']['medium_risk'] > 0:
                    callback(f'   ­ƒƒí M├®dio: {results['statistics']['medium_risk']}')
                if results['statistics']['low_risk'] > 0:
                    callback(f'   ­ƒƒó Baixo: {results['statistics']['low_risk']}')
                callback('============================================================')
            return results
        except Exception as e:
            logger.error(f'Erro na investiga├º├úo CSI: {str(e)}')
            logger.error(traceback.format_exc())
            if callback:
                callback(f'ÔØî Erro na investiga├º├úo: {str(e)}')
            return {'error': str(e), 'suspects': []}
    def _get_device_info(self):
        '''Obt├®m informa├º├Áes do dispositivo.'''
        try:
            return self.adb.get_device_info()
        except Exception as e:
            logger.error(f'Erro ao obter info do dispositivo: {str(e)}')
            return {'error': str(e)}
    def _get_user_apps(self):
        '''Obt├®m lista de apps instalados pelo usu├írio (n├úo sistema).'''
        try:
            result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'pm', 'list', 'packages', '-3'])
            apps = []
            for line in result.split('\n'):
                if line.startswith('package:'):
                    pkg = line[8:].strip()
                    if pkg:
                        apps.append(pkg)
            return apps
        except Exception as e:
            logger.error(f'Erro ao obter apps: {str(e)}')
            return []
    def _is_trusted(self, package):
        '''Verifica se o pacote ├® confi├ível (sistema).'''
        for prefix in self.trusted_packages:
            if package.startswith(prefix):
                return True
        return False
    def _capture_logcat_live(self, callback=None):
        '''
Captura logcat ao vivo e busca por padr├Áes de ads.
Returns:
    dict: {package: {"hits": int, "severity": str, "patterns": list}}
'''
        try:
            if callback:
                callback('ÔÇó Logcat (Ads)...')
            self.adb._run_adb_command([self.adb.adb_path, 'logcat', '-c'])
            time.sleep(self.config['logcat_capture_seconds'])
            result = self.adb._run_adb_command([self.adb.adb_path, 'logcat', '-d', '-v', 'brief'])
            hits = {}
            for line in result.split('\n'):
                if not line.strip():
                    continue
                pkg_match = re.search('([a-zA-Z][a-zA-Z0-9_]*(?:\\.[a-zA-Z][a-zA-Z0-9_]*){2,})', line)
                if not pkg_match:
                    continue
                pkg = pkg_match.group(1)
                if self._is_trusted(pkg):
                    continue
                for severity, patterns in self.logcat_patterns.items():
                    for pattern in patterns:
                        if not re.search(pattern, line):
                            continue
                        if pkg not in hits:
                            hits[pkg] = {'hits': 0, 'severity': 'low', 'patterns': []}
                        hits[pkg]['hits'] += 1
                        pattern_short = pattern[:40].replace('(?i)', '')
                        if pattern_short not in hits[pkg]['patterns']:
                            hits[pkg]['patterns'].append(pattern_short)
                        severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
                        if severity_order[severity] > severity_order[hits[pkg]['severity']]:
                            hits[pkg]['severity'] = severity
                        break
                continue
            if callback:
                callback('ÔÇó Flags overlay/top UI...')
            return hits
        except Exception as e:
            logger.error(f'Erro ao capturar logcat: {str(e)}')
            return {}
    def _analyze_package(self, package, logcat_hits):
        '''
Analisa um pacote individual e calcula seu score.
Args:
    package: Nome do pacote
    logcat_hits: Hits de logcat capturados anteriormente
Returns:
    dict: An├ílise completa do pacote
'''
        analysis = {'package': package, 'app_name': package.split('.')[-1].capitalize(), 'score': 0, 'reasons': [], 'is_recent': False, 'days_since_install': None, 'permissions_detected': [], 'risk_level': 'BAIXO'}
        try:
            package_dump = self.adb._run_adb_command([self.adb.adb_path, 'shell', f'dumpsys package {package}'])
            analysis['app_name'] = self._get_app_label(package, package_dump)
            install_info = self._parse_install_time(package_dump)
            if install_info:
                analysis['days_since_install'] = install_info.get('days')
                analysis['is_recent'] = install_info.get('is_recent', False)
                if install_info.get('is_recent'):
                    days = install_info.get('days', 0)
                    if days <= 3:
                        analysis['score'] += 15
                        analysis['reasons'].append('recente(Ôëñ3d)+15')
                    elif days <= 7:
                        analysis['score'] += 10
                        analysis['reasons'].append('recente(Ôëñ7d)+10')
                    else:
                        analysis['score'] += 5
                        analysis['reasons'].append(f'recente(Ôëñ{self.config['recent_days_threshold']}d)+5')
            overlay_score, overlay_reasons = self._check_overlay_permissions(package_dump)
            if overlay_score > 0:
                analysis['score'] += overlay_score
                analysis['reasons'].extend(overlay_reasons)
                analysis['permissions_detected'].append('OVERLAY')
            fg_score, fg_reasons = self._check_foreground_abuse(package_dump)
            if fg_score > 0:
                analysis['score'] += fg_score
                analysis['reasons'].extend(fg_reasons)
                analysis['permissions_detected'].append('FOREGROUND')
            boot_score, boot_reasons = self._check_boot_persistence(package_dump)
            if boot_score > 0:
                analysis['score'] += boot_score
                analysis['reasons'].extend(boot_reasons)
                analysis['permissions_detected'].append('BOOT')
            combo_score, combo_reasons = self._check_dangerous_combinations(package_dump)
            if combo_score > 0:
                analysis['score'] += combo_score
                analysis['reasons'].extend(combo_reasons)
            if package in logcat_hits:
                hit_data = logcat_hits[package]
                hit_score = self._calculate_logcat_score(hit_data)
                if hit_score > 0:
                    analysis['score'] += hit_score
                    analysis['reasons'].append(f'logcat({hit_data['severity']}) hits={hit_data['hits']} +{hit_score}')
        except Exception as e:
            logger.error(f'Erro ao analisar {package}: {str(e)}')
        return analysis
    def _parse_install_time(self, package_dump):
        '''Extrai e analisa o tempo de instala├º├úo do pacote.'''
        try:
            patterns = ['firstInstallTime=(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2})', 'firstInstallTime=(\\d+)']
            for pattern in patterns:
                match = re.search(pattern, package_dump)
                if match:
                    raw = match.group(1)
                    try:
                        try:
                            if len(raw) > 10:
                                dt = datetime.strptime(raw[:19], '%Y-%m-%d %H:%M:%S')
                                ts = dt.timestamp()
                            else:
                                ts = int(raw) / 1000
                            now = datetime.now().timestamp()
                            days = (now - ts) / 86400
                        except ValueError:
                            continue
                    except Exception as e:
                        logger.debug(f'Erro ao parsear install time: {str(e)}')
                    return {'timestamp': ts, 'days': round(days, 1), 'is_recent': days <= self.config['recent_days_threshold']}
        except Exception as e:
            logger.debug(f'Erro ao parsear install time: {str(e)}')
        try:
            return
        except Exception as e:
            logger.debug(f'Erro ao parsear install time: {str(e)}')
    def _check_overlay_permissions(self, package_dump):
        '''Verifica permiss├Áes de overlay/top UI.'''
        score = 0
        reasons = []
        if 'android.permission.SYSTEM_ALERT_WINDOW' in package_dump:
            score += 15
            reasons.append('overlay/topUI+15')
        if 'android.permission.BIND_ACCESSIBILITY_SERVICE' in package_dump:
            score += 10
            reasons.append('acessibilidade+10')
        return score, reasons
    def _check_foreground_abuse(self, package_dump):
        '''Verifica abuso de foreground service e bateria.'''
        score = 0
        reasons = []
        if 'android.permission.FOREGROUND_SERVICE' in package_dump:
            score += 5
            reasons.append('foreground+5')
        if 'android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS' in package_dump:
            score += 10
            reasons.append('bateria/ignorar+10')
        if 'android.permission.WAKE_LOCK' in package_dump:
            score += 3
            reasons.append('wakelock+3')
        return score, reasons
    def _check_boot_persistence(self, package_dump):
        '''Verifica se o app persiste no boot.'''
        score = 0
        reasons = []
        if 'android.permission.RECEIVE_BOOT_COMPLETED' in package_dump:
            score += 8
            reasons.append('boot+persist+8')
        return score, reasons
    def _check_dangerous_combinations(self, package_dump):
        '''Verifica combina├º├Áes perigosas de permiss├Áes.'''
        score = 0
        reasons = []
        for combo in self.dangerous_combinations:
            all_present = all((f'android.permission.{perm}' in package_dump for perm in combo['permissions']))
            if all_present:
                score += combo['bonus']
                reasons.append(combo['reason'])
        return score, reasons
    def _calculate_logcat_score(self, hit_data):
        '''Calcula pontua├º├úo baseada nos hits de logcat.'''
        severity_scores = {'critical': 20, 'high': 12, 'medium': 6, 'low': 2}
        base_score = severity_scores.get(hit_data['severity'], 0)
        hit_bonus = min(8, hit_data['hits'])
        return base_score + hit_bonus
    def _get_app_label(self, package, package_dump=None):
        """Obt├®m o nome amig├ível do app.
Args:
    package: nome do pacote.
    package_dump: saida de 'dumpsys package <pkg>' ja obtida. Se
        fornecida, e reaproveitada (evita uma 2a chamada ADB
        identica). Se None, mantem o comportamento original
        executando o dumpsys ÔÇö fallback total preservado.
"""
        try:
            result = package_dump
            if result is None:
                result = self.adb._run_adb_command([self.adb.adb_path, 'shell', f'dumpsys package {package}'])
            result = result or ''
            match = re.search('Application Label: (.+)', result)
            if match:
                return match.group(1).strip()
            return package.split('.')[-1].capitalize()
        except Exception:
            return package.split('.')[-1].capitalize()
