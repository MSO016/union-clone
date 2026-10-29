'''
Formatadores V2 ÔÇö Saida limpa para terminal.
Recebem dicts padronizados do diag_parser_v2 e devolvem strings
prontas para exibicao. Maximo ~15-20 linhas por diagnostico.
Ref: administrativo/documentacao/09-08-2026-DIAGNOSTICO-ANDROID-PADRONIZACAO/
'''
from datetime import datetime
_LINE = 'ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ'
_DASH = 'ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ'
_BRAND = 'TECH UNION SOLUTIONS'
_SLOGAN = 'Feito de tecnicos para tecnicos'
def wrap_output(body, elapsed_ms=None, operation=None):
    """
Envolve qualquer saida formatada com header e footer padrao.
Args:
    body: string formatada do diagnostico
    elapsed_ms: tempo em ms da operacao (opcional)
    operation: nome da operacao realizada (ex: 'Analise de Rede')
"""
    now = datetime.now().strftime('%d/%m/%Y  %H:%M:%S')
    header = f'\n{'============================================'}\n  {_BRAND}\n{'============================================'}'
    footer_parts = []
    if operation:
        footer_parts.append(f'  {operation} - concluido')
    footer_parts.append(f'  {now}')
    if elapsed_ms is not None:
        if elapsed_ms >= 1000:
            footer_parts.append(f'  Tempo: {elapsed_ms / 1000:.1f}s')
        else:
            footer_parts.append(f'  Tempo: {elapsed_ms}ms')
    footer_parts.append(f'  {_SLOGAN}')
    footer = f'\n{'ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ'}\n' + '\n'.join(footer_parts) + f'\n{'ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ'}'
    return f'{header}\n{body}\n{footer}'
def _pad(label, value, width=16):
    '''Alinha label com pontos ate o valor.'''
    dots = '.' * max(1, width - len(label))
    return f'  {label}{dots} {value}'
def _bars_visual(count, max_bars=5):
    '''Gera barras visuais de sinal.'''
    filled = min(count, max_bars)
    return 'Ôûá' * filled + 'Ôûí' * (max_bars - filled)
def format_battery(data):
    '''Formata resultado do parse_battery.'''
    if not data:
        return '  Informacao indisponivel neste dispositivo.'
    lines = [f'\n{_LINE}', '  BATERIA', _LINE]
    if data.get('health_pct') is not None:
        lines.append(_pad('Saude', f'{data['health_pct']}% ({data['health_label']})'))
    else:
        lines.append(_pad('Saude', 'Indisponivel'))
    if data.get('cycles') is not None:
        lines.append(_pad('Ciclos', str(data['cycles'])))
    if data.get('capacity_now_mah') and data.get('capacity_design_mah'):
        now = data['capacity_now_mah']
        design = data['capacity_design_mah']
        lines.append(_pad('Capacidade', f'{now} / {design} mAh (atual/fabrica)'))
    elif data.get('capacity_now_mah'):
        lines.append(_pad('Capacidade', f'{data['capacity_now_mah']} mAh'))
    if data.get('level') is not None:
        lines.append(_pad('Nivel', f'{data['level']}%'))
    if data.get('temperature_c') is not None:
        temp_suffix = f' ({data['temp_label']})' if data.get('temp_label') else ''
        lines.append(_pad('Temperatura', f'{data['temperature_c']:.1f} C{temp_suffix}'))
    if data.get('voltage_v') is not None:
        lines.append(_pad('Voltagem', f'{data['voltage_v']:.3f}V'))
    if data.get('charging'):
        parts = ['Sim']
        if data.get('charging_watts'):
            parts.append(f'{data['charging_watts']}W')
        if data.get('charging_source'):
            parts.append(f'via {data['charging_source']}')
        lines.append(_pad('Carregando', ' '.join(parts)))
    else:
        lines.append(_pad('Carregando', 'Nao'))
    if data.get('technology'):
        lines.append(_pad('Tecnologia', data['technology']))
    lines.append(_LINE)
    return '\n'.join(lines)
