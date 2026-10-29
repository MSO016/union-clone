import re
import logging
logger = logging.getLogger('DiagParser')
_INVALID = 2147483647
_CPU_VENDORS = {'0x41': 'ARM', '0x51': 'Qualcomm', '0x53': 'Samsung', '0x69': 'Intel', '0xc0': 'Ampere'}
_PLATFORM_SOC = {'erd3830': 'Exynos 850', 's5e3830': 'Exynos 850', 'erd8825': 'Exynos 1280', 'erd9925': 'Exynos 2200', 'erd8835': 'Exynos 1380', 's5e8825': 'Exynos 1280', 'bengal': 'Snapdragon 460/662', 'holi': 'Snapdragon 695', 'lahaina': 'Snapdragon 888', 'taro': 'Snapdragon 8 Gen 1', 'kalama': 'Snapdragon 8 Gen 2', 'mt6765': 'Helio G35/P35', 'mt6768': 'Helio G85', 'mt6769': 'Helio G80', 'mt6833': 'Dimensity 700', 'mt6853': 'Dimensity 720/800U', 'mt6877': 'Dimensity 900', 'mt6893': 'Dimensity 1200', 'mt6983': 'Dimensity 9000', 'mt6789': 'Helio G99', 'ums512': 'UNISOC Tiger T616', 'ums9230': 'UNISOC Tiger T606'}
_CPU_CORES = {'0xd03': 'Cortex-A53', '0xd04': 'Cortex-A35', '0xd05': 'Cortex-A55', '0xd07': 'Cortex-A57', '0xd08': 'Cortex-A72', '0xd09': 'Cortex-A73', '0xd0a': 'Cortex-A75', '0xd0b': 'Cortex-A76', '0xd0d': 'Cortex-A77', '0xd41': 'Cortex-A78', '0xd44': 'Cortex-X1', '0xd46': 'Cortex-A510', '0xd47': 'Cortex-A710', '0xd48': 'Cortex-X2', '0xd4b': 'Cortex-A78C', '0xd4d': 'Cortex-A715', '0xd4e': 'Cortex-X3', '0x800': 'Kryo 260 Gold', '0x801': 'Kryo 616', '0x802': 'Kryo 385 Gold', '0x803': 'Kryo 385 Silver', '0x804': 'Kryo 485 Gold', '0x805': 'Kryo 485 Silver'}
_SENSOR_ESSENCIAIS = {1: 'Acelerometro', 2: 'Bussola', 4: 'Giroscopio', 5: 'Luz Ambiente', 8: 'Proximidade', 6: 'Barometro'}
_SIGNAL_RSRP_CLASSIFICATION = [(-80, 'Excelente'), (-90, 'Bom'), (-100, 'Moderado'), (-110, 'Fraco'), (-140, 'Muito Fraco')]
_SIGNAL_RSCP_CLASSIFICATION = [(-75, 'Excelente'), (-85, 'Bom'), (-105, 'Moderado'), (-115, 'Fraco'), (-140, 'Muito Fraco')]
def _safe_int(value, default=None):
    if value is None:
        return default
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return default
def _safe_float(value, default=None):
    if value is None:
        return default
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return default
def _classify_temp(celsius):
    if celsius is None:
        return (None, None)
    if celsius < 35:
        return ('Normal', 'green')
    if celsius < 42:
        return ('Morno', 'yellow')
    if celsius < 50:
        return ('Quente', 'orange')
    return ('Critico', 'red')
def _classify_battery_health(pct):
    if pct is None:
        return ('Indisponivel', 'gray')
    if pct >= 90:
        return ('Excelente', 'green')
    if pct >= 80:
        return ('Boa', 'green')
    if pct >= 70:
        return ('Moderada', 'yellow')
    if pct >= 60:
        return ('Desgastada', 'orange')
    return ('Critica', 'red')
def _classify_signal(dbm, classification_table):
    if dbm is None or dbm == _INVALID:
        return ('Indisponivel', 'gray', 0)
    for threshold, label in classification_table:
        if dbm >= threshold:
            idx = classification_table.index((threshold, label))
            bars = len(classification_table) - idx
            return label, 'green' if bars >= 4 else 'yellow' if bars >= 3 else 'orange' if bars >= 2 else 'red', bars
    return ('Muito Fraco', 'red', 1)
def _parse_size_to_gb(size_str):
    if not size_str:
        return
    size_str = size_str.strip()
    try:
        if size_str.endswith('T'):
            return float(size_str[:-1]) * 1024
        if size_str.endswith('G'):
            return float(size_str[:-1])
        if size_str.endswith('M'):
            return float(size_str[:-1]) / 1024
        if size_str.endswith('K'):
            return float(size_str[:-1]) / 1048576
        return float(size_str) / 1073741824
    except (ValueError, TypeError):
        return
