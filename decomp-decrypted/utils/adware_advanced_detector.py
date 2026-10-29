import os
import re
import json
import time
import logging
import traceback
from datetime import datetime
from app.utils._pkg_defs import is_manufacturer_adware
logger = logging.getLogger(__name__)
class AdvancedAdwareDetector:
    def __init__(self, adb_manager):
        self.adb = adb_manager
        if not self.adb:
            logger.error('AdvancedAdwareDetector: ADBManager n├úo fornecido!')
            raise ValueError('ADBManager ├® obrigat├│rio para AdvancedAdwareDetector')
        self.blacklist = self._load_blacklist()
        self.dangerous_permissions = ['READ_SMS', 'SEND_SMS', 'RECEIVE_SMS', 'CALL_PHONE', 'RECORD_AUDIO', 'CAMERA', 'ACCESS_FINE_LOCATION', 'ACCESS_COARSE_LOCATION', 'READ_CONTACTS', 'READ_CALL_LOG', 'READ_PHONE_STATE', 'WRITE_SETTINGS', 'REQUEST_INSTALL_PACKAGES', 'SYSTEM_ALERT_WINDOW', 'BIND_NOTIFICATION_LISTENER_SERVICE']
        self.trusted_apps = ['com.android.', 'android', 'com.google.android.', 'com.google.', 'com.samsung.', 'com.sec.android.', 'com.sec.', 'com.knox.', 'com.miui.', 'com.xiaomi.', 'com.mi.', 'com.huawei.', 'com.honor.', 'com.hihonor.', 'com.motorola.', 'com.motorola.launcher3', 'com.oppo.', 'com.oppoex.', 'com.oneplus.', 'com.realme.', 'com.coloros.', 'com.heytap.', 'com.oplus.', 'oplus', 'com.vivo.', 'com.lge.', 'com.sony.', 'com.qualcomm.', 'com.mediatek.', 'com.transsion.', 'com.ontim.', 'com.itel.', 'com.sprd.', 'com.spreadtrum.', 'com.unisoc.', 'com.teslacoilsw.launcher', 'com.microsoft.launcher', 'com.transsion.hilauncher']
    def _load_blacklist(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            json_path = os.path.join(project_root, 'app', 'database', 'blacklist_union_apps_v2.json')
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    json_list = json_data.get('blacklist_packages', [])
                    logger.info(f'Lista adicional de apps maliciosos carregada: {len(json_list)} apps')
                    return json_list
            alt_path = os.path.join(os.path.dirname(current_dir), 'database', 'blacklist_union_apps_v2.json')
            if os.path.exists(alt_path):
                with open(alt_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    json_list = json_data.get('blacklist_packages', [])
                    logger.info(f'Lista adicional de apps maliciosos carregada: {len(json_list)} apps')
                    return json_list
        except Exception as e:
            logger.error(f'Erro ao carregar lista do JSON: {str(e)}')
            return ['com.findjunks.delerclock', 'com.apidev.horrorcraft_themimicer', 'com.snaptube.premium', 'com.whoyaho.tanghulu']
        return ['com.findjunks.delerclock', 'com.apidev.horrorcraft_themimicer', 'com.snaptube.premium', 'com.whoyaho.tanghulu', 'nb.ph.fixer', 'com.Happy.Video']
    def analyze_device(self, callback=None):
        if callback:
            callback('­ƒöì Iniciando an├ílise avan├ºada de adware...')
        if not self.adb.is_device_connected():
            if callback:
                callback('ÔØî Nenhum dispositivo conectado!')
            return {'error': 'Nenhum dispositivo conectado'}
        results = {'suspicious_apps': {}, 'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'device_info': self._get_device_info(), 'total_apps': 0, 'total_suspicious': 0, 'high_risk': 0, 'medium_risk': 0, 'low_risk': 0}
        if callback:
            callback('­ƒô▒ Obtendo informa├º├Áes do dispositivo e apps instalados...')
        user_apps = self._get_user_apps()
        results['total_apps'] = len(user_apps)
        if callback:
            callback(f'­ƒôª Encontrados {len(user_apps)} apps instalados pelo usu├írio')
        if callback:
            callback('­ƒöÄ Procurando por apps com recursos suspeitos...')
        overlay_apps = self._get_overlay_apps()
        admin_apps = self._get_admin_apps()
        boot_apps = self._get_boot_apps()
        accessibility_apps = self._get_accessibility_apps()
        high_cpu_apps = self._get_high_cpu_apps()
        if callback:
            callback('­ƒöö Resultados iniciais:')
            callback(f'  ÔÇó {len(overlay_apps)} apps com permiss├úo de overlay')
            callback(f'  ÔÇó {len(admin_apps)} apps com privil├®gios de administrador')
            callback(f'  ÔÇó {len(boot_apps)} apps que iniciam na inicializa├º├úo')
            callback(f'  ÔÇó {len(accessibility_apps)} apps com permiss├Áes de acessibilidade')
            callback(f'  ÔÇó {len(high_cpu_apps)} apps com uso elevado de CPU')
        if callback:
            callback('ÔÜû´©Å Calculando pontua├º├úo de risco para cada app...')
        for app in user_apps:
            if self._is_trusted_app(app):
                continue
            score = 0
            reasons = []
            if self._is_in_blacklist(app):
                score += 50
                reasons.append('App na lista de apps maliciosos conhecidos')
            if app in overlay_apps:
                score += 30
                reasons.append('Permiss├úo de overlay (desenhar sobre outros apps)')
            if app in admin_apps:
                score += 25
                reasons.append('Privil├®gios de administrador do dispositivo')
            if app in boot_apps:
                score += 20
                reasons.append('Inicia automaticamente com o sistema')
            if app in accessibility_apps:
                score += 15
                reasons.append('Permiss├Áes de acessibilidade ativas')
            if app in high_cpu_apps:
                cpu_percentage = high_cpu_apps[app]
                cpu_points = min(25, int(cpu_percentage * 0.5))
                score += cpu_points
                reasons.append(f'Uso elevado de CPU ({cpu_percentage:.1f}%)')
            dangerous_perms = self._get_dangerous_permissions(app)
            if dangerous_perms:
                perm_points = min(30, len(dangerous_perms) * 5)
                score += perm_points
                reasons.append(f'Permiss├Áes perigosas: {', '.join(dangerous_perms)}')
            if self._has_suspicious_name_pattern(app):
                score += 10
                reasons.append('Nome do pacote com padr├úo suspeito')
            if not score > 0:
                continue
            results['suspicious_apps'][app] = {'score': score, 'reasons': reasons, 'app_name': self._get_app_label(app), 'risk_level': 'Alto' if score > 70 else 'M├®dio' if score > 40 else 'Baixo'}
            if score > 70:
                results['high_risk'] += 1
                continue
            if score > 40:
                results['medium_risk'] += 1
                continue
            results['low_risk'] += 1
            continue
        results['suspicious_apps'] = dict(sorted(results['suspicious_apps'].items(), key=(lambda item: item[1]['score']), reverse=True))
        results['total_suspicious'] = len(results['suspicious_apps'])
        if callback:
            callback(f'Ô£à An├ílise conclu├¡da! Encontrados {results['total_suspicious']} apps suspeitos')
            callback(f'  ÔÇó {results['high_risk']} apps de alto risco')
            callback(f'  ÔÇó {results['medium_risk']} apps de risco m├®dio')
            callback(f'  ÔÇó {results['low_risk']} apps de baixo risco')
        return results
    def _get_device_info(self):
        try:
            device_info = self.adb.get_device_info()
            return device_info
        except Exception as e:
            logger.error(f'Erro ao obter informa├º├Áes do dispositivo: {str(e)}')
            return {'error': str(e)}
    def _get_user_apps(self):
        try:
            result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'pm', 'list', 'packages', '-3'])
            user_apps = []
            for line in result.split('\n'):
                if line.startswith('package:'):
                    app_name = line[8:].strip()
                    if app_name:
                        user_apps.append(app_name)
            return user_apps
        except Exception as e:
            logger.error(f'Erro ao obter apps do usu├írio: {str(e)}')
            return []
    def _get_overlay_apps(self):
        try:
            result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys window windows'])
            overlay_apps = []
            for line in result.split('\n'):
                if 'SYSTEM_ALERT_WINDOW' not in line:
                    continue
                if 'package=' in line:
                    match = re.search('package=([^ ]+)', line)
                    if match:
                        package_name = match.group(1)
                        if not package_name:
                            continue
                        if package_name not in overlay_apps:
                            overlay_apps.append(package_name)
            return overlay_apps
        except Exception as e:
            logger.error(f'Erro ao obter apps com overlay: {str(e)}')
            return []
    def _get_admin_apps(self):
        try:
            result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys device_policy'])
            admin_apps = []
            for line in result.split('\n'):
                if 'admin=' in line:
                    match = re.search('admin=\\{([^}]+)\\}', line)
                    if match:
                        admin_name = match.group(1).strip()
                        if not admin_name:
                            continue
                        if admin_name not in admin_apps:
                            admin_apps.append(admin_name)
            return admin_apps
        except Exception as e:
            logger.error(f'Erro ao obter apps com privil├®gios de admin: {str(e)}')
            return []
    def _get_boot_apps(self):
        try:
            result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'pm', 'query-receivers', '--components', '-a', 'android.intent.action.BOOT_COMPLETED'], timeout=30)
            boot_apps = []
            if result:
                for line in result.split('\n'):
                    line = line.strip()
                    if '/' in line:
                        pkg = line.split('/')[0].strip()
                        if not pkg:
                            continue
                        if pkg in boot_apps:
                            continue
                        if len(pkg) > 3:
                            boot_apps.append(pkg)
            if not boot_apps:
                result2 = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys', 'package', '-f'], timeout=30)
                if result2:
                    current_pkg = None
                    for line in result2.split('\n'):
                        pkg_match = re.search('Package \\[([^\\]]+)\\]', line)
                        if pkg_match:
                            current_pkg = pkg_match.group(1)
                        else:
                            if 'RECEIVE_BOOT_COMPLETED' not in line:
                                continue
                            if not current_pkg:
                                continue
                            if current_pkg not in boot_apps:
                                boot_apps.append(current_pkg)
            return boot_apps
        except Exception as e:
            logger.debug('Erro ao obter apps que iniciam no boot: %s', e)
            return []
    def _get_accessibility_apps(self):
        try:
            result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'settings get secure enabled_accessibility_services'])
            accessibility_apps = []
            if result and result.strip() != 'null':
                for service in result.strip().split(':'):
                    if '/' in service:
                        app_name = service.split('/')[0]
                        if not app_name:
                            continue
                        if app_name not in accessibility_apps:
                            accessibility_apps.append(app_name)
            return accessibility_apps
        except Exception as e:
            logger.error(f'Erro ao obter apps com acessibilidade: {str(e)}')
            return []
    def _get_high_cpu_apps(self):
        try:
            result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys cpuinfo'])
            high_cpu_apps = {}
            total_cpu = 0
            user_apps = self._get_user_apps()
            for line in result.split('\n'):
                if '%' in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        try:
                            cpu_percentage = float(parts[0].replace('%', ''))
                            for app in user_apps:
                                if app not in line:
                                    continue
                                if app in high_cpu_apps:
                                    high_cpu_apps[app] += cpu_percentage
                                else:
                                    high_cpu_apps[app] = cpu_percentage
                                total_cpu += cpu_percentage
                                break
                        except ValueError:
                            continue
                        try:
                            pass
                        except ValueError:
                            continue
        except Exception as e:
            logger.error(f'Erro ao obter apps com alto uso de CPU: {str(e)}')
            return {}
        try:
            return {app: percentage for app, percentage in high_cpu_apps.items() if percentage > 2}
        except Exception as e:
            logger.error(f'Erro ao obter apps com alto uso de CPU: {str(e)}')
            return {}
    def _get_dangerous_permissions(self, package):
        try:
            result = self.adb._run_adb_command([self.adb.adb_path, 'shell', f'dumpsys package {package}'])
            dangerous_perms = []
            for perm in self.dangerous_permissions:
                if perm in result:
                    dangerous_perms.append(perm)
            return dangerous_perms
        except Exception as e:
            logger.error(f'Erro ao verificar permiss├Áes de {package}: {str(e)}')
            return []
    def _is_in_blacklist(self, package):
        return package in self.blacklist
    def _is_trusted_app(self, package):
        if is_manufacturer_adware(package):
            return False
        return any((package.startswith(prefix) for prefix in self.trusted_apps))
    def _has_suspicious_name_pattern(self, package):
        suspicious_patterns = ['ads', 'ad.', 'advert', 'notification', 'notify', 'sponsor', 'analytics', 'tracker', 'cleaner', 'booster', 'speedup', 'cache', 'battery', 'virus', 'antivirus', 'security', 'clean', 'master', 'boost', 'speed', 'fast', 'quick', 'optimizer', 'doctor', 'memory', 'ram', 'cpu', 'cooler', 'flash', 'share', 'transfer', 'browser', 'scan', 'scanner']
        return any((pattern in package.lower() for pattern in suspicious_patterns))
    def _get_app_label(self, package):
        try:
            result = self.adb._run_adb_command([self.adb.adb_path, 'shell', f"dumpsys package {package} | grep -A1 'Application Label'"])
            match = re.search('Application Label: (.+)', result)
            if match:
                return match.group(1).strip()
            return package.split('.')[-1].capitalize()
        except Exception as e:
            return package.split('.')[-1].capitalize()
    def scan_realtime(self, duration=60, callback=None):
        if callback:
            callback(f'­ƒöì Iniciando monitoramento de adware em tempo real por {duration} segundos...')
        start_time = time.time()
        end_time = start_time + duration
        results = {'suspicious_activities': [], 'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'duration': duration, 'active_apps': set()}
        cpu_snapshots = {}
        intervals = min(10, max(3, duration // 15))
        interval_duration = duration / intervals
        for i in range(intervals):
            elapsed_time = time.time() - start_time
            remaining_time = max(0, int(duration - elapsed_time))
            if callback:
                callback(f'ÔÅ│ Monitorando atividades ({i + 1}/{intervals}) - Restam {remaining_time}s')
            current_cpu = self._get_high_cpu_apps()
            for app, cpu in current_cpu.items():
                if app in cpu_snapshots and cpu > cpu_snapshots[app] * 1.5 and cpu > 5:
                    results['suspicious_activities'].append({'app': app, 'timestamp': datetime.now().strftime('%H:%M:%S'), 'activity': f'Pico de CPU: {cpu:.1f}% (era {cpu_snapshots[app]:.1f}%)', 'type': 'cpu_spike'})
                cpu_snapshots[app] = cpu
                results['active_apps'].add(app)
            if i > 0:
                self._check_suspicious_navigation(results, callback)
            if not i < intervals - 1:
                continue
            elapsed_time = time.time() - start_time
            time_left = duration - elapsed_time
            sleep_time = min(interval_duration, time_left)
            if not sleep_time > 0:
                continue
            time.sleep(sleep_time)
            continue
        total_time = time.time() - start_time
        results['actual_duration'] = round(total_time, 1)
        try:
            results = self._refinar_por_correlacao(results, callback=callback)
        except Exception as refino_err:
            logger.debug(f'refino indisponivel: {type(refino_err).__name__}')
        if callback:
            callback(f'Ô£à Monitoramento conclu├¡do! Dura├º├úo real: {results['actual_duration']}s')
            if results['suspicious_activities']:
                callback(f'ÔÜá´©Å Detectadas {len(results['suspicious_activities'])} atividades suspeitas')
                return results
            callback('Ô£à Nenhuma atividade suspeita detectada no per├¡odo')
        return results
    def _refinar_por_correlacao(self, results, callback=None):
        original = results.get('suspicious_activities', []) or []
        try:
            overlay = set(self._get_overlay_apps() or [])
        except Exception:
            overlay = set()
        try:
            boot = set(self._get_boot_apps() or [])
        except Exception:
            boot = set()
        try:
            accessibility = set(self._get_accessibility_apps() or [])
        except Exception:
            accessibility = set()
        fg_counts = {}
        try:
            if callback:
                callback('­ƒöÄ Confirmando comportamento na tela (anti-falso-positivo)...')
            fg = self.monitor_screen_changes(duration=12, callback=None) or {}
            candidate = fg.get('foreground_suspects', {})
            if isinstance(candidate, dict):
                fg_counts = candidate
        except Exception as fg_err:
            logger.debug(f'foreground indisponivel no refino: {type(fg_err).__name__}')
            fg_counts = {}
        if not overlay and not boot and not accessibility and not fg_counts:
            return results
        def _score(pkg):
            s = 0
            c = fg_counts.get(pkg, 0)
            if c >= 3:
                s += 50
            elif c == 2:
                s += 20
            if pkg in overlay:
                s += 25
            if pkg in accessibility:
                s += 20
            if pkg in boot:
                s += 15
            return s
        corte = 40
        refinados = []
        vistos = set()
        for atividade in original:
            try:
                pkg = (atividade.get('app') or '').strip()
                if pkg:
                    if pkg == 'Desconhecido' or self._is_trusted_app(pkg):
                        continue
                    total = _score(pkg) + 10
                    if total >= corte:
                        novo = dict(atividade)
                        novo['score'] = total
                        novo['severity'] = 'Alto' if total >= 70 else 'M├®dio'
                        refinados.append(novo)
                        vistos.add(pkg)
            except Exception:
                continue
        for pkg, cnt in list(fg_counts.items()):
            try:
                if cnt < 3 or pkg in vistos:
                    continue
            except Exception:
                continue
            try:
                if not pkg or self._is_trusted_app(pkg):
                    continue
            except Exception:
                continue
            try:
                total = _score(pkg)
                refinados.append({'app': pkg, 'timestamp': datetime.now().strftime('%H:%M:%S'), 'activity': f'Apareceu {cnt}x na tela (comportamento de pop-up)', 'type': 'foreground', 'score': total, 'severity': 'Alto' if total >= 70 else 'M├®dio'})
                vistos.add(pkg)
            except Exception:
                continue
        results['suspicious_activities'] = refinados
        return results
    def _check_suspicious_navigation(self, results, callback=None):
        try:
            logcat_result = self.adb._run_adb_command([self.adb.adb_path, 'logcat', '-d', '-v', 'time', '-s', 'ActivityManager:I'], timeout=15)
            if not logcat_result:
                return
            nav_count = 0
            for line in logcat_result.split('\n'):
                if nav_count >= 10:
                    return
                if 'android.intent.action.VIEW' not in line:
                    continue
                app = self._extract_app_from_logcat(line)
                if app == 'Desconhecido' or self._is_trusted_app(app):
                    continue
                is_market = 'market://' in line
                is_url = 'http:' in line or 'https:' in line
                if is_market:
                    results['suspicious_activities'].append({'app': app, 'timestamp': datetime.now().strftime('%H:%M:%S'), 'activity': 'Tentativa de abrir Google Play Store', 'type': 'playstore_navigation'})
                    nav_count += 1
                    if callback:
                        callback('Detectada tentativa de abrir Google Play Store!')
                        continue
                    continue
                if not is_url:
                    continue
                results['suspicious_activities'].append({'app': app, 'timestamp': datetime.now().strftime('%H:%M:%S'), 'activity': 'Tentativa de abrir URL externa', 'type': 'url_navigation'})
                nav_count += 1
                if not callback:
                    continue
                callback('Detectada tentativa de abrir URL externa!')
                continue
            return
        except Exception as e:
            logger.debug('Erro ao verificar navegacao suspeita: %s', e)
    def _extract_app_from_logcat(self, logcat_line):
        try:
            pid_match = re.search('\\(\\s*(\\d+)\\)', logcat_line)
            if pid_match:
                pid = pid_match.group(1)
                try:
                    try:
                        process_info = self.adb._run_adb_command([self.adb.adb_path, 'shell', f'ps -p {pid} -o NAME='], timeout=5)
                        if process_info:
                            name = process_info.strip().split('\n')[-1].strip()
                            if name and '.' in name and len(name) > 3:
                                return name
                    except Exception:
                        return 'Desconhecido'
                except Exception:
                    pass
                return 'Desconhecido'
        except Exception:
            pass
        return 'Desconhecido'
    def analyze_device_enhanced(self, callback=None):
        if callback:
            callback('­ƒÜÇ Iniciando an├ílise aprimorada com novos recursos...')
        base_results = self.analyze_device(callback)
        if 'error' in base_results:
            return base_results
        if callback:
            callback('­ƒö¼ Aplicando an├ílises avan├ºadas adicionais...')
        enhanced_results = base_results.copy()
        enhanced_results['enhanced_features'] = {}
        if callback:
            callback('­ƒîÉ Analisando tr├ífego de rede...')
        network_analysis = self._analyze_network_traffic()
        enhanced_results['enhanced_features']['network_analysis'] = network_analysis
        if callback:
            callback('ÔÜÖ´©Å Analisando servi├ºos em execu├º├úo...')
        services_analysis = self._analyze_running_services()
        enhanced_results['enhanced_features']['services_analysis'] = services_analysis
        if callback:
            callback('­ƒöï Analisando consumo de bateria (pode demorar um pouco)...')
        battery_analysis = self._analyze_battery_usage()
        enhanced_results['enhanced_features']['battery_analysis'] = battery_analysis
        if callback:
            callback('­ƒÄ» Detectando intents maliciosos...')
        intents_analysis = self._analyze_suspicious_intents()
        enhanced_results['enhanced_features']['intents_analysis'] = intents_analysis
        if callback:
            callback('­ƒôè Recalculando pontua├º├Áes com novos crit├®rios...')
        enhanced_results = self._recalculate_scores_with_new_features(enhanced_results)
        if callback:
            callback('Ô£à An├ílise aprimorada conclu├¡da!')
        return enhanced_results
    def _analyze_network_traffic(self):
        try:
            netstat_result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'netstat -tuln'])
            suspicious_connections = []
            suspicious_ports = ['443', '80', '8080', '3000', '4443']
            ad_servers = ['googlesyndication', 'doubleclick', 'adsystem', 'facebook', 'admob']
            for line in netstat_result.split('\n'):
                if 'ESTABLISHED' in line:
                    for port in suspicious_ports:
                        if not f':{port}' in line:
                            continue
                        connection_info = {'line': line.strip(), 'port': port, 'suspicious': any((server in line.lower() for server in ad_servers))}
                        suspicious_connections.append(connection_info)
                        break
        except Exception as e:
            logger.error(f'Erro ao analisar tr├ífego de rede: {str(e)}')
            return {'error': str(e)}
        try:
            return {'total_connections': len(suspicious_connections), 'suspicious_connections': suspicious_connections, 'ad_related': [conn for conn in suspicious_connections if conn['suspicious']]}
        except Exception as e:
            logger.error(f'Erro ao analisar tr├ífego de rede: {str(e)}')
            return {'error': str(e)}
    def _analyze_running_services(self):
        try:
            services_result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys activity services'])
            suspicious_services = []
            suspicious_keywords = ['ad', 'ads', 'advertisement', 'notification', 'push', 'tracker', 'analytics', 'monitor', 'spy', 'hidden']
            current_service = None
            user_apps = self._get_user_apps()
            for line in services_result.split('\n'):
                if 'ServiceRecord{' in line:
                    match = re.search('ServiceRecord\\{[^}]+\\} ([^/]+)/([^}]+)', line)
                    if match:
                        package_name = match.group(1)
                        service_name = match.group(2)
                        if package_name in user_apps:
                            service_info = {'package': package_name, 'service': service_name, 'full_line': line.strip(), 'suspicious': any((keyword in service_name.lower() for keyword in suspicious_keywords))}
                            if not service_info['suspicious']:
                                if any((keyword in package_name.lower() for keyword in suspicious_keywords)):
                                    suspicious_services.append(service_info)
            return {'total_services': len(suspicious_services), 'suspicious_services': suspicious_services}
        except Exception as e:
            logger.error(f'Erro ao analisar servi├ºos: {str(e)}')
            return {'error': str(e)}
    def _analyze_battery_usage(self):
        try:
            battery_result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys batterystats --checkin'])
            high_battery_apps = []
            user_apps = self._get_user_apps()
            uid_to_app = {}
            try:
                packages_info = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys package packages'])
                current_package = None
                for line in packages_info.split('\n'):
                    if line.strip().startswith('Package ['):
                        match = re.search('Package \\[([^\\]]+)\\]', line)
                        if match:
                            current_package = match.group(1)
                        continue
                        continue
                    if 'userId=' not in line:
                        continue
                    if not current_package:
                        continue
                    if current_package in user_apps:
                        uid_match = re.search('userId=(\\d+)', line)
                        if uid_match:
                            uid = f'u0a{uid_match.group(1)}'
                            uid_to_app[uid] = current_package
            except Exception as e:
                logger.warning(f'Erro ao mapear UIDs: {str(e)}')
                try:
                    try:
                        return {'total_high_battery': 0, 'high_battery_apps': [], 'note': 'An├ílise de bateria pulada devido a erro de mapeamento'}
                    except:
                        pass
                except Exception as e:
                    logger.error(f'Erro ao analisar bateria: {str(e)}')
                    return {'total_high_battery': 0, 'high_battery_apps': [], 'error': str(e)}
            else:
                suspicious_uids = set()
                lines_processed = 0
                max_lines = 1000
                for line in battery_result.split('\n'):
                    lines_processed += 1
                    if lines_processed > max_lines:
                        break
                    if ',10,' in line:
                        parts = line.split(',')
        except Exception as e:
            logger.error(f'Erro ao analisar bateria: {str(e)}')
            return {'total_high_battery': 0, 'high_battery_apps': [], 'error': str(e)}
        for uid in suspicious_uids:
            if uid in uid_to_app:
                app_package = uid_to_app[uid]
                battery_info = {'package': app_package, 'uid': uid, 'indicator': 'Alto consumo detectado via checkin', 'app_name': self._get_app_label(app_package)}
                high_battery_apps.append(battery_info)
        return {'total_high_battery': len(high_battery_apps), 'high_battery_apps': high_battery_apps, 'lines_processed': lines_processed}
    def _analyze_suspicious_intents(self):
        try:
            self.adb._run_adb_command([self.adb.adb_path, 'logcat', '-c'])
            time.sleep(2)
            logcat_result = self.adb._run_adb_command([self.adb.adb_path, 'logcat', '-d', '-v', 'time'])
            suspicious_intents = []
            for line in logcat_result.split('\n'):
                if 'android.intent.action.VIEW' in line:
                    if any((pattern in line for pattern in ('http://', 'https://', 'market://'))):
                        intent_info = {'timestamp': datetime.now().strftime('%H:%M:%S'), 'type': 'navigation', 'line': line.strip(), 'suspicious': 'market://' in line or any((ad_domain in line.lower() for ad_domain in ('ads', 'doubleclick', 'googlesyndication', 'admob')))}
                        suspicious_intents.append(intent_info)
                elif any((action in line for action in ('INSTALL_PACKAGE', 'REQUEST_INSTALL'))):
                    intent_info = {'timestamp': datetime.now().strftime('%H:%M:%S'), 'type': 'install', 'line': line.strip(), 'suspicious': True}
                    suspicious_intents.append(intent_info)
        except Exception as e:
            logger.error(f'Erro ao analisar intents: {str(e)}')
            return {'error': str(e)}
        try:
            pass
        except Exception as e:
            logger.error(f'Erro ao analisar intents: {str(e)}')
            return {'error': str(e)}
        try:
            return {'total_intents': len(suspicious_intents), 'suspicious_intents': suspicious_intents, 'navigation_intents': [intent for intent in suspicious_intents if intent['type'] == 'navigation'], 'install_intents': [intent for intent in suspicious_intents if intent['type'] == 'install']}
        except Exception as e:
            logger.error(f'Erro ao analisar intents: {str(e)}')
            return {'error': str(e)}
    def _recalculate_scores_with_new_features(self, results):
        if 'enhanced_features' not in results:
            return results
        enhanced_features = results['enhanced_features']
        results['high_risk'] = 0
        results['medium_risk'] = 0
        results['low_risk'] = 0
        for app_package, app_data in results['suspicious_apps'].items():
            additional_score = 0
            additional_reasons = []
            network_data = enhanced_features.get('network_analysis', {})
            if 'ad_related' in network_data:
                for conn in network_data['ad_related']:
                    if not app_package in conn.get('line', ''):
                        continue
                    additional_score += 15
                    additional_reasons.append('Conex├Áes suspeitas com servidores de an├║ncios')
                    break
            services_data = enhanced_features.get('services_analysis', {})
            if 'suspicious_services' in services_data:
                for service in services_data['suspicious_services']:
                    if service['package'] == app_package:
                        additional_score += 25
                        additional_reasons.append(f'Servi├ºo suspeito: {service['service']}')
            battery_data = enhanced_features.get('battery_analysis', {})
            if 'high_battery_apps' in battery_data:
                for battery_app in battery_data['high_battery_apps']:
                    if not battery_app['package'] == app_package:
                        continue
                    additional_score += 15
                    additional_reasons.append('Consumo anormal de bateria')
                    break
            intents_data = enhanced_features.get('intents_analysis', {})
            if 'suspicious_intents' in intents_data:
                for intent in intents_data['suspicious_intents']:
                    if not intent['suspicious']:
                        continue
                    if not app_package in intent.get('line', ''):
                        continue
                    additional_score += 30
                    additional_reasons.append('Intents maliciosos detectados')
                    break
            if additional_score > 0:
                app_data['score'] += additional_score
                app_data['reasons'].extend(additional_reasons)
                new_score = app_data['score']
                app_data['risk_level'] = 'Alto' if new_score > 70 else 'M├®dio' if new_score > 40 else 'Baixo'
            final_score = app_data['score']
            if final_score > 70:
                results['high_risk'] += 1
                continue
            if final_score > 40:
                results['medium_risk'] += 1
                continue
            results['low_risk'] += 1
            continue
        results['suspicious_apps'] = dict(sorted(results['suspicious_apps'].items(), key=(lambda item: item[1]['score']), reverse=True))
        return results
    def monitor_screen_changes(self, duration=30, callback=None):
        if callback:
            callback(f'Monitorando atividade na tela por {duration} segundos...')
            callback('Verificando apps que aparecem repetidamente na tela')
        start_time = time.time()
        foreground_counts = {}
        suspicious_events = []
        reported_packages = set()
        check_interval = 2
        threshold = max(3, int(duration / check_interval * 0.15))
        try:
            total_checks = max(1, int(duration / check_interval))
            for i in range(total_checks):
                elapsed = time.time() - start_time
                remaining = max(0, int(duration - elapsed))
                if callback and i % 5 == 0:
                    callback(f'Monitorando tela... {remaining}s restantes')
            try:
                output = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys', 'activity', 'activities'], timeout=10)
                if not output:
                    output = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys', 'window', 'windows'], timeout=10) or ''
                match = re.search('(?:mResumedActivity|topResumedActivity|mCurrentFocus).*?([a-zA-Z][a-zA-Z0-9_]*(?:\\.[a-zA-Z][a-zA-Z0-9_]*){1,})/', output)
                if match:
                    package = match.group(1)
                    if not self._is_trusted_app(package):
                        foreground_counts[package] = foreground_counts.get(package, 0) + 1
                        if foreground_counts[package] >= threshold and package not in reported_packages:
                            reported_packages.add(package)
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            suspicious_events.append({'timestamp': timestamp, 'active_overlays': [package], 'suspicious': True, 'count': foreground_counts[package]})
                            if callback:
                                callback(f'App suspeito detectado: {package} (apareceu {foreground_counts[package]}x na tela)')
            except Exception as cmd_err:
                logger.debug('Erro na verificacao de foreground [%d]: %s', i, cmd_err)
            else:
                elapsed = time.time() - start_time
                sleep_time = min(check_interval, max(0, duration - elapsed))
                if not sleep_time > 0:
                    pass
                if not i < total_checks - 1:
                    pass
                time.sleep(sleep_time)
                actual_duration = round(time.time() - start_time, 1)
                result_data = {'duration': duration, 'actual_duration': actual_duration, 'screenshots_taken': 0, 'screen_changes': suspicious_events, 'suspicious_events': len(suspicious_events), 'foreground_suspects': foreground_counts}
                if callback:
                    pass
        except Exception as e:
            logger.error('Erro no monitoramento de foreground: %s', e, exc_info=True)
            if callback:
                try:
                    callback('Erro no monitoramento. Verifique a conexao com o dispositivo.')
                except Exception:
                    pass
        return result_data