def format_signal(slots):
    '''Formata resultado do parse_signal (lista de slots).'''
    if not slots:
        return '  Informacao indisponivel neste dispositivo.'
    lines = [f'\n{_LINE}', '  SINAL CELULAR', _LINE]
    for slot in slots:
        prefix = f'SIM {slot['slot']}' if len(slots) > 1 else 'Rede'
        if slot.get('sim_absent'):
            lines.append(_pad(prefix, 'Sem chip'))
            continue
        if slot['bars'] == 0:
            if slot['dbm'] is None:
                lines.append(_pad(prefix, 'Sem sinal'))
                continue
        gen = slot.get('network_gen') or ''
        net_label = f'{gen} ({slot['network']})' if slot.get('network') and gen else gen or 'Conectado'
        lines.append(_pad(prefix, net_label))
        if slot.get('dbm') is not None:
            bars = _bars_visual(slot['bars'])
            lines.append(_pad('  Intensidade', f'{slot['dbm']} dBm ({slot['classification']}) {bars}'))
        elif slot.get('level') is not None:
            bars = _bars_visual(slot['level'])
            lines.append(_pad('  Intensidade', f'Nivel {slot['level']}/4 ({slot['classification']}) {bars}'))
        if not slot.get('operator'):
            continue
        lines.append(_pad('  Operadora', slot['operator']))
        continue
    lines.append(_LINE)
    return '\n'.join(lines)
def format_sensors(data):
    '''Formata resultado do parse_sensors.'''
    if not data or data.get('total', 0) == 0:
        return '  Informacao indisponivel neste dispositivo.'
    lines = [f'\n{_LINE}', '  SENSORES', _LINE]
    presentes = data.get('essenciais_presentes', {})
    ausentes = data.get('essenciais_ausentes', [])
    total_essenciais = len(presentes) + len(ausentes)
    if presentes:
        lines.append('  Detectados:')
        for name in presentes:
            lines.append(f'    Ô£ö {name}')
    if ausentes:
        lines.append('')
        lines.append('  Ausentes:')
        for name in ausentes:
            lines.append(f'    Ô£û {name}')
    lines.append(f'\n  {'ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ'}')
    lines.append(_pad('Resultado', f'{len(presentes)}/{total_essenciais} essenciais'))
    if data.get('gyro_type') == 'virtual':
        lines.append(_pad('Giroscopio', 'Virtual (software)'))
    elif data.get('gyro_type') == 'hardware':
        lines.append(_pad('Giroscopio', 'Hardware dedicado'))
    lines.append(_LINE)
    return '\n'.join(lines)
def format_touch(data):
    '''Formata resultado do parse_touch para diagnostico completo de input.'''
    if not data:
        return '  Informacao indisponivel neste dispositivo.'
    lines = [f'\n{_LINE}', '  DIAGNOSTICO TOUCH / INPUT', _LINE]
    if data.get('touch_detected'):
        chip_name = data.get('touch_chip', 'Generico')
        lines.append('  Ô£ö Digitalizador detectado')
        lines.append(_pad('Chip', chip_name))
    else:
        lines.append('  Ô£û DIGITALIZADOR NAO DETECTADO')
        lines.append('')
        lines.append('    Possivel defeito: flex, conector ou IC do touch')
        lines.append(_LINE)
        return '\n'.join(lines)
    if data.get('display_resolution'):
        lines.append(_pad('Resolucao display', data['display_resolution']))
    if data.get('digitizer_oversampling'):
        lines.append(_pad('Precisao', 'Alta (oversampling 4x)'))
    if data.get('multitouch_points'):
        pts = data['multitouch_points']
        qual = 'Premium' if pts >= 10 else 'Basico'
        lines.append(_pad('Multi-touch', f'{pts} pontos ({qual})'))
    pressure_icon = 'Ô£ö' if data.get('has_pressure') else 'Ô£û'
    lines.append(_pad('Pressao', f'{pressure_icon} {'Suportada' if data.get('has_pressure') else 'Nao suportada'}'))
    lines.append(f'\n  {'ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ'}')
    lines.append('  Sensores de Input:')
    fp_icon = 'Ô£ö' if data.get('fingerprint_detected') else 'Ô£û'
    fp_name = data.get('fingerprint_chip', '')
    if fp_name and fp_name != 'sensor lateral/integrado':
        fp_detail = f' ({fp_name})'
    elif fp_name == 'sensor lateral/integrado':
        fp_detail = ' (lateral/integrado)'
    else:
        fp_detail = ''
    lines.append(f'    {fp_icon} Biometria (fingerprint){fp_detail}')
    jack_icon = 'Ô£ö' if data.get('headset_jack') else 'Ô£û'
    lines.append(f'    {jack_icon} Jack de audio (P2/P3)')
    btn_icon = 'Ô£ö' if data.get('buttons_detected') else 'Ô£û'
    lines.append(f'    {btn_icon} Botoes fisicos (power/volume)')
    lines.append(_LINE)
    return '\n'.join(lines)