def parse_battery(dumpsys_output, sysfs_data=None):
    result = {'level': None, 'health_pct': None, 'health_label': 'Indisponivel', 'health_color': 'gray', 'cycles': None, 'capacity_now_mah': None, 'capacity_design_mah': None, 'temperature_c': None, 'temp_label': None, 'temp_color': None, 'voltage_v': None, 'charging': False, 'charging_watts': None, 'charging_source': None, 'technology': None}
    if not dumpsys_output:
        return result
    sysfs_data = sysfs_data or {}
    lines = dumpsys_output.strip().split('\n')
    dumpsys = {}
    for line in lines:
        line = line.strip()
        if ':' in line:
            key, _, val = line.partition(':')
            dumpsys[key.strip()] = val.strip()
    result['level'] = _safe_int(dumpsys.get('level'))
    result['technology'] = dumpsys.get('technology')
    status = _safe_int(dumpsys.get('status'))
    result['charging'] = status == 2
    ac = dumpsys.get('AC powered', '').lower() == 'true'
    usb = dumpsys.get('USB powered', '').lower() == 'true'
    wireless = dumpsys.get('Wireless powered', '').lower() == 'true'
    if ac:
        result['charging_source'] = 'AC'
    elif usb:
        result['charging_source'] = 'USB'
    elif wireless:
        result['charging_source'] = 'Wireless'
    raw_temp = _safe_int(dumpsys.get('temperature'))
    if raw_temp is not None and raw_temp > 0:
        result['temperature_c'] = raw_temp / 10.0
    raw_voltage = _safe_int(dumpsys.get('voltage'))
    if raw_voltage is not None and raw_voltage > 0:
        if raw_voltage > 10000:
            result['voltage_v'] = raw_voltage / 1000000.0
        elif raw_voltage > 100:
            result['voltage_v'] = raw_voltage / 1000.0
        else:
            result['voltage_v'] = float(raw_voltage)
    charge_watt = _safe_int(dumpsys.get('charge watt'))
    if charge_watt and charge_watt > 0 and result['charging']:
        result['charging_watts'] = charge_watt
    cycles_dumpsys = _safe_int(dumpsys.get('cycle count'))
    full_cap_dumpsys = _safe_int(dumpsys.get('Full capacity'))
    full_design_dumpsys = _safe_int(dumpsys.get('Full design capacity'))
    samsung_asoc = _safe_int(dumpsys.get('mSavedBatteryAsoc'))
    sysfs_charge_full = _safe_int(sysfs_data.get('charge_full'))
    sysfs_charge_design = _safe_int(sysfs_data.get('charge_full_design'))
    sysfs_cycle = _safe_int(sysfs_data.get('cycle_count'))
    sysfs_voltage = _safe_int(sysfs_data.get('voltage_now'))
    sysfs_temp = _safe_int(sysfs_data.get('temp'))
    if sysfs_cycle and sysfs_cycle > 0:
        result['cycles'] = sysfs_cycle
    elif cycles_dumpsys and cycles_dumpsys > 0:
        result['cycles'] = cycles_dumpsys
    cap_now = None
    cap_design = None
    if sysfs_charge_full and sysfs_charge_design:
        if sysfs_charge_design >= sysfs_charge_full and sysfs_charge_design > 1000000:
            cap_now = sysfs_charge_full / 1000
            cap_design = sysfs_charge_design / 1000
        elif sysfs_charge_full > 1000000:
            cap_now = sysfs_charge_full / 1000
    elif sysfs_charge_full and sysfs_charge_full > 1000000:
        cap_now = sysfs_charge_full / 1000
    if cap_now is None and full_cap_dumpsys and full_cap_dumpsys > 1000000:
        cap_now = full_cap_dumpsys / 1000
    if cap_design is None and full_design_dumpsys and full_design_dumpsys > 1000000:
        cap_design = full_design_dumpsys / 1000
    result['capacity_now_mah'] = int(cap_now) if cap_now else None
    result['capacity_design_mah'] = int(cap_design) if cap_design else None
    if cap_now and cap_design and cap_design > 0:
        health = min(100, int(cap_now / cap_design * 100))
        result['health_pct'] = health
    elif samsung_asoc:
        if 0 < samsung_asoc <= 100:
            result['health_pct'] = samsung_asoc
    label, color = _classify_battery_health(result['health_pct'])
    result['health_label'] = label
    result['health_color'] = color
    if sysfs_temp and sysfs_temp > 0:
        temp_c = sysfs_temp / 10.0 if sysfs_temp > 100 else float(sysfs_temp)
        result['temperature_c'] = temp_c
    if sysfs_voltage and sysfs_voltage > 0 and result['voltage_v'] is None:
        result['voltage_v'] = sysfs_voltage / 1000000.0
    t_label, t_color = _classify_temp(result['temperature_c'])
    result['temp_label'] = t_label
    result['temp_color'] = t_color
    return result
def parse_signal(telephony_output, operator=None, network_type=None, sim_state=None):
    if not telephony_output:
        return []
    results = []
    lines = [l.strip() for l in telephony_output.strip().split('\n') if 'mSignalStrength' in l]
    operators = (operator or '').split(',') if operator else []
    net_types = (network_type or '').split(',') if network_type else []
    sim_states = (sim_state or '').split(',') if sim_state else []
    for idx, line in enumerate(lines):
        slot = {'slot': idx + 1, 'network': None, 'network_gen': None, 'dbm': None, 'level': None, 'max_level': 4, 'classification': 'Sem Sinal', 'color': 'gray', 'bars': 0, 'operator': None, 'sim_absent': False}
        if idx < len(sim_states):
            state = sim_states[idx].strip().upper()
            if state in ('ABSENT', 'NOT_READY', ''):
                slot['sim_absent'] = True
                slot['classification'] = 'Sem Chip'
                results.append(slot)
                continue
        if idx < len(operators):
            op = operators[idx].strip()
            if op and op.lower() not in ('', 'unknown', ','):
                slot['operator'] = op
        if idx < len(net_types):
            nt = net_types[idx].strip()
            if nt and nt.lower() != 'unknown':
                slot['network'] = nt
                if 'NR' in nt or '5G' in nt:
                    slot['network_gen'] = '5G'
                elif 'LTE' in nt:
                    slot['network_gen'] = '4G'
                elif 'HSPA' in nt or 'HSDPA' in nt or 'HSUPA' in nt:
                    slot['network_gen'] = '3G+'
                elif 'WCDMA' in nt or 'UMTS' in nt:
                    slot['network_gen'] = '3G'
                elif 'EDGE' in nt:
                    slot['network_gen'] = '2G'
                elif 'GSM' in nt or 'GPRS' in nt:
                    slot['network_gen'] = '2G'
        primary_match = re.search('primary=CellSignalStrength(\\w+)', line)
        primary_type = primary_match.group(1) if primary_match else None
        if primary_type and slot['network_gen'] is None:
            gen_map = {'Nr': '5G', 'Lte': '4G', 'Wcdma': '3G', 'Gsm': '2G', 'Cdma': 'CDMA'}
            slot['network_gen'] = gen_map.get(primary_type)
        dbm_value = None
        level_value = None
        if primary_type == 'Nr' or slot['network_gen'] == '5G':
            m = re.search('ssRsrp\\s*=\\s*(-?\\d+)', line)
            if m:
                val = int(m.group(1))
                if val != _INVALID:
                    dbm_value = val
            m_level = re.search('mNr=.*?level\\s*=\\s*(\\d+)', line)
            if m_level:
                level_value = int(m_level.group(1))
        elif primary_type == 'Lte' or slot['network_gen'] == '4G':
            m = re.search('mLte=.*?rsrp=(-?\\d+)', line)
            if m:
                val = int(m.group(1))
                if val != _INVALID:
                    dbm_value = val
            m_level = re.search('mLte=.*?level=(\\d+)', line)
            if m_level:
                level_value = int(m_level.group(1))
        elif primary_type == 'Wcdma' or slot['network_gen'] in ('3G', '3G+'):
            m = re.search('mWcdma=.*?rscp=(-?\\d+)', line)
            if m:
                val = int(m.group(1))
                if val != _INVALID:
                    dbm_value = val
            m_level = re.search('mWcdma=.*?level=(\\d+)', line)
            if m_level:
                level_value = int(m_level.group(1))
        elif primary_type == 'Gsm':
            m = re.search('mGsm=.*?rssi=(-?\\d+)', line)
            if m:
                val = int(m.group(1))
                if val != _INVALID:
                    dbm_value = val
            m_level = re.search('mGsm=.*?mLevel=(\\d+)', line)
            if m_level:
                level_value = int(m_level.group(1))
        if dbm_value is None and level_value is None:
            all_levels = re.findall('level=(\\d+)', line)
            for lv in all_levels:
                if not int(lv) > 0:
                    continue
                level_value = int(lv)
                break
        slot['dbm'] = dbm_value
        slot['level'] = level_value if level_value and level_value > 0 else 0 if dbm_value is None else None
        if dbm_value is not None:
            table = _SIGNAL_RSRP_CLASSIFICATION if primary_type in ('Lte', 'Nr') else _SIGNAL_RSCP_CLASSIFICATION
            label, color, bars = _classify_signal(dbm_value, table)
            slot['classification'] = label
            slot['color'] = color
            slot['bars'] = bars
        elif level_value and level_value > 0:
            level_map = {4: ('Excelente', 'green', 4), 3: ('Bom', 'green', 3), 2: ('Moderado', 'yellow', 2), 1: ('Fraco', 'red', 1)}
            info = level_map.get(level_value, ('Fraco', 'red', 1))
            slot['classification'] = info[0]
            slot['color'] = info[1]
            slot['bars'] = info[2]
        else:
            slot['classification'] = 'Sem Sinal'
            slot['color'] = 'gray'
            slot['bars'] = 0
        results.append(slot)
        continue
    return results
