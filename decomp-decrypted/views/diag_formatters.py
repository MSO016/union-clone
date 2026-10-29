import logging
logger = logging.getLogger('DiagnosticoAndroid.formatters')
_SEP = '============================================================'
_SUBSEP = '----------------------------------------'
_SUBSEP_50 = '--------------------------------------------------'
_CPU_IMPLEMENTERS = {'0x41': 'ARM', '0x51': 'Qualcomm', '0x53': 'Samsung', '0x69': 'Intel', '0xc0': 'Ampere'}
_CPU_PARTS = {'0xd03': 'Cortex-A53', '0xd04': 'Cortex-A35', '0xd05': 'Cortex-A55', '0xd07': 'Cortex-A57', '0xd08': 'Cortex-A72', '0xd09': 'Cortex-A73', '0xd0a': 'Cortex-A75', '0xd0b': 'Cortex-A76', '0xd0c': 'Neoverse N1', '0xd0d': 'Cortex-A77', '0xd41': 'Cortex-A78', '0xd44': 'Cortex-X1', '0xd47': 'Cortex-A710', '0xd48': 'Cortex-X2', '0xd4b': 'Cortex-A78C', '0xd4d': 'Cortex-A715', '0xd4e': 'Cortex-X3'}
def format_device_info(device_info: dict) -> str:
    out = f'\n{_SEP}\n'
    out += '­ƒô▒ INFORMA├ç├òES DO DISPOSITIVO\n'
    out += f'{_SEP}\n\n'
    if 'model' in device_info and 'brand' in device_info:
        out += f'­ƒô▒ Dispositivo: {device_info.get('brand')} {device_info.get('model')}\n'
    if 'android' in device_info:
        out += f'­ƒñû Android: {device_info.get('android')}'
        if 'security' in device_info:
            out += f' (Patch {device_info.get('security')})\n'
        else:
            out += '\n'
    if 'imei' in device_info and device_info.get('imei') and device_info.get('imei') != '\\x00\\x00':
        out += f'­ƒô▓ IMEI: {device_info.get('imei')}\n'
    out += '\n--- HARDWARE ---\n'
    if 'chipset' in device_info:
        out += f'­ƒöº Chipset: {device_info.get('chipset')}\n'
    if 'board' in device_info:
        out += f'­ƒºá Placa: {device_info.get('board')}\n'
    if 'hardware' in device_info:
        out += f'ÔÜÖ´©Å Hardware: {device_info.get('hardware')}\n'
    if 'manufacturer' in device_info:
        out += f'­ƒÅ¡ Fabricante: {device_info.get('manufacturer')}\n'
    if 'kernel' in device_info:
        out += f'­ƒÆ╗ Kernel: {device_info.get('kernel')}\n'
    out += '\n--- SISTEMA ---\n'
    if 'build_id' in device_info:
        out += f'­ƒåö Build ID: {device_info.get('build_id')}\n'
    if 'build_type' in device_info:
        out += f'­ƒôè Build Type: {device_info.get('build_type')}\n'
    if 'build_fingerprint' in device_info:
        out += f'­ƒöæ Fingerprint: {device_info.get('build_fingerprint')}\n'
    if 'baseband' in device_info and device_info.get('baseband'):
        out += f'­ƒôí Baseband: {device_info.get('baseband')}\n'
    out += f'\n{_SEP}'
    return out
def _parse_size(size_str: str) -> float:
    if size_str.endswith('G'):
        return float(size_str[:-1]) * 1024
    if size_str.endswith('M'):
        return float(size_str[:-1])
    if size_str.endswith('K'):
        return float(size_str[:-1]) / 1024
    try:
        return float(size_str)
    except (ValueError, TypeError):
        return 0