def format_storage(data):
    '''Formata resultado do parse_storage.'''
    if not data:
        return '  Informacao indisponivel neste dispositivo.'
    lines = [f'\n{_LINE}', '  ARMAZENAMENTO', _LINE]
    if data.get('type'):
        speed_hint = '(rapido)' if data['type'] == 'UFS' else ''
        lines.append(_pad('Tipo', f'{data['type']} {speed_hint}'.strip()))
    if data.get('total_gb'):
        lines.append(_pad('Capacidade', f'{data['total_gb']:.0f} GB'))
    if data.get('used_gb') is not None and data.get('free_gb') is not None:
        lines.append(_pad('Usado', f'{data['used_gb']:.1f} GB ({data.get('used_pct', '?')}%)'))
        lines.append(_pad('Livre', f'{data['free_gb']:.1f} GB'))
    if data.get('status') != 'Normal':
        lines.append(f'\n  ** {data['status'].upper()} ÔÇö Espaco em disco baixo **')
    lines.append(_LINE)
    return '\n'.join(lines)
def format_memory(data):
    '''Formata resultado do parse_memory.'''
    if not data or data.get('total_gb') is None:
        return '  Informacao indisponivel neste dispositivo.'
    lines = [f'\n{_LINE}', '  MEMORIA RAM', _LINE]
    lines.append(_pad('Total', f'{data['total_gb']:.1f} GB'))
    if data.get('available_gb') is not None:
        lines.append(_pad('Disponivel', f'{data['available_gb']:.1f} GB'))
    if data.get('used_pct') is not None:
        lines.append(_pad('Em uso', f'{data['used_pct']}%'))
    if data.get('status') != 'Normal':
        lines.append(f'\n  ** {data['status'].upper()} ÔÇö Memoria sob pressao **')
    lines.append(_LINE)
    return '\n'.join(lines)
def format_thermal(data):
    '''Formata resultado do parse_thermal.'''
    if not data or not data.get('available'):
        return '  Temperatura indisponivel neste dispositivo.'
    lines = [f'\n{_LINE}', '  TEMPERATURA', _LINE]
    if data.get('cpu') is not None:
        lines.append(_pad('CPU', f'{data['cpu']:.1f} C'))
    if data.get('gpu') is not None:
        lines.append(_pad('GPU', f'{data['gpu']:.1f} C'))
    if data.get('battery') is not None:
        lines.append(_pad('Bateria', f'{data['battery']:.1f} C'))
    if data.get('skin') is not None:
        lines.append(_pad('Carcaca', f'{data['skin']:.1f} C'))
    if data.get('skin') and not data.get('cpu') and not data.get('gpu'):
        lines.pop()
        lines.append(_pad('Dispositivo', f'{data['skin']:.1f} C'))
    if data.get('status') != 'Normal':
        lines.append(f'\n  ** {data['status'].upper()} ÔÇö Dispositivo aquecido **')
    lines.append(_LINE)
    return '\n'.join(lines)
def format_cpu(data):
    '''Formata resultado do parse_cpu.'''
    if not data or data.get('core_count', 0) == 0:
        return '  Informacao indisponivel neste dispositivo.'
    lines = [f'\n{_LINE}', '  PROCESSADOR', _LINE]
    if data.get('soc_name'):
        lines.append(_pad('Chipset', data['soc_name']))
    elif data.get('vendor'):
        lines.append(_pad('Fabricante', data['vendor']))
    if data.get('platform'):
        lines.append(_pad('Plataforma', data['platform']))
    lines.append(_pad('Nucleos', str(data['core_count'])))
    if data.get('cores'):
        for core_name, count in data['cores'].items():
            lines.append(f'    {count}x {core_name}')
    if data.get('max_freq_ghz'):
        lines.append(_pad('Freq. maxima', f'{data['max_freq_ghz']:.2f} GHz'))
    if data.get('architecture'):
        bits = '64-bit' if data.get('is_64bit') else '32-bit'
        lines.append(_pad('Arquitetura', f'{data['architecture']} ({bits})'))
    if data.get('category'):
        lines.append(_pad('Categoria', data['category']))
    lines.append(_LINE)
    return '\n'.join(lines)