def parse_sensors(sensorservice_output):
    result = {'total': 0, 'essenciais_presentes': {}, 'essenciais_ausentes': [], 'gyro_type': None, 'lista': []}
    if not sensorservice_output:
        return result
    seen_types = set()
    gyro_names = []
    pattern = re.compile('(?P<name>[^\\|]+)\\|[^\\|]*\\|[^\\|]*\\| type:\\s*(?:android\\.sensor\\.)?(?P<type_name>\\w+)\\((?P<type_id>\\d+)\\)')
    for line in sensorservice_output.split('\n'):
        m = pattern.search(line)
        if not m:
            continue
        type_id = int(m.group('type_id'))
        name = m.group('name').strip().split(')')[-1].strip() if ')' in m.group('name') else m.group('name').strip()
        if type_id in seen_types and 'WAKE_UP' in line.upper():
            continue
        seen_types.add(type_id)
        if type_id < 100:
            result['lista'].append({'id': type_id, 'name': name})
        if type_id != 4:
            continue
        gyro_names.append(name.lower())
        continue
    result['total'] = len(seen_types)
    for type_id, label in _SENSOR_ESSENCIAIS.items():
        if type_id in seen_types:
            result['essenciais_presentes'][label] = True
        else:
            result['essenciais_ausentes'].append(label)
    if 4 in seen_types:
        if any(('virtual' in n for n in gyro_names)):
            result['gyro_type'] = 'virtual'
            return result
        result['gyro_type'] = 'hardware'
    return result