def format_storage_info(raw_output: str) -> tuple:
    out = f'\n{_SEP}\n'
    out += '­ƒÆ¥ DIAGN├ôSTICO DE ARMAZENAMENTO\n'
    out += f'{_SEP}\n\n'
    lines = raw_output.strip().split('\n')
    storage_data = []
    data_partition = None
    system_partition = None
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 6:
            entry = {'device': parts[0], 'size': parts[1], 'used': parts[2], 'avail': parts[3], 'use_percent': parts[4], 'mount_point': parts[5], 'size_mb': _parse_size(parts[1]), 'used_mb': _parse_size(parts[2])}
            storage_data.append(entry)
            if entry['mount_point'] == '/data':
                data_partition = entry
            elif entry['mount_point'] == '/':
                system_partition = entry
    out += f'­ƒôè RESUMO GERAL\n{_SUBSEP}\n'
    free_storage_gb = 0
    if data_partition:
        user_storage_gb = data_partition['size_mb'] / 1024
        used_storage_gb = data_partition['used_mb'] / 1024
        free_storage_gb = (data_partition['size_mb'] - data_partition['used_mb']) / 1024
        out += f'­ƒô▒ Armazenamento do Usu├írio: {user_storage_gb:.1f} GB\n'
        out += f'   Ôö£ÔöÇÔöÇ Usado: {used_storage_gb:.1f} GB ({data_partition['use_percent']})\n'
        out += f'   ÔööÔöÇÔöÇ Livre: {free_storage_gb:.1f} GB\n\n'
    emmc_found = any(('/dev/block/mmcblk' in s['device'] for s in storage_data))
    ufs_found = any(('/dev/block/sda' in s['device'] for s in storage_data))
    storage_type = 'eMMC' if emmc_found else 'UFS' if ufs_found else 'Desconhecido'
    out += f'­ƒÆ¥ Tipo de Armazenamento: {storage_type}\n'
    if storage_data:
        fs_info = storage_data[0]['device'].split('/')[2] if len(storage_data[0]['device'].split('/')) > 2 else 'Desconhecido'
        out += f'­ƒôï Sistema de Arquivos: {fs_info}\n'
    out += f'\n­ƒôï PARTI├ç├òES CR├ìTICAS\n{_SUBSEP}\n'
    critical_mounts = ['/data', '/', '/system', '/vendor', '/product', '/system_ext']
    for mount in critical_mounts:
        partitions = [p for p in storage_data if p['mount_point'] == mount]
        if partitions:
            for p in partitions:
                status = 'Ô£à OK' if '100%' not in p['use_percent'] else 'ÔÜá´©Å CR├ìTICO'
                out += f'{status} {p['mount_point']}: {p['used']} / {p['size']} ({p['use_percent']})\n'
        elif mount == '/system':
            system_alternatives = [p for p in storage_data if '/system' in p['mount_point']]
            if system_alternatives:
                for p in system_alternatives:
                    status = 'Ô£à OK' if '100%' not in p['use_percent'] else 'ÔÜá´©Å CR├ìTICO'
                    out += f'{status} {p['mount_point']} (system): {p['used']} / {p['size']} ({p['use_percent']})\n'
            else:
                out += f'ÔØô {mount}: N├úo encontrado (pode estar em outra montagem)\n'
        else:
            out += f'ÔØô {mount}: N├úo encontrado\n'
    out += f'\n­ƒöì AN├üLISE DE PROBLEMAS\n{_SUBSEP}\n'
    full_partitions = [p for p in storage_data if '100%' in p['use_percent'] if p['mount_point'] not in ('/apex/',)]
    if full_partitions:
        out += 'ÔÜá´©Å ALERTA: Parti├º├Áes cr├¡ticas totalmente ocupadas:\n'
        for p in full_partitions[:5]:
            out += f'   - {p['mount_point']} ({p['size']})\n'
        if len(full_partitions) > 5:
            out += f'   - E outras {len(full_partitions) - 5} parti├º├Áes...\n'
    else:
        out += 'Ô£à Nenhuma parti├º├úo cr├¡tica totalmente ocupada\n'
    if data_partition and free_storage_gb < 1.0:
        out += f'ÔÜá´©Å ALERTA: Espa├ºo livre muito baixo ({free_storage_gb:.1f} GB)\n'
        out += '   Isso pode causar instabilidade no sistema\n'
    if data_partition and '90%' in data_partition['use_percent']:
        out += 'ÔÜá´©Å Armazenamento quase cheio: Pode causar lentid├úo e falhas no sistema\n'
    out += f'\n­ƒøá´©Å DIAGN├ôSTICO T├ëCNICO\n{_SUBSEP}\n'
    if emmc_found:
        out += '­ƒô▒ Dispositivo utiliza armazenamento eMMC\n'
    elif ufs_found:
        out += '­ƒô▒ Dispositivo utiliza armazenamento UFS (mais r├ípido)\n'
    out += '\n­ƒÆí RECOMENDA├ç├òES T├ëCNICAS:\n'
    if any(('100%' in p['use_percent'] for p in storage_data if p['mount_point'] in critical_mounts)):
        out += 'ÔÜá´©Å Sistema com parti├º├Áes cr├¡ticas cheias:\n'
        out += '   - Considere uma reinicializa├º├úo de f├íbrica\n'
        out += '   - Verifique problemas de corrup├º├úo no sistema de arquivos\n'
        out += '   - Em alguns casos, pode ser necess├írio reflashear o dispositivo\n'
    elif data_partition:
        try:
            pct = int(data_partition['use_percent'].strip('%'))
            if pct > 85:
                out += 'ÔÜá´©Å Armazenamento interno com alta ocupa├º├úo:\n'
                out += '   - Limpe o cache de aplicativos (Configura├º├Áes > Armazenamento)\n'
                out += '   - Verifique aplicativos que ocupam muito espa├ºo\n'
                out += '   - Sugira backup e remo├º├úo de arquivos n├úo essenciais\n'
            else:
                out += 'Ô£à Armazenamento em estado normal\n'
        except (ValueError, TypeError):
            out += 'Ô£à Armazenamento em estado normal\n'
    else:
        out += 'Ô£à Armazenamento em estado normal\n'
    if any(('/dev/block/dm-' in p['device'] for p in storage_data)):
        out += '\n­ƒöº Dispositivo utiliza mapeamento din├ómico (dm-verity)\n'
        out += '   - Em caso de problemas, considere verificar integridade do sistema\n'
    out += f'\n­ƒôÜ LEGENDA DOS S├ìMBOLOS\n{_SUBSEP}\n'
    out += '­ƒÆ¥ - Armazenamento/Diagn├│stico de armazenamento\n'
    out += '­ƒôè - Resumo geral/Estat├¡sticas\n'
    out += '­ƒô▒ - Dispositivo/Informa├º├Áes do dispositivo\n'
    out += '­ƒôï - Lista/Invent├írio de parti├º├Áes\n'
    out += 'Ô£à - Status OK/Sem problemas detectados\n'
    out += 'ÔÜá´©Å - Alerta/Problema detectado\n'
    out += 'ÔØô - Item n├úo encontrado/Informa├º├úo desconhecida\n'
    out += '­ƒöì - An├ílise detalhada/Diagn├│stico\n'
    out += '­ƒøá´©Å - Ferramentas/Diagn├│stico t├®cnico\n'
    out += '­ƒÆí - Recomenda├º├Áes/Dicas\n'
    out += '­ƒöº - Configura├º├úo do sistema/Informa├º├úo t├®cnica\n'
    out += f'\n{_SEP}'
    return out, data_partition