def format_identity(data):
    '''Formata resultado do parse_identity.'''
    if not data or not data.get('model'):
        return '  Informacao indisponivel neste dispositivo.'
    lines = [f'\n{_LINE}', '  DISPOSITIVO', _LINE]
    if data.get('brand') and data.get('model'):
        lines.append(_pad('Modelo', f'{data['brand']} {data['model']}'))
    if data.get('android_version'):
        lines.append(_pad('Android', data['android_version']))
    if data.get('security_patch'):
        lines.append(_pad('Patch seg.', data['security_patch']))
    if data.get('soc_name'):
        lines.append(_pad('Chipset', data['soc_name']))
    elif data.get('chipset_vendor'):
        platform = f' ({data['platform']})' if data.get('platform') else ''
        lines.append(_pad('Chipset', f'{data['chipset_vendor']}{platform}'))
    if data.get('build_id'):
        lines.append(_pad('Firmware', data['build_id']))
    if data.get('kernel'):
        kernel_short = data['kernel'].split()[0] if data['kernel'] else ''
        if kernel_short:
            lines.append(_pad('Kernel', kernel_short))
    if data.get('baseband'):
        lines.append(_pad('Baseband', data['baseband'][:30]))
    if data.get('bootloader_locked') is False:
        lines.append(_pad('Bootloader', 'DESBLOQUEADO'))
    else:
        lines.append(_pad('Bootloader', 'Travado'))
    lines.append(_LINE)
    return '\n'.join(lines)
def format_camera(data):
    '''Formata resultado do parse_camera ÔÇö formato profissional por grupo.'''
    if not data or data.get('total', 0) == 0:
        lines = [f'\n{_LINE}', '  CAMERAS', _LINE]
        lines.append('  Ô£û NENHUMA CAMERA DETECTADA')
        lines.append('')
        lines.append('    Possivel defeito: flex, conector ou modulo da camera')
        lines.append(_LINE)
        return '\n'.join(lines)
    lines = [f'\n{_LINE}', '  CAMERAS', _LINE]
    cameras = data.get('cameras', [])
    back_cams = [c for c in cameras if c.get('facing', '').lower() == 'back']
    front_cams = [c for c in cameras if c.get('facing', '').lower() == 'front']
    if back_cams:
        has_flash = any((c.get('flash') for c in back_cams))
        back_label = 'Camera traseira' if len(back_cams) == 1 else 'Cameras traseiras'
        lines.append(_pad(f'{back_label}', f'{len(back_cams)} detectada(s)'))
        lines.append(_pad('Flash', 'Presente' if has_flash else 'Ausente'))
    else:
        lines.append('  Ô£û Nenhuma camera traseira detectada')
    if front_cams:
        lines.append(_pad('Camera frontal', 'Detectada'))
    else:
        lines.append('  Ô£û Nenhuma camera frontal detectada')
    lines.append(f'\n  {'ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ'}')
    lines.append('  Resolucoes identificadas:')
    if back_cams:
        back_res = [f'{c['megapixels']} MP' for c in back_cams if c.get('megapixels')]
        if back_res:
            lines.append(f'    Traseira: {' | '.join(back_res)}')
    if front_cams:
        front_res = [f'{c['megapixels']} MP' for c in front_cams if c.get('megapixels')]
        if front_res:
            lines.append(f'    Frontal:  {' | '.join(front_res)}')
    if len(back_cams) < 4:
        lines.append(f'\n  {'ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ'}')
        lines.append('  Nota: cameras auxiliares (macro/profundidade)')
        lines.append('  podem nao ser listadas pelo sistema.')
    lines.append(_LINE)
    return '\n'.join(lines)