def parse_touch(input_output, features_output=None):
    result = {'resolution_x': None, 'resolution_y': None, 'display_resolution': None, 'multitouch_points': None, 'has_pressure': False, 'digitizer_oversampling': False, 'touch_detected': False, 'touch_chip': None, 'fingerprint_detected': False, 'fingerprint_chip': None, 'headset_jack': False, 'buttons_detected': False, 'devices': []}
    if not input_output:
        return result
    blocks = re.split('(?=add device \\d+:|/dev/input/event)', input_output)
    _FP_KEYWORDS = ('fp', 'fingerprint', 'goodix', 'fpc', 'jiiov', 'silead', 'egistec', 'synafp')
    _TOUCH_KEYWORDS = ('touch', 'sec_touch', 'nvt', 'ilitek', 'mtk-tpd', 'fts_ts', 'synaptics', 'himax', 'atmel', 'mxt')
    _HEADSET_KEYWORDS = ('headset jack', 'headphone', 'h2w')
    _BUTTON_KEYWORDS = ('gpio-keys', 'pmic', 'pon', 'kpd')
    for block in blocks:
        if not block.strip():
            continue
        name_match = re.search('name:\\s*"([^"]+)"', block)
        if not name_match:
            continue
        dev_name = name_match.group(1)
        dev_lower = dev_name.lower()
        if 'INPUT_PROP_DIRECT' in block:
            result['touch_detected'] = True
            result['touch_chip'] = dev_name
            x_match = re.search('0035\\s*:\\s*value\\s+\\d+,\\s*min\\s+\\d+,\\s*max\\s+(\\d+)', block)
            y_match = re.search('0036\\s*:\\s*value\\s+\\d+,\\s*min\\s+\\d+,\\s*max\\s+(\\d+)', block)
            if x_match and y_match:
                max_x = int(x_match.group(1))
                max_y = int(y_match.group(1))
                result['resolution_x'] = max_x + 1
                result['resolution_y'] = max_y + 1
                if max_x > 2000 and max_y > 4000:
                    result['digitizer_oversampling'] = True
                    disp_x = (max_x + 1) // 4
                    disp_y = (max_y + 1) // 4
                    result['display_resolution'] = f'{disp_x}x{disp_y}'
                else:
                    disp_x = max_x + 1
                    disp_y = max_y + 1
                    _STD_W = [720, 1080, 1440, 1600, 2560]
                    _STD_H = [1280, 1440, 1520, 1560, 1600, 2340, 2400, 2408, 2560, 2880]
                    for std in _STD_W:
                        if not abs(disp_x - std) <= 1:
                            continue
                        disp_x = std
                        break
                    for std in _STD_H:
                        if not abs(disp_y - std) <= 1:
                            continue
                        disp_y = std
                        break
                    result['display_resolution'] = f'{disp_x}x{disp_y}'
            slot_match = re.search('002f\\s*:\\s*value\\s+\\d+,\\s*min\\s+\\d+,\\s*max\\s+(\\d+)', block)
            if slot_match:
                result['multitouch_points'] = int(slot_match.group(1)) + 1
            pressure_match = re.search('003a\\s*:\\s*value\\s+\\d+,\\s*min\\s+\\d+,\\s*max\\s+(\\d+)', block)
            if pressure_match:
                result['has_pressure'] = int(pressure_match.group(1)) > 0
        if any((kw in dev_lower for kw in _FP_KEYWORDS)):
            result['fingerprint_detected'] = True
            result['fingerprint_chip'] = dev_name
        if any((kw in dev_lower for kw in _HEADSET_KEYWORDS)):
            result['headset_jack'] = True
        if any((kw in dev_lower for kw in _BUTTON_KEYWORDS)):
            result['buttons_detected'] = True
        result['devices'].append(dev_name)
        continue
    if not result['fingerprint_detected']:
        if features_output and 'android.hardware.fingerprint' in features_output:
            result['fingerprint_detected'] = True
            result['fingerprint_chip'] = 'sensor lateral/integrado'
    if not result['touch_detected']:
        x_match = re.search('X:\\s*min=\\d+,\\s*max=(\\d+)', input_output)
        y_match = re.search('Y:\\s*min=\\d+,\\s*max=(\\d+)', input_output)
        if x_match and y_match:
            max_x = int(x_match.group(1))
            max_y = int(y_match.group(1))
            result['resolution_x'] = max_x + 1
            result['resolution_y'] = max_y + 1
            result['touch_detected'] = True
            if max_x > 2000 and max_y > 4000:
                result['digitizer_oversampling'] = True
                result['display_resolution'] = f'{(max_x + 1) // 4}x{(max_y + 1) // 4}'
            else:
                result['display_resolution'] = f'{max_x + 1}x{max_y + 1}'
        slot_match = re.search('Slot:\\s*min=\\d+,\\s*max=(\\d+)', input_output)
        if slot_match:
            result['multitouch_points'] = int(slot_match.group(1)) + 1
    return result
def parse_storage(df_output, dev_checks=None):
    result = {'type': None, 'total_gb': None, 'used_gb': None, 'free_gb': None, 'used_pct': None, 'status': 'Normal', 'status_color': 'green'}
    dev_checks = dev_checks or {}
    if dev_checks.get('has_sda'):
        result['type'] = 'UFS'
    elif dev_checks.get('has_mmcblk0'):
        result['type'] = 'eMMC'
    if not df_output:
        return result
    lines = df_output.strip().split('\n')
    best_partition = None
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 6:
            continue
        mount = parts[5] if len(parts) >= 6 else ''
        size_gb = _parse_size_to_gb(parts[1])
        if '/data' in mount or '/storage/emulated' in mount:
            if not size_gb:
                continue
        if best_partition is not None:
            if size_gb > (best_partition.get('size_gb') or 0):
                best_partition = {'size_gb': size_gb, 'used_str': parts[2], 'avail_str': parts[3], 'pct_str': parts[4]}
    if best_partition:
        result['total_gb'] = round(best_partition['size_gb'], 1)
        used_gb = _parse_size_to_gb(best_partition['used_str'])
        free_gb = _parse_size_to_gb(best_partition['avail_str'])
        if used_gb:
            result['used_gb'] = round(used_gb, 1)
        if free_gb:
            result['free_gb'] = round(free_gb, 1)
        pct_str = best_partition['pct_str'].replace('%', '')
        pct = _safe_int(pct_str)
        if pct is not None:
            result['used_pct'] = pct
            if pct >= 95:
                result['status'] = 'Critico'
                result['status_color'] = 'red'
                return result
            if pct >= 85:
                result['status'] = 'Alto'
                result['status_color'] = 'orange'
                return result
            if pct >= 70:
                result['status'] = 'Moderado'
                result['status_color'] = 'yellow'
    return result
def parse_memory(meminfo_output):
    result = {'total_gb': None, 'available_gb': None, 'used_pct': None, 'status': 'Normal', 'status_color': 'green'}
    if not meminfo_output:
        return result
    values = {}
    for line in meminfo_output.strip().split('\n'):
        if ':' in line:
            key, _, val = line.partition(':')
            num = _safe_int(val.strip().split()[0]) if val.strip() else None
            if num is not None:
                values[key.strip()] = num
    total_kb = values.get('MemTotal')
    available_kb = values.get('MemAvailable')
    if total_kb:
        result['total_gb'] = round(total_kb / 1048576, 1)
    if available_kb:
        result['available_gb'] = round(available_kb / 1048576, 1)
    if total_kb and available_kb:
        used_pct = int((total_kb - available_kb) / total_kb * 100)
        result['used_pct'] = used_pct
        if used_pct >= 90:
            result['status'] = 'Critico'
            result['status_color'] = 'red'
            return result
        if used_pct >= 75:
            result['status'] = 'Alto'
            result['status_color'] = 'orange'
            return result
        if used_pct >= 60:
            result['status'] = 'Moderado'
            result['status_color'] = 'yellow'
    return result