def _parse_cores(raw_output: str) -> list:
    lines = raw_output.strip().split('\n')
    cores = []
    current_core = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('processor'):
            if current_core:
                cores.append(current_core)
            current_core = {'id': line.split(':')[1].strip()}
        elif ':' in line:
            key, value = line.split(':', 1)
            current_core[key.strip()] = value.strip()
    if current_core:
        cores.append(current_core)
    return cores
def format_cpu_info(raw_output: str, additional_info: dict) -> str:
    out = f'\n{_SEP}\n'
    out += '­ƒºá DIAGN├ôSTICO DE CPU\n'
    out += f'{_SEP}\n\n'
    cores = _parse_cores(raw_output)
    if not cores:
        out += 'ÔØî N├úo foi poss├¡vel extrair informa├º├Áes da CPU.\n'
        out += raw_output
        out += f'\n{_SEP}'
        return out
    implementer = cores[0].get('CPU implementer', '')
    cpu_vendor = _CPU_IMPLEMENTERS.get(implementer, 'Desconhecido')
    soc_type = additional_info.get('soc', '')
    if 'mediatek' in soc_type.lower() or 'mt' in soc_type.lower():
        soc_vendor = 'MediaTek'
    elif 'exynos' in soc_type.lower() or 'samsung' in soc_type.lower():
        soc_vendor = 'Samsung Exynos'
    elif 'kirin' in soc_type.lower() or 'hi' in soc_type.lower():
        soc_vendor = 'HiSilicon Kirin'
    elif 'snapdragon' in soc_type.lower() or 'sm' in soc_type.lower() or implementer == '0x51':
        soc_vendor = 'Qualcomm Snapdragon'
    elif 'unisoc' in soc_type.lower() or 'sp' in soc_type.lower():
        soc_vendor = 'Unisoc'
    elif 'dimensity' in soc_type.lower():
        soc_vendor = 'MediaTek Dimensity'
    else:
        soc_vendor = f'{cpu_vendor} {soc_type}'
    architecture = cores[0].get('CPU architecture', '')
    is_64bit = architecture in ('8', '8.1', '8.2', '8.3', '8.4', '8.5', '9')
    core_types = {}
    for core in cores:
        part = core.get('CPU part', '')
        core_model = _CPU_PARTS.get(part, f'Desconhecido ({part})')
        core_types[core_model] = core_types.get(core_model, 0) + 1
    is_big_little = len(core_types) > 1
    features = cores[0].get('Features', '')
    security_features = []
    if 'aes' in features:
        security_features.append('AES')
    if 'sha1' in features or 'sha2' in features:
        security_features.append('SHA')
    if 'crc32' in features:
        security_features.append('CRC32')
    temp_value = 'N/A'
    try:
        temp = int(additional_info.get('thermal', '0'))
        if temp > 1000:
            temp_value = f'{temp / 1000:.1f}┬░C'
        elif temp > 0:
            temp_value = f'{temp / 10 if temp > 100 else temp:.1f}┬░C'
    except (ValueError, TypeError):
        pass
    freq_value = 'N/A'
    try:
        freq = int(additional_info.get('freq', '0'))
        if freq > 1000000:
            freq_value = f'{freq / 1000000:.2f} GHz'
        elif freq > 1000:
            freq_value = f'{freq / 1000:.0f} MHz'
        elif freq > 0:
            freq_value = f'{freq} KHz'
    except (ValueError, TypeError):
        pass
    perf_level = 'Entrada'
    if any(('X' in ct for ct in core_types.keys())):
        perf_level = 'Flagship'
    elif any(('A7' in ct for ct in core_types.keys())):
        if not any(('A55' in ct for ct in core_types.keys())):
            perf_level = 'Premium'
        elif len(cores) >= 8 and is_big_little:
            perf_level = 'Alto'
        elif len(cores) >= 6:
            perf_level = 'M├®dio'
    out += f'­ƒô▒ RESUMO DO PROCESSADOR\n{_SUBSEP}\n'
    out += f'ÔÜí Fabricante: {soc_vendor}\n'
    out += f'­ƒº« Arquitetura: ARMv{architecture} ({' 64-bit' if is_64bit else ' 32-bit'})\n'
    out += f'­ƒº® Total de n├║cleos: {len(cores)}\n'
    if is_big_little:
        out += 'ÔÜÖ´©Å Configura├º├úo: big.LITTLE ou similar\n'
    out += '­ƒöó Distribui├º├úo dos n├║cleos:\n'
    for core_type, count in core_types.items():
        out += f'   ÔööÔöÇÔöÇ {count}x {core_type}\n'
    if freq_value != 'N/A':
        out += f'ÔÅ▒´©Å Frequ├¬ncia atual: {freq_value}\n'
    if temp_value != 'N/A':
        out += f'­ƒîí´©Å Temperatura: {temp_value}\n'
    out += f'\n­ƒôè AN├üLISE DE DESEMPENHO\n{_SUBSEP}\n'
    out += f'­ƒÅå Categoria: {perf_level}\n'
    use_cases = {'Entrada': 'B├ísico (navega├º├úo, redes sociais, apps leves)', 'M├®dio': 'Intermedi├írio (apps gerais, jogos leves)', 'Alto': 'Avan├ºado (multitarefa, jogos, edi├º├úo de fotos)', 'Premium': 'Alta performance (jogos exigentes, edi├º├úo)', 'Flagship': 'Ultra performance (jogos intensos, edi├º├úo de v├¡deo)'}
    out += f'­ƒæì Uso recomendado: {use_cases.get(perf_level, 'Uso geral')}\n'
    if security_features:
        out += f'­ƒöÉ Recursos de seguran├ºa: {', '.join(security_features)}\n'
    out += f'\n­ƒöì AN├üLISE DE POSS├ìVEIS PROBLEMAS\n{_SUBSEP}\n'
    problems = []
    try:
        temp_num = float(temp_value.replace('┬░C', ''))
        if temp_num > 85:
            problems.append('ÔÜá´©Å Temperatura extremamente elevada - Risco de throttling severo e danos')
        elif temp_num > 75:
            problems.append('ÔÜá´©Å Temperatura muito alta - Performance comprometida por throttling')
        elif temp_num > 65:
            problems.append('ÔÜá´©Å Temperatura elevada - Poss├¡vel throttling e redu├º├úo de performance')
    except (ValueError, TypeError):
        pass
    if 'MediaTek' in soc_vendor:
        if any(('A55' in ct for ct in core_types.keys())):
            problems.append('Ôä╣´©Å Processadores MediaTek com n├║cleos A55 podem sofrer com aquecimento em carga elevada')
    elif 'HiSilicon' in soc_vendor:
        problems.append('Ôä╣´©Å Processadores HiSilicon podem ter limita├º├Áes de atualiza├º├Áes devido a restri├º├Áes comerciais')
    elif 'Exynos' in soc_vendor and len(cores) == 8:
        problems.append('Ôä╣´©Å Alguns SoCs Exynos podem apresentar problemas de otimiza├º├úo em jogos pesados')
    if any(('A53' in ct for ct in core_types.keys())):
        problems.append('Ôä╣´©Å Cores Cortex-A53 s├úo mais antigos e podem limitar a performance em apps modernos')
    if not problems:
        out += 'Ô£à Nenhum problema conhecido encontrado para este processador\n'
    else:
        for problem in problems:
            out += f'{problem}\n'
    out += f'\n­ƒøá´©Å DIAGN├ôSTICO T├ëCNICO\n{_SUBSEP}\n'
    out += '­ƒÆí RECOMENDA├ç├òES PARA T├ëCNICOS:\n'
    if 'MediaTek' in soc_vendor:
        out += 'ÔÇó Processadores MediaTek podem necessitar de:\n'
        out += '  - Verificar aquecimento (comum em alguns modelos)\n'
        out += '  - Checagem do SPD (Speed Performance Data)\n'
        out += '  - Em caso de lentid├úo, limpar cache e reiniciar o sistema\n'
        out += '  - Modelos espec├¡ficos podem se beneficiar de reflash da ROM\n'
    elif 'Snapdragon' in soc_vendor:
        out += 'ÔÇó Processadores Qualcomm Snapdragon geralmente s├úo est├íveis, mas:\n'
        out += '  - Verifique poss├¡vel throttling em condi├º├Áes de carga\n'
        out += '  - Em caso de reboot aleat├│rio, verifique atualiza├º├Áes de firmware\n'
        out += '  - Alguns modelos t├¬m vulnerabilidades que requerem patch de seguran├ºa\n'
    elif 'Exynos' in soc_vendor:
        out += 'ÔÇó Processadores Samsung Exynos podem apresentar:\n'
        out += '  - Aquecimento excessivo em modelos espec├¡ficos\n'
        out += '  - Consumo de bateria elevado em alguns casos\n'
        out += '  - Incompatibilidade com algumas aplica├º├Áes de benchmark\n'
    elif 'Kirin' in soc_vendor:
        out += 'ÔÇó Processadores HiSilicon Kirin podem apresentar:\n'
        out += '  - Limita├º├Áes de atualiza├º├Áes do sistema devido a restri├º├Áes\n'
        out += '  - Em modelos mais antigos, degrada├º├úo de performance ao longo do tempo\n'
    else:
        out += 'ÔÇó Recomenda├º├Áes gerais para este processador:\n'
        out += '  - Verifique a temperatura sob carga para poss├¡vel throttling\n'
        out += '  - Avalie a performance com benchmarks padr├úo\n'
        out += '  - Se houver problemas, verifique atualiza├º├Áes do sistema\n'
    out += f'\n­ƒöº PROCEDIMENTOS DE TESTE RECOMENDADOS\n{_SUBSEP}\n'
    out += '1. Teste de carga: Execute benchmark por 10-15 minutos e monitore temperatura\n'
    out += '2. Teste de estabilidade: Verifique se ocorrem reboots sob carga elevada\n'
    out += '3. Teste multi-core: Verifique se todos os n├║cleos est├úo ativos e funcionais\n'
    out += '4. Teste de RAM: Verifique se a mem├│ria ├® compat├¡vel com a CPU\n'
    out += f'\n­ƒôÜ LEGENDA DOS S├ìMBOLOS\n{_SUBSEP}\n'
    out += '­ƒºá - Informa├º├Áes da CPU/Processador\n'
    out += '­ƒô▒ - Dispositivo/Modelo\n'
    out += 'ÔÜí - Fabricante do SoC\n'
    out += '­ƒº« - Arquitetura/Estrutura\n'
    out += '­ƒº® - N├║cleos/Componentes\n'
    out += 'ÔÜÖ´©Å - Configura├º├úo t├®cnica\n'
    out += 'ÔÅ▒´©Å - Velocidade/Frequ├¬ncia\n'
    out += '­ƒîí´©Å - Temperatura\n'
    out += '­ƒôè - An├ílise de desempenho\n'
    out += '­ƒÅå - Categoria/N├¡vel\n'
    out += '­ƒæì - Recomenda├º├úo/Uso ideal\n'
    out += '­ƒöì - Diagn├│stico/An├ílise\n'
    out += 'ÔÜá´©Å - Alerta/Problema\n'
    out += 'Ôä╣´©Å - Informa├º├úo relevante\n'
    out += 'Ô£à - Status normal/OK\n'
    out += '­ƒøá´©Å - Informa├º├Áes t├®cnicas\n'
    out += '­ƒÆí - Dicas/Recomenda├º├Áes\n'
    out += '­ƒöº - Procedimentos/Testes\n'
    out += f'\n{_SEP}'
    return out