def format_partitions(data):
    '''Formata resultado do parse_partitions com layout tabular organizado.'''
    if not data or data.get('total', 0) == 0:
        return '  Informacao indisponivel neste dispositivo.'
    lines = [f'\n{_LINE}', '  MAPA DE PARTICOES', _LINE]
    lines.append(_pad('Total', str(data['total'])))
    if data.get('storage_type'):
        lines.append(_pad('Armazenamento', data['storage_type']))
    if data.get('ab_slot'):
        lines.append(_pad('Esquema', 'A/B (seamless update)'))
    else:
        lines.append(_pad('Esquema', 'Single slot'))
    lines.append(f'\n  {'ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ'}')
    lines.append(f'  {'PARTICAO':<22}{'FUNCAO'}')
    lines.append(f'  {'ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ'}')
    _CAT_ORDER = ['Boot', 'Sistema', 'Recovery', 'Modem/RF', 'Seguranca', 'Dados', 'NVRAM/Calibracao']
    sorted_parts = []
    for cat in _CAT_ORDER:
        cat_parts = data.get('categories', {}).get(cat, [])
        for p in sorted(cat_parts):
            sorted_parts.append((p, cat))
    uncategorized = sorted(data.get('uncategorized', []))
    for p in uncategorized:
        sorted_parts.append((p, 'Outro'))
    current_cat = None
    for name, cat in sorted_parts:
        if cat != current_cat:
            current_cat = cat
            lines.append('')
            lines.append(f'  [{cat}]')
        lines.append(f'    {name:<20} {_partition_hint(name, cat)}')
    lines.append(_LINE)
    return '\n'.join(lines)