def parse_thermal(thermalservice_output):
    result = {'available': False, 'cpu': None, 'gpu': None, 'battery': None, 'skin': None, 'status': 'Normal', 'status_color': 'green'}
    if not thermalservice_output:
        return result
    temps = re.findall('Temperature\\{mValue=([\\d.]+),\\s*mType=(\\d+),\\s*mName=(\\w+)', thermalservice_output)
    if not temps:
        return result
    result['available'] = True
    for value_str, type_id, name in temps:
        temp_c = _safe_float(value_str)
        if temp_c is None or temp_c <= 0:
            continue
        name_lower = name.lower()
        if 'cpu' in name_lower and result['cpu'] is None:
            result['cpu'] = temp_c
        elif 'gpu' in name_lower and result['gpu'] is None:
            result['gpu'] = temp_c
        elif 'battery' in name_lower or 'batt' in name_lower:
            result['battery'] = temp_c
        elif 'skin' in name_lower:
            result['skin'] = temp_c
    max_temp = max(filter(None, [result['cpu'], result['gpu'], result['skin']]), default=None)
    if max_temp:
        label, color = _classify_temp(max_temp)
        result['status'] = label
        result['status_color'] = color
    return result
def parse_cpu(cpuinfo_output, max_freq=None, platform=None):
    result = {'vendor': None, 'core_count': 0, 'cores': {}, 'architecture': None, 'is_64bit': False, 'max_freq_ghz': None, 'platform': platform, 'soc_name': None, 'category': None}
    if platform:
        result['soc_name'] = _PLATFORM_SOC.get(platform.lower())
    if not cpuinfo_output:
        return result
    cores = []
    current = {}
    for line in cpuinfo_output.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('processor'):
            if current:
                cores.append(current)
            current = {}
        elif ':' in line:
            key, _, val = line.partition(':')
            current[key.strip()] = val.strip()
    if current:
        cores.append(current)
    result['core_count'] = len(cores)
    if not cores:
        return result
    implementer = cores[0].get('CPU implementer', '')
    result['vendor'] = _CPU_VENDORS.get(implementer, 'Desconhecido')
    arch = cores[0].get('CPU architecture', '')
    result['architecture'] = f'ARMv{arch}' if arch else None
    result['is_64bit'] = arch in ('8', '8.1', '8.2', '8.3', '8.4', '8.5', '9')
    core_dist = {}
    for core in cores:
        part = core.get('CPU part', '')
        core_name = _CPU_CORES.get(part, f'Core ({part})' if part else 'Desconhecido')
        core_dist[core_name] = core_dist.get(core_name, 0) + 1
    result['cores'] = core_dist
    freq_khz = _safe_int(max_freq)
    if freq_khz and freq_khz > 0:
        result['max_freq_ghz'] = round(freq_khz / 1000000, 2)
    if platform:
        p_lower = platform.lower()
        if 'mt' in p_lower or 'mediatek' in p_lower:
            result['vendor'] = 'MediaTek'
        elif 'qcom' in p_lower or 'bengal' in p_lower or 'sm' in p_lower or 'lahaina' in p_lower:
            result['vendor'] = 'Qualcomm'
        elif 'exynos' in p_lower or 'universal' in p_lower or 'erd' in p_lower or 's5e' in p_lower:
            result['vendor'] = 'Samsung Exynos'
        elif 'ums' in p_lower or 'sprd' in p_lower:
            result['vendor'] = 'UNISOC'
    has_big = len(core_dist) > 1
    count = len(cores)
    if any(('X' in name for name in core_dist)):
        result['category'] = 'Flagship'
        return result
    if any(('A76' in name for name in core_dist if 'A78' in name or 'A77' in name)):
        result['category'] = 'Alto'
        return result
    if count >= 8 and has_big:
        result['category'] = 'Intermediario'
        return result
    if count >= 6:
        result['category'] = 'Intermediario'
        return result
    result['category'] = 'Entrada'
    return result
def parse_identity(props):
    result = {'model': props.get('model', ''), 'brand': props.get('brand', ''), 'android_version': props.get('android', ''), 'security_patch': props.get('security', ''), 'device_codename': props.get('device', ''), 'platform': props.get('platform', ''), 'build_id': props.get('build_id', ''), 'kernel': props.get('kernel', ''), 'baseband': props.get('baseband', ''), 'bootloader_locked': True, 'chipset_vendor': None, 'soc_name': None}
    flash_locked = props.get('flash_locked', '1')
    bootstate = props.get('bootstate', 'green')
    result['bootloader_locked'] = flash_locked == '1' and bootstate == 'green'
    hw = (props.get('hardware') or '').lower()
    platform = (props.get('platform') or '').lower()
    if 'qcom' in hw or 'bengal' in platform or 'lahaina' in platform:
        result['chipset_vendor'] = 'Qualcomm'
    elif 'mt' in hw or 'mt' in platform:
        result['chipset_vendor'] = 'MediaTek'
    elif 'ums' in hw or 'sprd' in platform:
        result['chipset_vendor'] = 'UNISOC'
    elif 'exynos' in hw or 'universal' in platform or 'erd' in hw or 's5e' in hw:
        result['chipset_vendor'] = 'Samsung Exynos'
    if platform:
        result['soc_name'] = _PLATFORM_SOC.get(platform)
    return result
def parse_camera(camera_output):
    result = {'total': 0, 'cameras': [], 'active_clients': 0, 'has_flash': False}
    if not camera_output:
        return result
    active_match = re.search('Number of open cameras:\\s*(\\d+)', camera_output)
    if active_match:
        result['active_clients'] = int(active_match.group(1))
    sections = re.split('== Camera HAL device [^\\n]+static information: ==', camera_output)
    all_cameras = []
    for section in sections[1:]:
        facing_m = re.search('^\\s*Facing:\\s*(Back|Front)', section, re.MULTILINE)
        flash_m = re.search('Has a flash unit:\\s*(true|false)', section, re.IGNORECASE)
        res_m = re.search('pixelArraySize\\s*\\([^)]*\\):[^\\n]*\\n\\s*\\[(\\d+)\\s+(\\d+)\\s*\\]', section)
        if not facing_m:
            continue
        if not res_m:
            continue
        w, h = int(res_m.group(1)), int(res_m.group(2))
        mp = round(w * h / 1000000, 1)
        all_cameras.append({'facing': facing_m.group(1), 'flash': flash_m.group(1).lower() == 'true' if flash_m else False, 'megapixels': mp, 'resolution': f'{w}x{h}'})
        continue
    seen = set()
    unique_cameras = []
    for cam in all_cameras:
        key = cam['facing'], cam['resolution']
        if key not in seen:
            seen.add(key)
            unique_cameras.append(cam)
    back_cameras = [c for c in unique_cameras if c['facing'] == 'Back']
    front_cameras = [c for c in unique_cameras if c['facing'] == 'Front']
    if len(front_cameras) > 1:
        front_cameras.sort(key=(lambda c: c.get('megapixels') or 0), reverse=True)
        front_cameras = front_cameras[:1]
    back_cameras.sort(key=(lambda c: c.get('megapixels') or 0), reverse=True)
    result['cameras'] = back_cameras + front_cameras
    result['total'] = len(result['cameras'])
    result['has_flash'] = any((c.get('flash') for c in result['cameras']))
    return result
