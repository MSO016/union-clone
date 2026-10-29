import time
from . import _mit_core as _core
_OK = 'Ô£ö'
_FAIL_ICON = 'Ô£û'
_LINE = 'ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ'
_DASH = 'ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ'
_BRAND = 'TECH UNION SOLUTIONS'
_DESCRIPTIONS = {'wifi': 'Internet sem fio', 'bluetooth': 'Conexao sem fio (fone, caixa)', 'modem': 'Chip de ligacao e dados moveis', 'audio': 'Alto-falante e microfone', 'sensores': 'Rotacao de tela, bussola, movimento', 'display': 'Tela e iluminacao', 'storage': 'Memoria interna (armazenamento)', 'usb': 'Conexao com computador', 'pmic': 'Bateria e alimentacao', 'camera': 'Cameras, flash e foco', 'gps_fm': 'Localizacao GPS e radio FM'}
_FAIL_HINTS = {'wifi': 'Possivel defeito: modulo WiFi, antena ou flex', 'bluetooth': 'Possivel defeito: modulo BT ou antena', 'modem': 'Possivel defeito: modem, flex do SIM ou antena', 'audio': 'Possivel defeito: codec de audio ou alto-falante', 'sensores': 'Sensores podem estar desativados neste modo', 'display': 'Verificacao limitada ÔÇö teste visual recomendado', 'storage': 'Possivel defeito: chip eMMC ou conexao BGA', 'usb': 'Porta USB esta funcionando (conectado agora)', 'pmic': 'Possivel defeito: IC de carga ou bateria', 'camera': 'Possivel defeito: flex da camera ou IC', 'gps_fm': 'GPS/FM podem nao estar disponiveis neste modelo'}
def _noop(msg):
    pass
def _pad(label, value, width=18):
    dots = '.' * max(1, width - len(label))
    return f'  {label!s}{dots!s} {value!s}'
def _count_markers(raw, labels_dict):
    found = {}
    for marker in labels_dict:
        if marker in (raw or ''):
            found[marker] = labels_dict[marker]
    return found
def _log_header(log, key, label, status):
    icon = _OK if status == 'PASS' else _FAIL_ICON if status == 'FAIL' else 'Ôùï'
    desc = _DESCRIPTIONS.get(key, '')
    if desc:
        log(f'{icon!s} {label!s} ({desc!s})')
        return
    log(f'{icon!s} {label!s}')
def _log_fail_hint(log, key):
    hint = _FAIL_HINTS.get(key, '')
    if hint:
        log('  ** %s **' % hint)