def _partition_hint(name, cat):
    '''Retorna dica curta sobre a funcao da particao para o tecnico.'''
    _HINTS = {'boot': 'Kernel Android', 'init_boot': 'Kernel init (A13+)', 'vendor_boot': 'Kernel vendor', 'lk': 'Bootloader (LK)', 'lk2': 'Bootloader backup', 'bootloader1': 'Bootloader pri.', 'bootloader2': 'Bootloader bkp.', 'preloader': '1o estagio boot', 'tee': 'TrustZone (seguro)', 'tee1': 'TrustZone pri.', 'tee2': 'TrustZone bkp.', 'gz': 'ARM TrustZone', 'scp': 'Co-processador', 'sspm': 'Security subsys', 'mcupm': 'MCU power mgmt', 'xbl': 'Bootloader Qualcomm', 'abl': 'Android bootloader', 'hyp': 'Hypervisor', 'uboot': 'Bootloader UNISOC', 'uboot_log': 'Log do bootloader', 'spl': 'Secondary Loader', 'sml': 'Security Module', 'trustos': 'TrustZone UNISOC', 'teecfg': 'Config TrustZone', 'hypervsior': 'Hypervisor', 'hypervisor': 'Hypervisor', 'super': 'System+Vendor+Product', 'system': 'Sistema Android', 'vendor': 'Drivers fabricante', 'product': 'Apps fabricante', 'dtbo': 'Device tree overlay', 'dtb': 'Device tree blob', 'vbmeta': 'Verified Boot', 'vbmeta_system': 'VB sistema', 'vbmeta_vendor': 'VB vendor', 'vbmeta_odm': 'VB ODM', 'vbmeta_product': 'VB produto', 'vbmeta_system_ext': 'VB system ext', 'logo': 'Splash boot', 'fbootlogo': 'Logo fastboot', 'recovery': 'Modo recovery', 'modem': 'Firmware celular', 'md1img': 'Modem firmware', 'md1dsp': 'Modem DSP', 'dsp': 'Digital Signal Proc.', 'connsys_bt': 'Bluetooth FW', 'connsys_wifi': 'WiFi FW', 'connsys_gnss': 'GPS FW', 'bluetooth': 'Bluetooth FW', 'l_modem': 'Modem UNISOC', 'l_agdsp': 'Audio DSP', 'l_gdsp': 'General DSP', 'l_ldsp': 'Low-power DSP', 'userdata': 'Dados do usuario', 'metadata': 'Criptografia', 'misc': 'Config recovery', 'miscdata': 'Dados diversos', 'persist': 'Dados persistentes', 'protect': 'Dados protegidos', 'protect2': 'Dados protegidos 2', 'cache': 'Cache sistema', 'frp': 'Factory Reset Prot.', 'efuse': 'Fusivel hardware', 'otp': 'One-Time Program.', 'seccfg': 'Config seguranca', 'sec': 'Seguranca', 'nvram': 'Calibracao radio/BT', 'nvdata': 'Dados NV', 'nvcfg': 'Config NV', 'proinfo': 'Info producao', 'expdb': 'Exception DB', 'boot_para': 'Parametros boot', 'dram_para': 'Config memoria RAM', 'para': 'Parametros gerais', 'carrier': 'Config operadora', 'pi_img': 'Product info', 'odm': 'ODM customizacao', 'l_fixnv1': 'NV fixo 1 (IMEI)', 'l_fixnv2': 'NV fixo 2 (backup)', 'l_deltanv': 'NV delta (diffs)', 'l_runtimenv1': 'NV runtime 1', 'l_runtimenv2': 'NV runtime 2', 'prodnv': 'NV producao', 'calinv': 'NV calibracao', 'sysdumpdb': 'Crash dump DB', 'prodpersist': 'Dados fabrica', 'ocdt': 'Calibracao producao', 'pm_sys': 'Power management', 'blackbox': 'Log crash (OPPO)', 'oplusreserve1': 'Reservado fabricante', 'oplusreserve2': 'Reservado fabricante', 'oplusreserve3': 'Reservado fabricante', 'oplusreserve4': 'Reservado fabricante', 'oplusreserve5': 'Reservado fabricante', 'opporeserve': 'Reservado OPPO', 'my_preload': 'Apps pre-instalados', 'common_rs1': 'Rescue system 1', 'common_rs2': 'Rescue system 2', 'avbmeta_rs': 'VB rescue', 'efs': 'IMEI + calib. RF', 'sec_efs': 'Backup IMEI/RF', 'cpefs': 'EFS modem (CP)', 'radio': 'Firmware modem', 'cp_debug': 'Debug modem', 'persistent': 'FRP (Google Lock)', 'keydata': 'Chaves criptografia', 'keyrefuge': 'Backup chaves', 'keystorage': 'Armazen. chaves', 'fmp_selftest': 'Teste FMP', 'uh': 'Hypervisor Samsung', 'uhcfg': 'Config hypervisor', 'tzsw': 'TrustZone software', 'tzar': 'TrustZone AR', 'ldfw': 'Low-level firmware', 'blcmd': 'Bootloader command', 'bota': 'Boot OS update', 'optics': 'Calib. camera', 'prism': 'Config operadora', 'omr': 'OMR (regional)', 'param': 'Parametros sistema', 'up_param': 'Param. atualizacao', 'nad_refer': 'Diag. Samsung (NAD)', 'steady': 'Dados estabilidade', 'debug': 'Particao debug', 'reserved': 'Reservado sistema', 'reserved2': 'Reservado sistema 2', 'xbl_config': 'Config bootloader QC', 'btd': 'Boot-to-Download', 'uefivarstore': 'UEFI variables', 'apdp': 'App provisioning', 'splash': 'Tela splash boot', 'apnhlos': 'Firmware modem QC', 'bksecapp': 'Backup secure app', 'dip': 'Data Integrity Prot.', 'hdm': 'Hardware Device Mgr', 'spu': 'Secure Proc. Unit', 'spunvm': 'SPU NVM (Knox)', 'ssd': 'Secure SW Download', 'storsec': 'Storage Security', 'toolsfv': 'Tools firmware val.', 'tz_kg': 'TZ key generation', 'tziccc': 'TZ ICC cert', 'vk': 'Verification key', 'questdatafv': 'Quest test data', 'logdump': 'Log de crash', 'logfs': 'Log filesystem', 'rawdump': 'Raw crash dump', 'dqmdbg': 'QMI debug', 'pad': 'Padding', 'ddr': 'Treino DDR (RAM)', 'devinfo': 'Info dispositivo', 'dpo': 'Display Power Opt.', 'limits': 'Limites termicos', 'limits-cdsp': 'Limites CDSP'}
    hint = _HINTS.get(name)
    if hint:
        return hint
    _CAT_HINTS = {'Boot': 'Inicializacao', 'Sistema': 'Sistema', 'Recovery': 'Recuperacao', 'Modem/RF': 'Conectividade', 'Seguranca': 'Seguranca', 'Dados': 'Armazenamento', 'NVRAM/Calibracao': 'Calibracao', 'Outro': '--'}
    return _CAT_HINTS.get(cat, '--')