_PARTITION_CATEGORIES = {'Boot': ['xbl', 'xbl_config', 'abl', 'boot', 'init_boot', 'vendor_boot', 'hyp', 'rpm', 'tz', 'devcfg', 'qupfw', 'lk', 'lk2', 'bootloader1', 'bootloader2', 'preloader', 'tee', 'tee1', 'tee2', 'gz', 'scp', 'sspm', 'mcupm', 'uboot', 'uboot_log', 'spl', 'sml', 'trustos', 'teecfg', 'hypervsior', 'hypervisor', 'ldfw', 'blcmd', 'bota', 'btd', 'uefivarstore', 'apdp'], 'Sistema': ['super', 'system', 'vendor', 'product', 'odm', 'vbmeta', 'vbmeta_system', 'vbmeta_vendor', 'vbmeta_odm', 'vbmeta_product', 'vbmeta_system_ext', 'avbmeta_rs', 'dtbo', 'dtb', 'logo', 'fbootlogo', 'pi_img', 'tranfs', 'carrier', 'cust', 'reserve', 'splash', 'optics', 'prism', 'omr'], 'Recovery': ['recovery', 'rescue', 'common_rs1', 'common_rs2'], 'Modem/RF': ['modem', 'dsp', 'bluetooth', 'modemst1', 'modemst2', 'fsg', 'fsc', 'md1img', 'md1dsp', 'md3img', 'connsys_bt', 'connsys_wifi', 'connsys_gnss', 'rfcal', 'wmt', 'l_modem', 'l_agdsp', 'l_gdsp', 'l_ldsp', 'radio', 'cp_debug', 'cpefs', 'efs', 'sec_efs', 'apnhlos'], 'Seguranca': ['keymaster', 'keystore', 'cmnlib', 'cmnlib64', 'mdtp', 'mdtpsecapp', 'uefisecapp', 'frp', 'secdata', 'imagefv', 'featenabler', 'sec', 'seccfg', 'efuse', 'efuseBackup', 'otp', 'keydata', 'keyrefuge', 'keystorage', 'fmp_selftest', 'persistent', 'uh', 'uhcfg', 'tzsw', 'tzar', 'bksecapp', 'dip', 'hdm', 'spu', 'spunvm', 'ssd', 'storsec', 'toolsfv', 'tz_kg', 'tziccc', 'vk', 'questdatafv'], 'Dados': ['userdata', 'metadata', 'persist', 'misc', 'protect', 'protect2', 'cache', 'miscdata', 'my_preload', 'oplusreserve1', 'oplusreserve2', 'oplusreserve3', 'oplusreserve4', 'oplusreserve5', 'opporeserve', 'blackbox', 'debug', 'reserved', 'reserved2', 'logdump', 'logfs', 'rawdump', 'dqmdbg', 'pad'], 'NVRAM/Calibracao': ['nvram', 'nvdata', 'nvcfg', 'proinfo', 'expdb', 'boot_para', 'dram_para', 'para', 'l_fixnv1', 'l_fixnv2', 'l_deltanv', 'l_runtimenv1', 'l_runtimenv2', 'prodnv', 'calinv', 'sysdumpdb', 'prodpersist', 'ocdt', 'pm_sys', 'param', 'up_param', 'nad_refer', 'steady', 'ddr', 'devinfo', 'dpo', 'limits', 'limits-cdsp']}
def parse_partitions(partition_output):
    result = {'total': 0, 'ab_slot': False, 'storage_type': None, 'path': None, 'partitions': [], 'categories': {}, 'uncategorized': []}
    if not partition_output:
        return result
    lines = partition_output.strip().split('\n')
    for line in lines:
        if not line.startswith('PATH:'):
            continue
        result['path'] = line[5:].strip()
        break
    for line in lines:
        match = re.match('.*\\s+(\\S+)\\s+->\\s+(/dev/block/\\S+)', line)
        if match:
            name = match.group(1)
            target = match.group(2)
            result['partitions'].append({'name': name, 'target': target})
            if result['storage_type'] is not None:
                continue
            if 'mmcblk' in target:
                result['storage_type'] = 'eMMC'
            elif 'sda' in target or 'sdb' in target or 'sdc' in target:
                result['storage_type'] = 'UFS'
    result['total'] = len(result['partitions'])
    names = [p['name'] for p in result['partitions']]
    result['ab_slot'] = any((n.endswith('_a') for n in names)) and any((n.endswith('_b') for n in names))
    categorized_names = set()
    for cat, keywords in _PARTITION_CATEGORIES.items():
        found = []
        for p in result['partitions']:
            base_name = re.sub('_[ab]$', '', p['name'])
            if base_name not in keywords:
                continue
            if base_name not in found:
                found.append(base_name)
                categorized_names.add(base_name)
        if found:
            result['categories'][cat] = found
    _BLOCK_DEVICE_PREFIXES = ('mmcblk', 'sda', 'sdb', 'sdc', 'sdd', 'sde', 'sdf')
    all_base_names = set()
    for p in result['partitions']:
        base_name = re.sub('_[ab]$', '', p['name'])
        if any((base_name.startswith(pfx) for pfx in _BLOCK_DEVICE_PREFIXES)):
            continue
        all_base_names.add(base_name)
    uncategorized = sorted(all_base_names - categorized_names)
    if uncategorized:
        result['uncategorized'] = uncategorized
    return result