def _test_wifi(sh, log):
    r = {'status': 'FAIL', 'detalhes': {}}
    try:
        time.sleep(0.15)
        batch = sh(_core.HW_BATCH_WIFI, timeout=5.0)
        found = _count_markers(batch, _core.HW_WIFI_LABELS)
        r['detalhes'] = found
        count = len(found)
        if count > 0:
            r['status'] = 'PASS'
            _log_header(log, 'wifi', 'WIFI', 'PASS')
            log(_pad('Resultado', 'Funcionando'))
            log(_pad('Evidencias', '%d componentes detectados' % count))
            return r
    except Exception:
        r['status'] = 'INFO'
        _log_header(log, 'wifi', 'WIFI', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    return r
    try:
        _log_header(log, 'wifi', 'WIFI', 'FAIL')
        log(_pad('Resultado', 'Nao detectado'))
        _log_fail_hint(log, 'wifi')
    except Exception:
        r['status'] = 'INFO'
        _log_header(log, 'wifi', 'WIFI', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    return r
def _test_bluetooth(sh, log):
    r = {'status': 'FAIL', 'detalhes': {}}
    try:
        time.sleep(0.15)
        batch = sh(_core.HW_BATCH_BT, timeout=5.0)
        found = _count_markers(batch, _core.HW_BT_LABELS)
        r['detalhes'] = found
        count = len(found)
        if count > 0:
            r['status'] = 'PASS'
            _log_header(log, 'bluetooth', 'BLUETOOTH', 'PASS')
            log(_pad('Resultado', 'Funcionando'))
            perfs = []
            if 'GATT:OK' in found:
                perfs.append('GATT')
            if 'A2DP:OK' in found:
                perfs.append('A2DP')
            if perfs:
                log(_pad('Perfis', '%s (audio BT)' % ' + '.join(perfs)))
                return r
            log(_pad('Evidencias', '%d componentes' % count))
            return r
    except Exception:
        r['status'] = 'INFO'
        _log_header(log, 'bluetooth', 'BLUETOOTH', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    return r
    try:
        _log_header(log, 'bluetooth', 'BLUETOOTH', 'FAIL')
        log(_pad('Resultado', 'Nao detectado'))
        _log_fail_hint(log, 'bluetooth')
    except Exception:
        r['status'] = 'INFO'
        _log_header(log, 'bluetooth', 'BLUETOOTH', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    return r
def _test_modem(sh, log):
    r = {'status': 'FAIL', 'detalhes': {}}
    try:
        time.sleep(0.15)
        batch = sh(_core.HW_BATCH_MODEM, timeout=5.0)
        found = _count_markers(batch, _core.HW_MODEM_LABELS)
        r['detalhes'] = found
        count = len(found)
        if count > 0:
            r['status'] = 'PASS'
            _log_header(log, 'modem', 'MODEM/RF', 'PASS')
            log(_pad('Resultado', 'Funcionando'))
            portas = sum((1 for m in ('TTYC0:OK', 'TTYC1:OK', 'TTYGS0:OK') if m in found))
            if portas:
                log(_pad('Portas', '%d porta(s) de comunicacao' % portas))
            has_ril = 'RIL:OK' in found
            has_ccci = 'CCCI_FS:OK' in found
            if has_ril and has_ccci:
                log(_pad('Status', 'RIL + comunicacao AP-Modem OK'))
                return r
            if has_ril:
                log(_pad('Status', 'RIL configurado'))
                return r
            if has_ccci:
                log(_pad('Status', 'Comunicacao AP-Modem ativa'))
            return r
    except Exception:
        r['status'] = 'INFO'
        _log_header(log, 'modem', 'MODEM/RF', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    return r
    try:
        _log_header(log, 'modem', 'MODEM/RF', 'FAIL')
        log(_pad('Resultado', 'Nao detectado'))
        _log_fail_hint(log, 'modem')
    except Exception:
        r['status'] = 'INFO'
        _log_header(log, 'modem', 'MODEM/RF', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    return r
def _test_audio(sh, log):
    r = {'status': 'FAIL', 'detalhes': {}}
    try:
        time.sleep(0.15)
        cards = sh('cat /proc/asound/cards 2>/dev/null', timeout=3.0)
        if cards and len(cards) > 3:
            r['status'] = 'PASS'
            _log_header(log, 'audio', 'AUDIO', 'PASS')
            log(_pad('Resultado', 'Funcionando'))
            raw_card = cards.strip().split('\n')[0] if cards else ''
            codec = raw_card
            if ']:' in raw_card:
                codec = raw_card.split(']:')[0].split('[')[-1].strip()
            if codec:
                r['detalhes']['codec'] = codec
                log(_pad('Codec', codec))
            time.sleep(0.15)
            pcm = sh('cat /proc/asound/pcm 2>/dev/null', timeout=3.0)
            if pcm:
                count = len([l for l in pcm.split('\n') if l.strip()])
                r['detalhes']['pcm_count'] = str(count)
                log(_pad('Canais', '%d canais de audio' % count))
            return r
    except Exception:
        r['status'] = 'INFO'
        _log_header(log, 'audio', 'AUDIO', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    try:
        _log_header(log, 'audio', 'AUDIO', 'FAIL')
        log(_pad('Resultado', 'Nao detectado'))
        _log_fail_hint(log, 'audio')
    except Exception:
        r['status'] = 'INFO'
        _log_header(log, 'audio', 'AUDIO', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    return r
def _test_sensors(sh, log):
    r = {'status': 'INFO', 'detalhes': {}}
    try:
        time.sleep(0.15)
        batch = sh(_core.HW_BATCH_SENSORS, timeout=5.0)
        if not batch:
            _log_header(log, 'sensores', 'SENSORES', 'INFO')
            log(_pad('Resultado', 'Sem resposta do dispositivo'))
            return r
    except Exception:
        _log_header(log, 'sensores', 'SENSORES', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    try:
        parts = [p.strip() for p in batch.split('|')]
        sensors_map = [('Acelerometro', 'Detecta movimento e inclinacao'), ('Giroscopio', 'Rotacao e orientacao da tela'), ('Magnetometro', 'Bussola digital'), ('Prox/Luz', 'Sensor de proximidade e luz'), ('Prox/Luz (alt)', None), ('Barometro', 'Pressao atmosferica'), ('Step Counter', 'Contador de passos')]
        found = 0
        found_names = []
        missing_names = []
        for i, (name, desc) in enumerate(sensors_map):
            if i < len(parts) and parts[i]:
                if i == 4:
                    if found > 3:
                        continue
                chip = parts[i]
                r['detalhes'][name.lower()] = chip
                found_names.append((name, chip))
                found += 1
            elif i <= 2:
                missing_names.append(name)
        if found > 0:
            r['status'] = 'PASS'
            _log_header(log, 'sensores', 'SENSORES', 'PASS')
            log(_pad('Resultado', '%d sensor(es) detectado(s)' % found))
            for name, chip in found_names:
                log(_pad(name, f'{chip!s} {_OK!s}'))
            for name in missing_names:
                log(_pad(name, 'Nao encontrado %s' % _FAIL_ICON))
            return r
    except Exception:
        _log_header(log, 'sensores', 'SENSORES', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    return r
    try:
        _log_header(log, 'sensores', 'SENSORES', 'INFO')
        log(_pad('Resultado', 'Nenhum sensor detectado'))
        _log_fail_hint(log, 'sensores')
    except Exception:
        _log_header(log, 'sensores', 'SENSORES', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    return r
def _test_display(sh, log):
    r = {'status': 'INFO', 'detalhes': {}}
    try:
        time.sleep(0.15)
        batch = sh(_core.HW_BATCH_DISPLAY, timeout=5.0)
        found = _count_markers(batch, _core.HW_DISPLAY_LABELS)
        r['detalhes'] = found
        count = len(found)
        density_val = ''
        if 'DENS:OK' in (batch or ''):
            time.sleep(0.15)
            density_val = sh('getprop ro.sf.lcd_density 2>/dev/null', timeout=3.0)
            if density_val:
                density_val = density_val.strip()
                r['detalhes']['densidade'] = '%s DPI' % density_val
        if count > 0:
            r['status'] = 'PASS'
            _log_header(log, 'display', 'DISPLAY', 'PASS')
            log(_pad('Resultado', 'Funcionando'))
            if density_val:
                log(_pad('Densidade', '%s DPI' % density_val))
            if 'HWC:OK' in found:
                log(_pad('HW Composer', 'Configurado %s' % _OK))
            return r
    except Exception:
        _log_header(log, 'display', 'DISPLAY', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    return r
    try:
        _log_header(log, 'display', 'DISPLAY', 'INFO')
        log(_pad('Resultado', 'Verificacao limitada neste modo'))
        _log_fail_hint(log, 'display')
    except Exception:
        _log_header(log, 'display', 'DISPLAY', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    return r
def _test_storage(sh, log):
    r = {'status': 'FAIL', 'detalhes': {}}
    try:
        for dev in ('mmcblk0', 'sda'):
            time.sleep(0.15)
            sz = sh('cat /sys/class/block/%s/size 2>/dev/null' % dev, timeout=3.0)
            if not sz or not sz.strip().isdigit():
                continue
            size_val = int(sz.strip())
            if size_val <= 0:
                continue
            gb = size_val * 512 / 1073741824
            r['detalhes']['device'] = dev
            r['detalhes']['tamanho'] = '%.1f GB' % gb
            r['status'] = 'PASS'
            time.sleep(0.15)
            name = sh('cat /sys/class/mmc_host/mmc0/mmc0:0001/name 2>/dev/null', timeout=3.0)
            time.sleep(0.15)
            manfid = sh('cat /sys/class/mmc_host/mmc0/mmc0:0001/manfid 2>/dev/null', timeout=3.0)
            time.sleep(0.15)
            life = sh('cat /sys/class/mmc_host/mmc0/mmc0:0001/life_time 2>/dev/null', timeout=3.0)
            time.sleep(0.15)
            eol = sh('cat /sys/class/mmc_host/mmc0/mmc0:0001/pre_eol_info 2>/dev/null', timeout=3.0)
            fabricante = ''
            if manfid and manfid.strip():
                fabricante = _core.decode_emmc_manufacturer(manfid.strip())
                r['detalhes']['fabricante'] = fabricante
            modelo = (name or '').strip()
            if modelo:
                r['detalhes']['modelo'] = modelo
            _log_header(log, 'storage', 'STORAGE', 'PASS')
            log(_pad('Tipo', 'eMMC'))
            fab_label = fabricante or 'Desconhecido'
            if modelo:
                fab_label = f'{fab_label!s} {modelo!s}'
            log(_pad('Fabricante', fab_label))
            log(_pad('Capacidade', '%.1f GB' % gb))
            if life and life.strip():
                saude = _core.interpret_life_time(life.strip())
                r['detalhes']['vida_util'] = saude
                log(_pad('Vida util', saude))
            if eol and eol.strip():
                eol_label = _core.interpret_pre_eol(eol.strip())
                r['detalhes']['eol'] = eol_label
                log(_pad('Status', eol_label))
            break
        if r['status'] != 'PASS':
            _log_header(log, 'storage', 'STORAGE', 'FAIL')
            log(_pad('Resultado', 'Nao detectado'))
            _log_fail_hint(log, 'storage')
    except Exception:
        r['status'] = 'INFO'
        _log_header(log, 'storage', 'STORAGE', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    return r
    return r
def _test_usb(sh, log):
    r = {'status': 'PASS', 'detalhes': {'comunicacao': 'Ativa'}}
    try:
        time.sleep(0.15)
        batch = sh(_core.HW_BATCH_USB, timeout=3.0)
        _log_header(log, 'usb', 'USB', 'PASS')
        if batch:
            parts = [p.strip() for p in batch.split('|')]
            if len(parts) >= 1 and parts[0]:
                r['detalhes']['estado'] = parts[0]
                log(_pad('Estado', '%s (ativo)' % parts[0]))
            else:
                log(_pad('Estado', 'Conectado'))
            if len(parts) >= 2 and parts[1]:
                r['detalhes']['funcoes'] = parts[1]
            return r
    except Exception:
        _log_header(log, 'usb', 'USB', 'PASS')
        log(_pad('Estado', 'Conectado (comunicacao ativa)'))
    try:
        log(_pad('Estado', 'Conectado (comunicacao ativa)'))
    except Exception:
        _log_header(log, 'usb', 'USB', 'PASS')
        log(_pad('Estado', 'Conectado (comunicacao ativa)'))
    return r
def _test_pmic(sh, log):
    r = {'status': 'INFO', 'detalhes': {}}
    try:
        time.sleep(0.15)
        batch = sh(_core.HW_BATCH_PMIC, timeout=5.0)
        if not batch:
            _log_header(log, 'pmic', 'BATERIA', 'INFO')
            log(_pad('Resultado', 'Sem resposta'))
            return r
    except Exception:
        _log_header(log, 'pmic', 'BATERIA', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    try:
        parts = [p.strip() for p in batch.split('|')]
        status_bat = parts[0] if len(parts) >= 1 and parts[0] else ''
        capacity = parts[1] if len(parts) >= 2 and parts[1] else ''
        voltage_raw = parts[2] if len(parts) >= 3 and parts[2] else ''
        temp_raw = parts[3] if len(parts) >= 4 and parts[3] else ''
        current_raw = parts[4] if len(parts) >= 5 and parts[4] else ''
        health = parts[5] if len(parts) >= 6 and parts[5] else ''
        has_data = bool(status_bat or capacity)
        if has_data:
            r['status'] = 'PASS'
            _log_header(log, 'pmic', 'BATERIA', 'PASS')
        else:
            _log_header(log, 'pmic', 'BATERIA', 'INFO')
            log(_pad('Resultado', 'Dados insuficientes'))
            return r
        if capacity:
            r['detalhes']['capacidade'] = '%s%%' % capacity
            log(_pad('Carga', '%s%%' % capacity))
        if voltage_raw and voltage_raw.lstrip('-').isdigit():
            mv = int(voltage_raw) / 1000
            volts = mv / 1000
            r['detalhes']['voltagem'] = '%.3fV' % volts
            log(_pad('Voltagem', '%.3fV' % volts))
        if temp_raw and temp_raw.lstrip('-').isdigit():
            temp_c = int(temp_raw) / 10
            r['detalhes']['temperatura'] = '%.1f┬░C' % temp_c
            log(_pad('Temperatura', '%.1f┬░C' % temp_c))
        if current_raw and current_raw.lstrip('-').isdigit():
            ma = int(current_raw) / 1000
            r['detalhes']['corrente'] = '%.0f mA' % ma
            log(_pad('Corrente', '%.0f mA' % ma))
        if health:
            r['detalhes']['health'] = health
            health_pt = {'Good': 'Boa', 'Overheat': 'Superaquecida', 'Dead': 'Defeituosa', 'Over voltage': 'Sobretensao', 'Cold': 'Muito fria'}.get(health, health)
            log(_pad('Saude', '%s' % health_pt))
        if status_bat:
            r['detalhes']['status'] = status_bat
            status_pt = {'Charging': 'Carregando', 'Discharging': 'Descarregando', 'Full': 'Completa', 'Not charging': 'Nao carregando'}.get(status_bat, status_bat)
            log(_pad('Estado', status_pt))
    except Exception:
        _log_header(log, 'pmic', 'BATERIA', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    return r
    return r
def _test_camera(sh, log):
    r = {'status': 'INFO', 'detalhes': {}}
    try:
        time.sleep(0.3)
        sh('echo OK', timeout=2.0)
        time.sleep(0.15)
        batch = sh(_core.HW_BATCH_CAMERA, timeout=5.0)
        if not batch:
            time.sleep(0.3)
            batch = sh(_core.HW_BATCH_CAMERA, timeout=5.0)
        found = _count_markers(batch, _core.HW_CAMERA_LABELS)
        r['detalhes'] = found
        if found:
            r['status'] = 'PASS'
            _log_header(log, 'camera', 'CAMERA', 'PASS')
            log(_pad('Resultado', 'Funcionando'))
            if 'CAM:OK' in found:
                log(_pad('Driver', 'Presente %s' % _OK))
            if 'FLASH:OK' in found:
                log(_pad('Flash', 'Presente %s' % _OK))
            if 'AF:OK' in found:
                log(_pad('AutoFocus', 'Presente %s' % _OK))
            return r
    except Exception:
        _log_header(log, 'camera', 'CAMERA', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    return r
    try:
        _log_header(log, 'camera', 'CAMERA', 'INFO')
        log(_pad('Resultado', 'Verificacao limitada neste modo'))
        _log_fail_hint(log, 'camera')
    except Exception:
        _log_header(log, 'camera', 'CAMERA', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    return r
def _test_gps_fm(sh, log):
    r = {'status': 'INFO', 'detalhes': {}}
    try:
        time.sleep(0.15)
        batch = sh(_core.HW_BATCH_GPS_FM, timeout=5.0)
        found = _count_markers(batch, _core.HW_GPS_FM_LABELS)
        r['detalhes'] = found
        if found:
            r['status'] = 'PASS'
            _log_header(log, 'gps_fm', 'GPS / FM', 'PASS')
            log(_pad('Resultado', 'Funcionando'))
            if 'GPS:OK' in found:
                log(_pad('GPS', 'Presente %s' % _OK))
            if 'FM:OK' in found:
                log(_pad('FM Radio', 'Presente %s' % _OK))
            return r
    except Exception:
        _log_header(log, 'gps_fm', 'GPS / FM', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    return r
    try:
        _log_header(log, 'gps_fm', 'GPS / FM', 'INFO')
        log(_pad('Resultado', 'Nao verificavel neste modelo'))
        _log_fail_hint(log, 'gps_fm')
    except Exception:
        _log_header(log, 'gps_fm', 'GPS / FM', 'INFO')
        log(_pad('Resultado', 'Verificacao inconclusiva'))
    return r
_TEST_SEQUENCE = [('wifi', 'WIFI', _test_wifi), ('bluetooth', 'BLUETOOTH', _test_bluetooth), ('modem', 'MODEM/RF', _test_modem), ('audio', 'AUDIO', _test_audio), ('sensores', 'SENSORES', _test_sensors), ('display', 'DISPLAY', _test_display), ('storage', 'STORAGE', _test_storage), ('usb', 'USB', _test_usb), ('pmic', 'BATERIA', _test_pmic), ('camera', 'CAMERA', _test_camera), ('gps_fm', 'GPS / FM', _test_gps_fm)]
def run_diagnostics(shell_fn, log_fn=None):
    log = log_fn or _noop
    result = {'device_info': {}, 'tests': {}, 'resumo': {}}
    log(_LINE)
    log('  DIAGNOSTICO DE HARDWARE')
    log('  %s' % _BRAND)
    log(_LINE)
    try:
        time.sleep(0.15)
        info_raw = shell_fn(_core.HW_BATCH_DEVICE_INFO, timeout=5.0)
        if info_raw:
            parts = [p.strip() for p in info_raw.split('|')]
            keys = ['hardware', 'modelo', 'marca', 'android', 'sdk', 'build']
            for i, key in enumerate(keys):
                if not i < len(parts):
                    continue
                if parts[i]:
                    result['device_info'][key] = parts[i]
            di = result['device_info']
            log(_pad('Marca', di.get('marca', '?')))
            log(_pad('Modelo', di.get('modelo', '?')))
            log(_pad('Processador', di.get('hardware', '?')))
            log(_pad('Android', di.get('android', '?')))
        else:
            log('  Informacoes do dispositivo indisponiveis')
    except Exception:
        log('  Informacoes do dispositivo indisponiveis')
    log('')
    counts = {'pass': 0, 'fail': 0, 'info': 0}
    for key, label, test_fn in _TEST_SEQUENCE:
        try:
            test_result = test_fn(shell_fn, log)
            result['tests'][key] = test_result
            status = test_result.get('status', 'INFO')
            if status == 'PASS':
                counts['pass'] += 1
            elif status == 'FAIL':
                counts['fail'] += 1
            else:
                counts['info'] += 1
        except Exception:
            result['tests'][key] = {'status': 'INFO', 'detalhes': {}}
            counts['info'] += 1
            _log_header(log, key, label, 'INFO')
            log(_pad('Resultado', 'Erro interno'))
            continue
    total = counts['pass'] + counts['fail'] + counts['info']
    result['resumo'] = {'total': total, 'pass': counts['pass'], 'fail': counts['fail'], 'info': counts['info']}
    log('')
    log(_DASH)
    log('  RESUMO: %d OK | %d FALHA | %d INFO' % (counts['pass'], counts['fail'], counts['info']))
    log(_DASH)
    log('  Analise de hardware em Meta Mode')
    log('  Resultado baseado na deteccao de componentes')
    log('  Feito de tecnicos para tecnicos')
    log(_DASH)
    return result