_PKG_FRIENDLY = {'com.facebook.katana': 'Facebook', 'com.facebook.orca': 'Messenger', 'com.facebook.lite': 'Facebook Lite', 'com.instagram.android': 'Instagram', 'com.whatsapp': 'WhatsApp', 'com.whatsapp.w4b': 'WhatsApp Business', 'com.google.android.youtube': 'YouTube', 'com.google.android.gm': 'Gmail', 'com.google.android.apps.maps': 'Google Maps', 'com.google.android.apps.photos': 'Google Fotos', 'com.spotify.music': 'Spotify', 'com.twitter.android': 'Twitter/X', 'com.zhiliaoapp.musically': 'TikTok', 'com.ss.android.ugc.trill': 'TikTok', 'com.tencent.mm': 'WeChat', 'com.snapchat.android': 'Snapchat', 'com.netflix.mediaclient': 'Netflix', 'com.amazon.mShop.android.shopping': 'Amazon', 'com.shopee.br': 'Shopee', 'com.mercadolibre': 'Mercado Livre', 'com.ubercab': 'Uber', 'com.ubercab.eats': 'Uber Eats', 'com.ifood.ifood': 'iFood', 'com.kwai.video': 'Kwai', 'com.samsung.android.game.gamehome': 'Game Launcher', 'com.miui.securitycenter': 'Seguranca MIUI'}
def _friendly_pkg_name(package_name):
    '''Retorna nome amigavel do pacote ou a parte final legivel.'''
    if package_name in _PKG_FRIENDLY:
        return _PKG_FRIENDLY[package_name]
    parts = package_name.split('.')
    if len(parts) >= 3:
        return parts[-1].replace('_', ' ').capitalize()
    return package_name
def format_network(data):
    '''Formata resultado do parse_network.'''
    if not data:
        return '  Informacao indisponivel neste dispositivo.'
    lines = [f'\n{_LINE}', '  ANALISE DE REDE', _LINE]
    active = data.get('active_network', 'Nenhuma')
    if active and active != 'Nenhuma':
        lines.append(_pad('Conexao', f'ONLINE via {active}'))
    else:
        lines.append(_pad('Conexao', 'OFFLINE (sem internet)'))
    lines.append('')
    wifi_ok = data.get('wifi_available')
    mobile_ok = data.get('mobile_available')
    wifi_icon = 'Ô£ö' if wifi_ok else 'Ô£û'
    mobile_icon = 'Ô£ö' if mobile_ok else 'Ô£û'
    if wifi_ok:
        wifi_status = 'Disponivel (pronto para uso)'
    else:
        wifi_status = 'Indisponivel'
    if mobile_ok:
        mobile_status = 'Disponivel (pronto para uso)'
    else:
        mobile_status = 'Indisponivel (sem chip ou desativado)'
    lines.append(f'  {wifi_icon} Wi-Fi......... {wifi_status}')
    lines.append(f'  {mobile_icon} Dados moveis.. {mobile_status}')
    blocked_count = data.get('blocked_apps', 0)
    if blocked_count > 0:
        lines.append('')
        lines.append(f'  Apps com rede bloqueada: {blocked_count}')
        blocked_names = data.get('blocked_names', [])
        if blocked_names:
            lines.append('')
            for name in blocked_names[:20]:
                friendly = _friendly_pkg_name(name)
                lines.append(f'    Ô£û {friendly}')
            if len(blocked_names) > 20:
                lines.append(f'    ... e mais {len(blocked_names) - 20}')
    lines.append(_LINE)
    return '\n'.join(lines)
def format_system_events(data):
    '''Formata resultado do parse_system_events.'''
    if not data:
        return '  Informacao indisponivel neste dispositivo.'
    lines = [f'\n{_LINE}', '  EVENTOS DO SISTEMA', _LINE]
    if data.get('uptime'):
        lines.append(_pad('Ligado ha', data['uptime']))
    if data.get('load_avg') is not None:
        load = data['load_avg']
        if load < 3:
            label = 'Normal'
        elif load < 6:
            label = 'Moderada'
        else:
            label = 'Alta'
        lines.append(_pad('Carga CPU', f'{load:.1f} ({label})'))
    lines.append(_pad('Erros recentes', str(data.get('total_errors', 0))))
    if data.get('crashes'):
        lines.append(_pad('  Crashes', str(data['crashes'])))
    if data.get('anrs'):
        lines.append(_pad('  ANRs', str(data['anrs'])))
    if data.get('network_errors'):
        lines.append(_pad('  Rede', str(data['network_errors'])))
    if data.get('permission_errors'):
        lines.append(_pad('  Permissao', str(data['permission_errors'])))
    if data.get('top_sources'):
        lines.append(f'\n  {'ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ'}')
        lines.append('  Fontes mais frequentes:')
        for tag, count in data['top_sources']:
            lines.append(f'    {tag} ({count}x)')
    if data.get('recent_errors'):
        lines.append(f'\n  {'ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ'}')
        lines.append('  Ultimos erros:')
        for err in data['recent_errors']:
            lines.append(f'    [{err['tag']}] {err['msg']}')
    lines.append(_LINE)
    return '\n'.join(lines)