def parse_network(connectivity_output):
    result = {'active_network': None, 'wifi_available': False, 'mobile_available': False, 'blocked_apps': 0, 'blocked_uids': [], 'transports': []}
    if not connectivity_output:
        return result
    active_match = re.search('Active default network:\\s*(.+)', connectivity_output)
    if active_match:
        active = active_match.group(1).strip()
        if active.lower() == 'none':
            result['active_network'] = 'Nenhuma'
        else:
            result['active_network'] = active
    if 'Transports: WIFI' in connectivity_output:
        result['wifi_available'] = True
        if 'WIFI' not in result['transports']:
            result['transports'].append('Wi-Fi')
    if 'Transports: CELLULAR' in connectivity_output:
        result['mobile_available'] = True
        if 'Celular' not in result['transports']:
            result['transports'].append('Celular')
    if 'CONNECTED' in connectivity_output and 'WIFI' in connectivity_output:
        result['active_network'] = 'Wi-Fi'
    elif 'CONNECTED' in connectivity_output and 'MOBILE' in connectivity_output:
        result['active_network'] = 'Celular'
    blocked_entries = re.findall('UID=(\\d+)\\s+blockedReasons=(\\d+)', connectivity_output)
    blocked_uids = [int(uid) for uid, reason in blocked_entries if int(reason) > 0]
    result['blocked_apps'] = len(blocked_uids)
    result['blocked_uids'] = blocked_uids
    return result
def parse_system_events(logcat_output, uptime_output=None):
    result = {'uptime': None, 'load_avg': None, 'total_errors': 0, 'crashes': 0, 'anrs': 0, 'network_errors': 0, 'permission_errors': 0, 'top_sources': [], 'recent_errors': []}
    if uptime_output:
        up_match = re.search('up\\s+(.+?),\\s+\\d+\\s+user', uptime_output)
        if up_match:
            result['uptime'] = up_match.group(1).strip()
        load_match = re.search('load average:\\s*([\\d.]+)', uptime_output)
        if load_match:
            result['load_avg'] = float(load_match.group(1))
    if not logcat_output:
        return result
    lines = [l for l in logcat_output.strip().split('\n') if l.strip() if not l.startswith('---')]
    result['total_errors'] = len(lines)
    source_count = {}
    for line in lines:
        lower = line.lower()
        if 'crash' in lower or 'fatal' in lower or 'died' in lower:
            result['crashes'] += 1
        if 'anr' in lower:
            result['anrs'] += 1
        if 'network' in lower or 'host' in lower or 'connect' in lower:
            result['network_errors'] += 1
        if 'permission' in lower or 'denied' in lower:
            result['permission_errors'] += 1
        tag_match = re.match('\\d{2}-\\d{2}\\s+[\\d:.]+\\s+\\d+\\s+\\d+\\s+\\w\\s+(\\S+):', line)
        if tag_match:
            tag = tag_match.group(1)
            source_count[tag] = source_count.get(tag, 0) + 1
    sorted_sources = sorted(source_count.items(), key=(lambda x: x[1]), reverse=True)
    result['top_sources'] = sorted_sources[:5]
    seen_tags = set()
    for line in reversed(lines):
        tag_match = re.match('\\d{2}-\\d{2}\\s+[\\d:.]+\\s+\\d+\\s+\\d+\\s+\\w\\s+(\\S+):\\s*(.*)', line)
        if tag_match:
            tag = tag_match.group(1)
            msg = tag_match.group(2).strip()[:80]
            if tag in seen_tags:
                continue
            if len(result['recent_errors']) < 5:
                result['recent_errors'].append({'tag': tag, 'msg': msg})
                seen_tags.add(tag)
    return result
def parse_wifi(wifi_output):
    result = {'enabled': False, 'connected': False, 'ssid': None, 'rssi': None, 'frequency_mhz': None, 'link_speed_mbps': None, 'security': None, 'wifi_standard': None, 'signal_label': None, 'signal_color': 'gray', 'band': None}
    if not wifi_output:
        return result
    if 'Wi-Fi is enabled' in wifi_output:
        result['enabled'] = True
    elif 'Wi-Fi is disabled' in wifi_output:
        return result
    wifi_match = re.search('mWifiInfo SSID:\\s*([^,]+),.*?RSSI:\\s*(-?\\d+),.*?Link speed:\\s*(-?\\d+)Mbps.*?Frequency:\\s*(-?\\d+)MHz', wifi_output)
    if wifi_match:
        ssid = wifi_match.group(1).strip().strip('"')
        rssi = int(wifi_match.group(2))
        link_speed = int(wifi_match.group(3))
        freq = int(wifi_match.group(4))
        if ssid and ssid != '<unknown ssid>' and rssi != -127:
            result['connected'] = True
            result['ssid'] = ssid
            result['rssi'] = rssi
            result['link_speed_mbps'] = link_speed if link_speed > 0 else None
            result['frequency_mhz'] = freq if freq > 0 else None
            if freq > 0:
                if freq >= 5000:
                    result['band'] = '5 GHz'
                elif freq >= 2400:
                    result['band'] = '2.4 GHz'
            if rssi >= -50:
                result['signal_label'] = 'Excelente'
                result['signal_color'] = 'green'
            elif rssi >= -60:
                result['signal_label'] = 'Bom'
                result['signal_color'] = 'green'
            elif rssi >= -70:
                result['signal_label'] = 'Moderado'
                result['signal_color'] = 'yellow'
            elif rssi >= -80:
                result['signal_label'] = 'Fraco'
                result['signal_color'] = 'orange'
            else:
                result['signal_label'] = 'Muito Fraco'
                result['signal_color'] = 'red'
    std_match = re.search('Wi-Fi standard:\\s*(\\d+)', wifi_output)
    if std_match:
        std_code = int(std_match.group(1))
        standards = {1: '802.11a/b/g', 4: 'Wi-Fi 4 (n)', 5: 'Wi-Fi 5 (ac)', 6: 'Wi-Fi 6 (ax)', 7: 'Wi-Fi 7 (be)'}
        result['wifi_standard'] = standards.get(std_code)
    return result