def format_partition_map(raw_output: str) -> str:
    out = f'\n{_SEP}\n'
    out += '­ƒùé´©Å MAPA DE PARTI├ç├òES DO DISPOSITIVO\n'
    out += f'{_SEP}\n\n'
    lines = raw_output.strip().split('\n')
    controller_path = ''
    partition_lines = []
    for line in lines:
        if line.startswith('PATH:'):
            controller_path = line[5:].strip()
        elif line.strip():
            partition_lines.append(line.strip())
    if controller_path:
        if 'ufs' in controller_path.lower():
            storage_type = 'UFS (Universal Flash Storage)'
        elif 'mmc' in controller_path.lower() or 'emmc' in controller_path.lower():
            storage_type = 'eMMC (Embedded MultiMediaCard)'
        elif 'sdhci' in controller_path.lower():
            storage_type = 'SD/eMMC (SDHCI)'
        else:
            storage_type = 'N├úo identificado'
        out += f'­ƒÆ¥ Tipo de armazenamento: {storage_type}\n'
        out += f'\n{_SUBSEP_50}\n'
    if partition_lines:
        if len(partition_lines) == 1 and 'total' in partition_lines[0].lower():
            pass
    out += 'ÔÜá´©Å N├úo foi poss├¡vel listar as parti├º├Áes deste aparelho.\n'
    out += '   Poss├¡veis motivos:\n'
    out += '   ÔÇó Modelo n├úo compat├¡vel com esta leitura\n'
    out += '   ÔÇó Aparelho com acesso restrito\n'
    out += f'­ƒôï PARTI├ç├òES ENCONTRADAS\n{_SUBSEP_50}\n'
    count = 0
    for line in partition_lines:
        if line.startswith('total'):
            continue
        parts = line.split()
        if len(parts) >= 2 and '->' in line:
            arrow_idx = parts.index('->')
            name = parts[arrow_idx - 1] if arrow_idx > 0 else '?'
            target = parts[arrow_idx + 1] if arrow_idx + 1 < len(parts) else '?'
            count += 1
            out += f'  {count:3d}. {name:<30s} ÔåÆ {target}\n'
        elif len(parts) >= 1:
            name = parts[-1]
            count += 1
            out += f'  {count:3d}. {name}\n'
    out += f'\n{_SUBSEP_50}\n'
    out += f'­ƒôè Total de parti├º├Áes: {count}\n'
    out += '\n­ƒÆí DICAS PARA O T├ëCNICO:\n'
    out += "   ÔÇó As parti├º├Áes 'boot', 'recovery' e 'system' s├úo cr├¡ticas\n"
    out += "   ÔÇó Parti├º├Áes 'userdata' cont├¬m dados do usu├írio\n"
    out += "   ÔÇó Parti├º├Áes 'modem'/'radio' controlam a rede celular\n"
    out += '   ÔÇó Nunca apague parti├º├Áes sem backup completo\n'
    out += f'\n{_SEP}'
    return out