def format_wifi(data):
    '''Formata resultado do parse_wifi.'''
    if not data:
        return '  Informacao indisponivel neste dispositivo.'
    lines = [f'\n{_LINE}', '  WI-FI', _LINE]
    if not data.get('enabled'):
        lines.append(_pad('Status', 'Desligado'))
        lines.append(_LINE)
        return '\n'.join(lines)
    if not data.get('connected'):
        lines.append(_pad('Status', 'Ligado (desconectado)'))
        lines.append(_LINE)
        return '\n'.join(lines)
    lines.append(_pad('Status', 'Conectado'))
    if data.get('ssid'):
        lines.append(_pad('Rede', data['ssid']))
    if data.get('rssi') is not None:
        bars = _bars_visual(5 if data['rssi'] >= -50 else 4 if data['rssi'] >= -60 else 3 if data['rssi'] >= -70 else 2 if data['rssi'] >= -80 else 1)
        lines.append(_pad('Sinal', f'{data['rssi']} dBm ({data.get('signal_label', '')}) {bars}'))
    if data.get('band'):
        lines.append(_pad('Banda', data['band']))
    if data.get('link_speed_mbps'):
        lines.append(_pad('Velocidade', f'{data['link_speed_mbps']} Mbps'))
    if data.get('wifi_standard'):
        lines.append(_pad('Padrao', data['wifi_standard']))
    if data.get('frequency_mhz'):
        lines.append(_pad('Frequencia', f'{data['frequency_mhz']} MHz'))
    lines.append(_LINE)
    return '\n'.join(lines)
def format_usb(data):
    '''Formata resultado do parse_usb.'''
    if not data or data.get('state') is None:
        return '  Informacao indisponivel neste dispositivo.'
    lines = [f'\n{_LINE}', '  USB', _LINE]
    lines.append(_pad('Estado', data['state']))
    if data.get('mode'):
        lines.append(_pad('Modo', data['mode']))
    if data.get('otg_supported'):
        lines.append(_pad('OTG', 'Suportado'))
    else:
        lines.append(_pad('OTG', 'Nao suportado'))
    lines.append(_LINE)
    return '\n'.join(lines)
def format_audio(data):
    '''Formata resultado do parse_audio para diagnostico de hardware de som.'''
    if not data:
        return '  Informacao indisponivel neste dispositivo.'
    lines = [f'\n{_LINE}', '  DIAGNOSTICO DE AUDIO', _LINE]
    lines.append(_pad('Modo', data.get('mode', 'Normal')))
    speaker_icon = 'Ô£ö' if data.get('speaker_ok') else 'Ô£û'
    earpiece_icon = 'Ô£ö' if data.get('earpiece_ok') else 'Ô£û'
    lines.append(f'\n  {'ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ'}')
    lines.append('  Saida de Audio:')
    lines.append(f'    {speaker_icon} Alto-falante (Speaker)')
    lines.append(f'    {earpiece_icon} Auricular (Earpiece)')
    if data.get('headset_connected'):
        lines.append('    Ô£ö Fone com fio conectado')
    if data.get('bluetooth_name'):
        lines.append(f'    Ô£ö Bluetooth: {data['bluetooth_name']}')
    if data.get('output_device'):
        lines.append(_pad('Saida ativa', data['output_device']))
    mic_count = data.get('mic_count', 0)
    lines.append(f'\n  {'ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ'}')
    lines.append('  Entrada de Audio:')
    if mic_count > 0:
        locs = data.get('mic_locations', [])
        loc_str = ' + '.join(locs) if locs else 'detectado(s)'
        lines.append(f'    Ô£ö Microfones: {mic_count} ({loc_str})')
    else:
        lines.append('    Ô£û Nenhum microfone detectado')
    if data.get('fm_tuner'):
        lines.append('    Ô£ö FM Tuner')
    lines.append(f'\n  {'ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ'}')
    vib_icon = 'Ô£ö' if data.get('has_vibrator') else 'Ô£û'
    lines.append(f'  {vib_icon} Vibrador {'funcional' if data.get('has_vibrator') else 'nao detectado'}')
    if data.get('mic_muted'):
        lines.append('\n  ÔÜá MICROFONE MUTADO POR SOFTWARE')
    if data.get('volume_music') is not None:
        lines.append(_pad('Volume midia', str(data['volume_music'])))
    lines.append(_LINE)
    return '\n'.join(lines)