def parse_usb(usb_output):
    result = {'state': None, 'mode': None, 'functions': None, 'speed': None, 'otg_supported': False}
    if not usb_output:
        return result
    state_match = re.search('kernel_state=(\\w+)', usb_output)
    if state_match:
        state = state_match.group(1)
        state_map = {'CONFIGURED': 'Conectado', 'CONNECTED': 'Conectado', 'DISCONNECTED': 'Desconectado', 'NOT_ATTACHED': 'Desconectado'}
        result['state'] = state_map.get(state, state)
    mode_match = re.search('current_mode=(\\w+)', usb_output)
    if mode_match:
        mode = mode_match.group(1)
        mode_map = {'ufp': 'Dispositivo (UFP)', 'dfp': 'Host (DFP)', 'none': 'Nenhum'}
        result['mode'] = mode_map.get(mode, mode)
    func_match = re.search('current_functions_applied=true', usb_output)
    if func_match:
        result['functions'] = 'Ativas'
    modes_match = re.search('supported_modes=([^\\n]+)', usb_output)
    if modes_match:
        modes = modes_match.group(1).strip()
        result['otg_supported'] = 'dual' in modes.lower()
    return result
def parse_audio(audio_output, policy_output=None):
    result = {'mode': 'Normal', 'mic_muted': False, 'has_vibrator': False, 'output_device': None, 'headset_connected': False, 'bluetooth_name': None, 'volume_music': None, 'earpiece_ok': False, 'speaker_ok': False, 'mic_count': 0, 'mic_locations': [], 'fm_tuner': False, 'echo_reference': False, 'audio_devices_out': [], 'audio_devices_in': []}
    combined = (audio_output or '') + '\n' + (policy_output or '')
    if not combined.strip():
        return result
    mode_match = re.search('audio mode:\\s*(\\w+)', audio_output or '')
    if not mode_match:
        mode_match = re.search('phone state:\\s*(\\w+)', audio_output or '')
    if mode_match:
        mode_raw = mode_match.group(1).upper()
        mode_map = {'NORMAL': 'Normal', 'MODE_NORMAL': 'Normal', 'RINGTONE': 'Tocando', 'MODE_RINGTONE': 'Tocando', 'IN_CALL': 'Em ligacao', 'MODE_IN_CALL': 'Em ligacao', 'IN_COMMUNICATION': 'Em comunicacao', 'MODE_IN_COMMUNICATION': 'Em comunicacao'}
        result['mode'] = mode_map.get(mode_raw, mode_raw)
    if re.search('Mic Mute:\\s*true', audio_output or '', re.IGNORECASE):
        result['mic_muted'] = True
    elif re.search('mic mute.*?true', audio_output or '', re.IGNORECASE):
        result['mic_muted'] = True
    if re.search('mHasVibrator:\\s*true', audio_output or '', re.IGNORECASE):
        result['has_vibrator'] = True
    elif re.search('vibrator.*?true', audio_output or '', re.IGNORECASE):
        result['has_vibrator'] = True
    vol_match = re.search('(?:Stream\\s*3|STREAM_MUSIC).*?index:\\s*(\\d+)', audio_output or '', re.DOTALL)
    if not vol_match:
        vol_match = re.search('music.*?streamVolume.*?(\\d+)', audio_output or '', re.IGNORECASE)
    if vol_match:
        result['volume_music'] = int(vol_match.group(1))
    if re.search('AUDIO_DEVICE_OUT_WIRED_HEADSET|AUDIO_DEVICE_OUT_WIRED_HEADPHONE', audio_output or ''):
        result['headset_connected'] = True
    bt_match = re.search('mBluetoothName[=:]\\s*(\\S+)', audio_output or '')
    if bt_match and bt_match.group(1).lower() not in ('null', 'none', ''):
        result['bluetooth_name'] = bt_match.group(1)
    out_match = re.search('(?:Output devices|mSafeMediaVolumeDevice|Routing.*output).*?(SPEAKER|EARPIECE|WIRED_HEADSET|WIRED_HEADPHONE|BT_SCO|BT_A2DP)', audio_output or '', re.IGNORECASE)
    if out_match:
        dev_map = {'SPEAKER': 'Alto-falante (Speaker)', 'EARPIECE': 'Auricular (Earpiece)', 'WIRED_HEADSET': 'Fone com fio', 'WIRED_HEADPHONE': 'Fone com fio', 'BT_SCO': 'Bluetooth (chamada)', 'BT_A2DP': 'Bluetooth (midia)'}
        result['output_device'] = dev_map.get(out_match.group(1).upper(), out_match.group(1))
    policy_src = policy_output or audio_output or ''
    out_devices = re.findall('Port ID:\\s*\\d+;\\s*"([^"]+)";\\s*\\{(AUDIO_DEVICE_OUT_\\w+)', policy_src)
    seen_out = set()
    for name, dev_type in out_devices:
        if dev_type not in seen_out:
            seen_out.add(dev_type)
            result['audio_devices_out'].append(name)
            if 'EARPIECE' in dev_type:
                result['earpiece_ok'] = True
            if 'SPEAKER' in dev_type:
                result['speaker_ok'] = True
    in_devices = re.findall('Port ID:\\s*\\d+;\\s*"([^"]+)";\\s*\\{(AUDIO_DEVICE_IN_\\w+)(?:,\\s*@:(\\w*))?', policy_src)
    seen_in = set()
    for name, dev_type, addr in in_devices:
        if dev_type not in seen_in:
            seen_in.add(dev_type)
            result['audio_devices_in'].append(name)
            if 'BUILTIN_MIC' in dev_type or 'BACK_MIC' in dev_type:
                result['mic_count'] += 1
                loc = addr if addr else 'inferior' if 'BUILTIN' in dev_type else 'traseiro'
                result['mic_locations'].append(loc)
            if 'FM_TUNER' in dev_type:
                result['fm_tuner'] = True
            if 'ECHO_REFERENCE' in dev_type:
                result['echo_reference'] = True
    if not result['speaker_ok']:
        if 'SPEAKER' in combined.upper():
            result['speaker_ok'] = True
    if not result['earpiece_ok']:
        if 'EARPIECE' in combined.upper():
            result['earpiece_ok'] = True
    return result
