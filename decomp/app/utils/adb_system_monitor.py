'''
M├│dulo para monitoramento de sistema via ADB usando comando top
Compat├¡vel com Android 9+ e integrado ao sistema UNION
Desenvolvido seguindo as diretrizes RESTORECELL:
- Modularidade e coes├úo
- Tratamento de erros robusto
- Logging detalhado
- Monitoramento em tempo real
MELHORIAS IMPLEMENTADAS (Inspiradas no adware_advanced_detector.py):
- Comandos ADB mais robustos com m├║ltiplas tentativas
- Valida├º├úo de PIDs para evitar dados obsoletos
- Parsing melhorado para diferentes formatos de sa├¡da do top
- M├®todos alternativos usando /proc/stat, /proc/meminfo, ps
- C├ílculos corretos de CPU e RAM com fallbacks
- Tratamento de erros mais inteligente
'''
import subprocess
import re
import logging
import threading
import time
import os
from typing import (Dict, List, Optional, Tuple, Callable)
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import json
logger = logging.getLogger(__name__)
class MonitorType(Enum):
    '''Tipos de monitoramento dispon├¡veis'''
    CPU = 'cpu'
    RAM = 'memory'
    PROCESSES = 'processes'
    SYSTEM = 'system'
    ALL = 'all'
class AlertLevel(Enum):
    '''N├¡veis de alerta para monitoramento'''
    LOW = ('low', '[OK]')
    MEDIUM = ('medium', '[!]')
    HIGH = ('high', '[!!]')
    CRITICAL = ('critical', '[!!!]')
@dataclass
class ProcessInfo:
    '''Informa├º├Áes de processo obtidas via top'''
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_kb: int
    user: str
    priority: int
    nice: int
    virtual_memory: int
    resident_memory: int
    shared_memory: int
    state: str
    timestamp: datetime
@dataclass
class SystemInfo:
    '''Informa├º├Áes do sistema obtidas via top'''
    timestamp: datetime
    uptime: str
    load_average: Tuple[float, float, float]
    cpu_usage: Dict[str, float]
    memory_usage: Dict[str, int]
    processes_total: int
    processes_running: int
    processes_sleeping: int
    processes_stopped: int
    processes_zombie: int
@dataclass
class AlertInfo:
    '''Informa├º├Áes de alerta do sistema'''
    timestamp: datetime
    alert_type: str
    level: AlertLevel
    message: str
    value: float
    threshold: float
    process_info: Optional[ProcessInfo] = None
class ADBSystemMonitor:
    '''
    Monitor de sistema via ADB usando comando top
    Funcionalidades:
    - Monitoramento de CPU em tempo real
    - Monitoramento de RAM em tempo real
    - Listagem de processos com consumo
    - Hist├│rico de monitoramento
    - Sistema de alertas configur├ível
    - Exporta├º├úo de relat├│rios
    '''
    def __init__(self, adb_manager):
        '''
Inicializa o monitor de sistema
Args:
    adb_manager: Inst├óncia do ADBManager
'''
        self.adb_manager = adb_manager
        self.logger = logging.getLogger(__name__)
        self.is_monitoring = False
        self.monitor_thread = None
        self.monitor_lock = threading.Lock()
        self.update_interval = 2
        self.current_system_info = None
        self.current_processes = []
        self.system_history = []
        self.process_history = []
        self.alerts = []
        self.last_alerts = {}
        self.alert_callbacks = []
        self.alert_thresholds = {'cpu_high': 80.0, 'cpu_critical': 95.0, 'memory_high': 85.0, 'memory_critical': 95.0, 'process_cpu_high': 50.0, 'process_memory_high': 30.0}
        self.last_update = None
        self.last_error_logs = {}
        self.error_log_cooldown = 30
        self.app_names_cache = {}
        self.package_names_cache = {}
        self.logger.info('ADBSystemMonitor inicializado com configura├º├Áes otimizadas')
    def _should_log_error(self, error_msg: str) -> bool:
        '''
Verifica se devemos fazer log de um erro espec├¡fico para evitar spam
Args:
    error_msg: Mensagem de erro
Returns:
    bool: True se devemos fazer log
'''
        current_time = time.time()
        if 'no devices/emulators found' in error_msg.lower():
            last_log_time = self.last_error_logs.get('no_devices', 0)
            if current_time - last_log_time < self.error_log_cooldown:
                return False
            self.last_error_logs['no_devices'] = current_time
            return True
        return True
    def _execute_adb_command(self, command: List[str], timeout: int=10) -> str:
        """
Executa comando ADB usando abordagem consistente com ADBManager
Corrigido para evitar erro 'unknown command'
Args:
    command: Lista com comando ADB (sem o caminho do adb)
    timeout: Timeout em segundos
Returns:
    str: Sa├¡da do comando
Raises:
    Exception: Em caso de erro na execu├º├úo
"""
        try:
            if not self.adb_manager.adb_path:
                raise Exception('ADB n├úo est├í dispon├¡vel')
            if not os.path.isfile(self.adb_manager.adb_path):
                raise Exception('ADB n├úo encontrado. Verifique a instala├º├úo.')
            full_command = [self.adb_manager.adb_path] + command
            import platform
            if platform.system() == 'Windows':
                result = subprocess.run(full_command, capture_output=True, text=True, encoding='utf-8', errors='ignore', startupinfo=self.adb_manager.startupinfo, creationflags=self.adb_manager.creation_flags, timeout=timeout)
            else:
                result = subprocess.run(full_command, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=timeout)
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else 'Erro desconhecido'
                raise Exception(f'Comando ADB falhou: {error_msg}')
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise Exception(f'Timeout na execu├º├úo do comando ADB ({timeout}s)')
        except Exception as e:
            self.logger.error(f'Erro ao executar comando ADB {command}: {str(e)}')
            raise
    def _execute_adb_command_safe(self, command: List[str], timeout: int=10) -> str:
        '''
Vers├úo segura do comando ADB com m├║ltiplas tentativas
Usando m├®todo corrigido com verifica├º├úo de dispositivos
Args:
    command: Lista com comando ADB (sem o caminho do adb)
    timeout: Timeout em segundos
Returns:
    str: Sa├¡da do comando
Raises:
    Exception: Em caso de erro na execu├º├úo ou dispositivo n├úo conectado
'''
        try:
            if not self.adb_manager or not self.adb_manager.adb_path:
                raise Exception('ADB n├úo est├í dispon├¡vel')
            if not os.path.isfile(self.adb_manager.adb_path):
                raise Exception('ADB n├úo encontrado. Verifique a instala├º├úo.')
            if command and len(command) > 0 and command[0] == 'shell':
                try:
                    try:
                        device_connected = self.adb_manager.check_device()
                        if not device_connected:
                            raise Exception('Nenhum dispositivo Android conectado')
                    except Exception as e:
                        error_msg = str(e)
                        if self._should_log_error(error_msg):
                            self.logger.warning(f'Verifica├º├úo de dispositivo falhou: {error_msg}')
                        raise Exception(f'Erro ao verificar dispositivo: {error_msg}')
                except Exception as e:
                    error_msg = str(e)
                    if self._should_log_error(error_msg):
                        self.logger.error(f'Erro na verifica├º├úo inicial do comando {command}: {error_msg}')
                    raise
        except Exception as e:
            error_msg = str(e)
            if self._should_log_error(error_msg):
                self.logger.error(f'Erro na verifica├º├úo inicial do comando {command}: {error_msg}')
            raise
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                pass
            except Exception as e:
                error_msg = str(e)
                if 'no devices/emulators found' in error_msg:
                    if self._should_log_error(error_msg):
                        self.logger.warning(f'Dispositivo n├úo conectado para comando {command}')
                    raise Exception('Nenhum dispositivo Android conectado')
                if attempt == max_attempts - 1:
                    if self._should_log_error(error_msg):
                        self.logger.error(f'Falha final ap├│s {max_attempts} tentativas para comando {command}: {error_msg}')
                    raise
                if self._should_log_error(error_msg):
                    self.logger.warning(f'Tentativa {attempt + 1} falhou para comando {command}: {error_msg}')
                time.sleep(1)
                continue
            return self._execute_adb_command(command, timeout)
        raise Exception('Falha ap├│s m├║ltiplas tentativas')
    def _get_system_info_alternative(self) -> Optional[SystemInfo]:
        '''
        M├®todo alternativo para obter informa├º├Áes do sistema
        Inspirado no detector de adware com comandos mais confi├íveis
        '''
        try:
            commands_to_try = [['shell', 'cat', '/proc/stat'], ['shell', 'cat', '/proc/meminfo'], ['shell', 'cat', '/proc/loadavg'], ['shell', 'ps', '-A']]
            system_data = {}
            for cmd in commands_to_try:
                pass
            try:
                result = self._execute_adb_command_safe(cmd)
                if 'stat' in cmd:
                    system_data['cpu_raw'] = result
            except:
                pass
        except Exception as e:
            self.logger.error(f'Erro no m├®todo alternativo: {str(e)}')
        return self._parse_alternative_system_data(system_data)
    def _parse_alternative_system_data(self, data: Dict) -> Optional[SystemInfo]:
        '''
        Parse alternativo dos dados do sistema
        T├®cnica inspirada no detector de adware
        '''
        try:
            timestamp = datetime.now()
            cpu_usage = {}
            if 'cpu_raw' in data:
                cpu_lines = data['cpu_raw'].split('\n')
                for line in cpu_lines:
                    if not line.startswith('cpu '):
                        continue
                    parts = line.split()
                    if len(parts) >= 8:
                        user = int(parts[1])
                        nice = int(parts[2])
                        system = int(parts[3])
                        idle = int(parts[4])
                        iowait = int(parts[5])
                        irq = int(parts[6])
                        softirq = int(parts[7])
                        total = user + nice + system + idle + iowait + irq + softirq
                        if total > 0:
                            cpu_usage['user'] = round(user / total * 100, 2)
                            cpu_usage['system'] = round(system / total * 100, 2)
                            cpu_usage['idle'] = round(idle / total * 100, 2)
                            cpu_usage['wait'] = round(iowait / total * 100, 2)
                    break
            memory_usage = {}
            if 'memory_raw' in data:
                mem_lines = data['memory_raw'].split('\n')
                for line in mem_lines:
                    if line.startswith('MemTotal:'):
                        memory_usage['total'] = int(line.split()[1])
                        continue
                    if line.startswith('MemFree:'):
                        memory_usage['free'] = int(line.split()[1])
                        continue
                    if line.startswith('MemAvailable:'):
                        memory_usage['available'] = int(line.split()[1])
                        continue
                    if line.startswith('Buffers:'):
                        memory_usage['buffers'] = int(line.split()[1])
                        continue
                    if not line.startswith('Cached:'):
                        continue
                    memory_usage['cached'] = int(line.split()[1])
                    continue
            if 'total' in memory_usage and 'available' in memory_usage:
                memory_usage['used'] = memory_usage['total'] - memory_usage['available']
                memory_usage['used_percent'] = memory_usage['used'] / memory_usage['total'] * 100
            load_average = (0.0, 0.0, 0.0)
            if 'load_raw' in data:
                load_parts = data['load_raw'].strip().split()
                if len(load_parts) >= 3:
                    pass
            try:
                load_average = float(load_parts[0]), float(load_parts[1]), float(load_parts[2])
            except:
                pass
            else:
                processes_total = 0
                processes_running = 0
                processes_sleeping = 0
                processes_stopped = 0
                processes_zombie = 0
                if 'processes_raw' in data:
                    proc_lines = data['processes_raw'].split('\n')[1:]
                    for line in proc_lines:
                        if line.strip():
                            processes_total += 1
                            if ' R ' in line:
                                processes_running += 1
                            elif ' S ' in line:
                                processes_sleeping += 1
                            elif ' T ' in line:
                                processes_stopped += 1
                            elif ' Z ' in line:
                                processes_zombie += 1
        except Exception as e:
            self.logger.error(f'Erro no parse alternativo: {str(e)}')
        return SystemInfo(timestamp=timestamp, uptime='M├®todo alternativo', load_average=load_average, cpu_usage=cpu_usage, memory_usage=memory_usage, processes_total=processes_total, processes_running=processes_running, processes_sleeping=processes_sleeping, processes_stopped=processes_stopped, processes_zombie=processes_zombie)
    def get_system_info(self) -> Optional[SystemInfo]:
        '''
Obt├®m informa├º├Áes do sistema usando m├║ltiplos m├®todos
M├®todo melhorado com fallback para maior compatibilidade
Returns:
    Optional[SystemInfo]: Informa├º├Áes do sistema ou None em caso de erro
'''
        try:
            output = self._execute_adb_command_safe(['shell', 'top', '-n', '1', '-b'])
            result = self._parse_top_output(output)
            if result:
                return result
            self.logger.warning('M├®todo top falhou, tentando m├®todo alternativo')
        except Exception as e:
            self.logger.error(f'Erro ao obter informa├º├Áes do sistema: {str(e)}')
            try:
                pass
            except Exception as e2:
                self.logger.error(f'M├®todo alternativo tamb├®m falhou: {str(e2)}')
                e = None
                del e
                return
        return self._get_system_info_alternative()
    def get_processes(self, limit: int=20, sort_by: str='cpu') -> List[ProcessInfo]:
        '''
Obt├®m lista de processos com informa├º├Áes de recursos
M├®todo melhorado com m├║ltiplas tentativas e valida├º├úo de PIDs
Args:
    limit: N├║mero m├íximo de processos a retornar
    sort_by: Crit├®rio de ordena├º├úo ("cpu", "memory", "pid")
Returns:
    List[ProcessInfo]: Lista de processos validados
'''
        try:
            processes = self._get_processes_from_top(limit, sort_by)
            valid_processes = self._validate_process_pids(processes)
            if valid_processes:
                return valid_processes
            self.logger.warning('M├®todo top para processos falhou, tentando m├®todo alternativo')
        except Exception as e:
            self.logger.error(f'Erro ao obter processos: {str(e)}')
            try:
                pass
            except Exception as e2:
                self.logger.error(f'M├®todo alternativo de processos tamb├®m falhou: {str(e2)}')
                e = None
                del e
                return []
        return self._get_processes_alternative(limit, sort_by)
    def _get_processes_from_top(self, limit: int, sort_by: str) -> List[ProcessInfo]:
        '''
        Obt├®m processos usando comando top
        '''
        output = self._execute_adb_command_safe(['shell', 'top', '-n', '1', '-b'])
        processes = self._parse_processes_from_top(output)
        if sort_by == 'cpu':
            processes.sort(key=(lambda p: p.cpu_percent), reverse=True)
        elif sort_by == 'memory':
            processes.sort(key=(lambda p: p.memory_percent), reverse=True)
        elif sort_by == 'pid':
            processes.sort(key=(lambda p: p.pid))
        return processes[:limit]
    def _get_processes_alternative(self, limit: int, sort_by: str) -> List[ProcessInfo]:
        '''
        M├®todo alternativo para obter processos usando ps
        Inspirado no detector de adware
        '''
        try:
            ps_commands = [['shell', 'ps', '-A', '-o', 'pid,ppid,user,comm,pcpu,pmem,stat'], ['shell', 'ps', '-A'], ['shell', 'ps']]
            processes = []
            for cmd in ps_commands:
                pass
            try:
                output = self._execute_adb_command_safe(cmd)
                processes = self._parse_ps_output(output)
                if processes:
                    pass
            except:
                pass
            else:
                if sort_by == 'cpu':
                    processes.sort(key=(lambda p: p.cpu_percent), reverse=True)
                elif sort_by == 'memory':
                    processes.sort(key=(lambda p: p.memory_percent), reverse=True)
                elif sort_by == 'pid':
                    processes.sort(key=(lambda p: p.pid))
        except Exception as e:
            self.logger.error(f'Erro no m├®todo alternativo de processos: {str(e)}')
            return []
        return processes[:limit]
    def _parse_ps_output(self, output: str) -> List[ProcessInfo]:
        '''
        Parse da sa├¡da do comando ps
        T├®cnica inspirada no detector de adware
        '''
        processes = []
        lines = output.strip().split('\n')
        if lines:
            if 'PID' in lines[0] or 'USER' in lines[0]:
                lines = lines[1:]
        for line in lines:
            if not line.strip():
                continue
            try:
                parts = line.split()
                if len(parts) >= 4:
                    pid = int(parts[0])
                    user = parts[1] if len(parts) > 1 else 'unknown'
                    if len(parts) >= 8:
                        name = parts[7]
                    elif len(parts) >= 4:
                        name = parts[3]
                    else:
                        name = 'unknown'
                    cpu_percent = 0.0
                    memory_percent = 0.0
                    memory_kb = 0
                    if len(parts) >= 6:
                        pass
                try:
                    cpu_percent = float(parts[4])
                    memory_percent = float(parts[5])
                except:
                    pass
                else:
                    state = 'S'
                    if len(parts) >= 7:
                        state = parts[6]
                    process = ProcessInfo(pid=pid, name=name, cpu_percent=cpu_percent, memory_percent=memory_percent, memory_kb=memory_kb, user=user, priority=0, nice=0, virtual_memory=0, resident_memory=0, shared_memory=0, state=state, timestamp=datetime.now())
                    processes.append(process)
            except (ValueError, IndexError) as e:
                self.logger.debug(f'Erro ao processar linha: {line} - {str(e)}')
        return processes
    def _validate_process_pids(self, processes: List[ProcessInfo]) -> List[ProcessInfo]:
        '''
Valida se os PIDs dos processos ainda existem no sistema
Vers├úo otimizada para reduzir logs de debug
Args:
    processes: Lista de processos para validar
Returns:
    List[ProcessInfo]: Lista de processos v├ílidos
'''
        if not processes:
            return []
        valid_processes = []
        removed_count = 0
        try:
            pass
        except Exception as e:
            self.logger.error(f'Erro ao validar PIDs: {str(e)}')
            return processes
        try:
            pids_to_check = [p.pid for p in processes]
            ps_output = self._execute_adb_command_safe(['shell', 'ps', '-A', '-o', 'pid'])
            if ps_output:
                existing_pids = set()
                for line in ps_output.split('\n'):
                    line = line.strip()
                    if line.isdigit():
                        existing_pids.add(int(line))
                for process in processes:
                    if process.pid in existing_pids:
                        valid_processes.append(process)
                    else:
                        removed_count += 1
            else:
                for process in processes:
                    if self._validate_single_pid_quiet(process.pid):
                        valid_processes.append(process)
                    else:
                        removed_count += 1
            if removed_count > 0:
                self.logger.info(f'Removidos {removed_count} processos com PIDs obsoletos')
        except Exception as e:
            self.logger.error(f'Erro ao validar PIDs: {str(e)}')
            return processes
        return valid_processes
    def _validate_single_pid_quiet(self, pid: int) -> bool:
        '''
Valida PID individual sem logs de debug para melhor performance
Args:
    pid: PID para validar
Returns:
    bool: True se PID existe
'''
        try:
            result = self._execute_adb_command_safe(['shell', 'test', '-d', f'/proc/{pid}', '&&', 'echo', '1'])
            return '1' in result
        except:
            return False
    def _parse_top_output(self, output: str) -> Optional[SystemInfo]:
        '''
Analisa a sa├¡da do comando top com parsing mais robusto
Vers├úo melhorada com corre├º├úo de CPU > 100%
Args:
    output: Sa├¡da do comando top
Returns:
    Optional[SystemInfo]: Informa├º├Áes do sistema parseadas
'''
        try:
            lines = output.strip().split('\n')
            uptime = 'Desconhecido'
            load_average = (0.0, 0.0, 0.0)
            cpu_usage = {'user': 0.0, 'system': 0.0, 'idle': 100.0, 'wait': 0.0}
            memory_usage = {'total': 0, 'used': 0, 'free': 0, 'buffers': 0, 'cached': 0}
            process_summary = {'total': 0, 'running': 0, 'sleeping': 0, 'stopped': 0, 'zombie': 0}
            for line in lines:
                line = line.strip()
                if 'cpu' in line.lower() and '%' in line:
                    patterns = ['(\\d+(?:\\.\\d+)?)%us.*?(\\d+(?:\\.\\d+)?)%sy.*?(\\d+(?:\\.\\d+)?)%ni.*?(\\d+(?:\\.\\d+)?)%id.*?(\\d+(?:\\.\\d+)?)%wa', '(\\d+(?:\\.\\d+)?)%\\s*user.*?(\\d+(?:\\.\\d+)?)%\\s*system.*?(\\d+(?:\\.\\d+)?)%\\s*idle', 'User\\s*(\\d+(?:\\.\\d+)?)%.*?System\\s*(\\d+(?:\\.\\d+)?)%.*?IOW\\s*(\\d+(?:\\.\\d+)?)%.*?IRQ\\s*(\\d+(?:\\.\\d+)?)%']
                    for pattern in patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if not match:
                            continue
                        values = [float(x) for x in match.groups()]
                        total_cpu = sum(values)
                        if total_cpu > 100:
                            factor = 100.0 / total_cpu
                            values = [v * factor for v in values]
                        if len(values) >= 3:
                            cpu_usage = {'user': values[0], 'system': values[1], 'idle': values[2] if len(values) > 2 else 100.0 - values[0] - values[1], 'wait': values[4] if len(values) > 4 else 0.0}
                            active_cpu = cpu_usage['user'] + cpu_usage['system'] + cpu_usage['wait']
                            if active_cpu > 100:
                                active_cpu = 100
                            cpu_usage['idle'] = 100.0 - active_cpu
                        break
                    continue
                if 'mem' in line.lower():
                    if 'k' not in line.lower():
                        if 'kb' in line.lower() or 'mb' in line.lower():
                            numbers = re.findall('(\\d+(?:\\.\\d+)?)\\s*([kmgKMG]?[bB]?)', line)
                            if numbers:
                                mem_values = []
                                for num, unit in numbers:
                                    value = float(num)
                                    if unit.lower().startswith('m'):
                                        value *= 1024
                                    elif unit.lower().startswith('g'):
                                        value *= 1048576
                                    mem_values.append(int(value))
                                if len(mem_values) >= 3:
                                    memory_usage = {'total': mem_values[0], 'used': mem_values[1], 'free': mem_values[2], 'buffers': mem_values[3] if len(mem_values) > 3 else 0, 'cached': mem_values[4] if len(mem_values) > 4 else 0}
                                    continue
                if 'task' in line.lower() or 'process' in line.lower():
                    numbers = re.findall('(\\d+)', line)
                    if numbers:
                        process_summary['total'] = int(numbers[0])
                        if 'running' in line.lower():
                            running_match = re.search('(\\d+)\\s*running', line, re.IGNORECASE)
                            if running_match:
                                process_summary['running'] = int(running_match.group(1))
                        if 'sleeping' in line.lower():
                            sleeping_match = re.search('(\\d+)\\s*sleeping', line, re.IGNORECASE)
                            if sleeping_match:
                                process_summary['sleeping'] = int(sleeping_match.group(1))
                        if 'stopped' in line.lower():
                            stopped_match = re.search('(\\d+)\\s*stopped', line, re.IGNORECASE)
                            if stopped_match:
                                process_summary['stopped'] = int(stopped_match.group(1))
                        if 'zombie' in line.lower():
                            zombie_match = re.search('(\\d+)\\s*zombie', line, re.IGNORECASE)
                            if zombie_match:
                                process_summary['zombie'] = int(zombie_match.group(1))
                                continue
                if 'load average' in line.lower():
                    load_match = re.search('load average:\\s*(\\d+(?:\\.\\d+)?),?\\s*(\\d+(?:\\.\\d+)?),?\\s*(\\d+(?:\\.\\d+)?)', line, re.IGNORECASE)
                    if load_match:
                        load_average = float(load_match.group(1)), float(load_match.group(2)), float(load_match.group(3))
                        continue
                else:
                    if 'up' not in line.lower():
                        continue
                    if 'day' not in line.lower() and 'min' not in line.lower() and ':' not in line:
                        continue
                    uptime = line.strip()
                    continue
        except Exception as e:
            self.logger.error(f'Erro ao analisar sa├¡da do top: {str(e)}')
        if cpu_usage['user'] + cpu_usage['system'] + cpu_usage['idle'] + cpu_usage['wait'] > 105:
            active = cpu_usage['user'] + cpu_usage['system'] + cpu_usage['wait']
            if active > 100:
                factor = 100.0 / active
                cpu_usage['user'] *= factor
                cpu_usage['system'] *= factor
                cpu_usage['wait'] *= factor
                active = cpu_usage['user'] + cpu_usage['system'] + cpu_usage['wait']
            cpu_usage['idle'] = 100.0 - active
        cpu_usage['total_used'] = cpu_usage['user'] + cpu_usage['system'] + cpu_usage['wait']
        if cpu_usage['total_used'] > 100:
            cpu_usage['total_used'] = 100.0
        cpu_usage['idle'] = 100.0 - cpu_usage['total_used']
        if memory_usage['total'] > 0:
            if 'used_percent' not in memory_usage:
                memory_usage['used_percent'] = memory_usage['used'] / memory_usage['total'] * 100
            if memory_usage['used_percent'] > 100:
                memory_usage['used_percent'] = 100.0
        else:
            memory_usage['used_percent'] = 0.0
        return SystemInfo(timestamp=datetime.now(), uptime=uptime, load_average=load_average, cpu_usage=cpu_usage, memory_usage=memory_usage, processes_total=process_summary['total'], processes_running=process_summary['running'], processes_sleeping=process_summary['sleeping'], processes_stopped=process_summary['stopped'], processes_zombie=process_summary['zombie'])
    def _parse_processes_from_top(self, output: str) -> List[ProcessInfo]:
        '''
Extrai informa├º├Áes dos processos da sa├¡da do top
Args:
    output: Sa├¡da do comando top
Returns:
    List[ProcessInfo]: Lista de processos
'''
        processes = []
        try:
            lines = output.strip().split('\n')
            header_found = False
            for i, line in enumerate(lines):
                if 'PID' not in line:
                    continue
                if 'USER' not in line:
                    continue
                if not '%CPU' in line:
                    continue
                header_found = True
                for j in range(i + 1, len(lines)):
                    process_line = lines[j].strip()
                    if process_line:
                        process_info = self._parse_process_line(process_line)
                        if process_info:
                            processes.append(process_info)
                break
            if not header_found:
                for line in lines:
                    if re.match('^\\s*\\d+\\s+', line):
                        process_info = self._parse_process_line(line)
                        if process_info:
                            processes.append(process_info)
        except Exception as e:
            self.logger.error(f'Erro ao parsear processos do top: {str(e)}')
        return processes
    def _parse_process_line(self, line: str) -> Optional[ProcessInfo]:
        '''
Parseia uma linha de processo do top com valida├º├úo rigorosa
Vers├úo corrigida para evitar valores incorretos de CPU
Args:
    line: Linha do processo
Returns:
    Optional[ProcessInfo]: Informa├º├Áes do processo ou None se falhou
'''
        try:
            parts = line.strip().split()
            if len(parts) < 8:
                return
            pid = int(parts[0])
            user = parts[1]
            priority = 0
            nice = 0
            try:
                priority = int(parts[2]) if parts[2].isdigit() or parts[2].lstrip('-').isdigit() else 0
                nice = int(parts[3]) if parts[3].isdigit() or parts[3].lstrip('-').isdigit() else 0
            except (ValueError, IndexError):
                pass
            else:
                virtual_memory = self._parse_memory_value(parts[4]) if len(parts) > 4 else 0
                resident_memory = self._parse_memory_value(parts[5]) if len(parts) > 5 else 0
                shared_memory = self._parse_memory_value(parts[6]) if len(parts) > 6 else 0
                state = parts[7] if len(parts) > 7 else 'S'
                cpu_percent = 0.0
                if len(parts) > 8:
                    cpu_str = parts[8]
                    if self._is_float(cpu_str):
                        cpu_percent = float(cpu_str)
                        if cpu_percent < 0:
                            cpu_percent = 0.0
                        elif cpu_percent > 100:
                            cpu_percent = min(cpu_percent, 400.0)
                memory_percent = 0.0
                if len(parts) > 9:
                    mem_str = parts[9]
                    if self._is_float(mem_str):
                        memory_percent = float(mem_str)
                        if memory_percent < 0:
                            memory_percent = 0.0
                        elif memory_percent > 100:
                            memory_percent = 100.0
                name = 'unknown'
                if len(parts) > 10:
                    name = parts[-1]
                    if len(name) < 2 and len(parts) > 11:
                        name_parts = parts[11:]
                        if name_parts:
                            name = ' '.join(name_parts)
                    if len(name) > 50:
                        name = name[:50] + '...'
                if not name or name == 'unknown':
                    name = f'PID_{pid}'
                memory_kb = resident_memory
                if cpu_percent > 200:
                    self.logger.debug(f'CPU muito alta para processo {name} (PID {pid}): {cpu_percent}%')
                    cpu_percent = min(cpu_percent, 200.0)
        except Exception as e:
            self.logger.debug(f"Erro ao parsear linha de processo '{line}': {str(e)}")
        return ProcessInfo(pid=pid, name=name, cpu_percent=cpu_percent, memory_percent=memory_percent, memory_kb=memory_kb, user=user, priority=priority, nice=nice, virtual_memory=virtual_memory, resident_memory=resident_memory, shared_memory=shared_memory, state=state, timestamp=datetime.now())
    def _extract_percentage(self, text: str) -> float:
        '''
Extrai porcentagem de uma string com valida├º├úo melhorada
Args:
    text: Texto contendo porcentagem
Returns:
    float: Valor da porcentagem (0.0 - 100.0)
'''
        try:
            match = re.search('([\\d.]+)%', text)
            if match:
                value = float(match.group(1))
                return max(0.0, min(100.0, value))
        except Exception:
            pass
        return 0.0
    def _parse_memory_value(self, value: str) -> int:
        '''
Parseia valores de mem├│ria (pode ter sufixos como K, M, G)
Args:
    value: Valor de mem├│ria
Returns:
    int: Valor em KB
'''
        try:
            if not value or value == '0':
                return 0
            value = value.strip().lower()
            match = re.match('([\\d.]+)([kmgt]?)', value)
            if not match:
                if value.isdigit():
                    return int(value)
                return 0
            num = float(match.group(1))
            suffix = match.group(2)
            if suffix == 'k':
                return int(num)
            if suffix == 'm':
                return int(num * 1024)
            if suffix == 'g':
                return int(num * 1024 * 1024)
            if suffix == 't':
                return int(num * 1024 * 1024 * 1024)
            return int(num)
        except Exception:
            return 0
    def _is_float(self, value: str) -> bool:
        '''
Verifica se uma string pode ser convertida para float
Args:
    value: String a ser verificada
Returns:
    bool: True se pode ser convertida
'''
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    def start_monitoring(self, callback: Optional[Callable]=None) -> bool:
        '''
Inicia o monitoramento em tempo real
Args:
    callback: Fun├º├úo a ser chamada a cada atualiza├º├úo
Returns:
    bool: True se iniciado com sucesso
'''
        try:
            with self.monitor_lock:
                if self.is_monitoring:
                    self.logger.warning('Monitoramento j├í est├í ativo')
                    return False
                self.is_monitoring = True
                self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(callback,), daemon=True)
                self.monitor_thread.start()
                self.logger.info('Monitoramento iniciado')
        except Exception as e:
            self.logger.error(f'Erro ao iniciar monitoramento: {str(e)}')
            return False
        return True
    def stop_monitoring(self) -> bool:
        '''
Para o monitoramento em tempo real
Returns:
    bool: True se parado com sucesso
'''
        try:
            with self.monitor_lock:
                if not self.is_monitoring:
                    self.logger.warning('Monitoramento n├úo est├í ativo')
                    return False
                self.is_monitoring = False
                if self.monitor_thread and self.monitor_thread.is_alive():
                    self.monitor_thread.join(timeout=5)
        except Exception as e:
            self.logger.error(f'Erro ao parar monitoramento: {str(e)}')
            return False
        try:
            try:
                if hasattr(self.adb_manager, 'finalize_adb_operation'):
                    self.adb_manager.finalize_adb_operation()
            except:
                pass
        finally:
            pass
        self.logger.info('Monitoramento parado')
        try:
            return True
        except Exception as e:
            self.logger.error(f'Erro ao parar monitoramento: {str(e)}')
            return False
    def _monitor_loop(self, callback: Optional[Callable]=None):
        '''
Loop principal do monitoramento
Args:
    callback: Fun├º├úo a ser chamada a cada atualiza├º├úo
'''
        self.logger.info('Loop de monitoramento iniciado')
        while self.is_monitoring:
            try:
                system_info = self.get_system_info()
                if system_info:
                    self.current_system_info = system_info
                    self.system_history.append(system_info)
                    self._check_alerts(system_info)
                processes = self.get_processes(limit=10)
                if processes:
                    self.current_processes = processes
                    self.process_history.append(processes)
                    self._check_process_alerts(processes)
                self.last_update = datetime.now()
                if callback:
                    pass
                try:
                    callback(system_info, processes)
                except Exception as e:
                    self.logger.error(f'Erro no callback: {str(e)}')
                else:
                    time.sleep(self.update_interval)
            except Exception as e:
                self.logger.error(f'Erro no loop de monitoramento: {str(e)}')
                time.sleep(self.update_interval)
        self.logger.info('Loop de monitoramento finalizado')
    def _check_alerts(self, system_info: SystemInfo):
        '''
Verifica alertas do sistema
Args:
    system_info: Informa├º├Áes do sistema
'''
        try:
            if 'total_used' in system_info.cpu_usage:
                cpu_usage = system_info.cpu_usage['total_used']
                if cpu_usage >= self.alert_thresholds['cpu_critical']:
                    self._create_alert('cpu_critical', AlertLevel.CRITICAL, f'CPU cr├¡tico: {cpu_usage:.1f}%', cpu_usage, self.alert_thresholds['cpu_critical'])
                elif cpu_usage >= self.alert_thresholds['cpu_high']:
                    self._create_alert('cpu_high', AlertLevel.HIGH, f'CPU alto: {cpu_usage:.1f}%', cpu_usage, self.alert_thresholds['cpu_high'])
            if 'used_percent' in system_info.memory_usage:
                memory_usage = system_info.memory_usage['used_percent']
                if memory_usage >= self.alert_thresholds['memory_critical']:
                    self._create_alert('memory_critical', AlertLevel.CRITICAL, f'Mem├│ria cr├¡tica: {memory_usage:.1f}%', memory_usage, self.alert_thresholds['memory_critical'])
                    return
                if memory_usage >= self.alert_thresholds['memory_high']:
                    self._create_alert('memory_high', AlertLevel.HIGH, f'Mem├│ria alta: {memory_usage:.1f}%', memory_usage, self.alert_thresholds['memory_high'])
                    return
                return
        except Exception as e:
            self.logger.error(f'Erro ao verificar alertas: {str(e)}')
    def _check_process_alerts(self, processes: List[ProcessInfo]):
        '''
Verifica alertas de processos - vers├úo otimizada com menos logs
Args:
    processes: Lista de processos
'''
        try:
            high_cpu_processes = []
            high_memory_processes = []
            for process in processes:
                if process.cpu_percent >= 50:
                    high_cpu_processes.append(process)
                if process.memory_percent >= 30:
                    high_memory_processes.append(process)
            if high_cpu_processes:
                high_cpu_processes.sort(key=(lambda p: p.cpu_percent), reverse=True)
                for process in high_cpu_processes[:3]:
                    self._create_alert(f'process_cpu_{process.pid}', AlertLevel.HIGH, f'Processo {process.name} (PID: {process.pid}) usando {process.cpu_percent:.1f}% CPU', process.cpu_percent, 50, process_info=process)
            if high_memory_processes:
                high_memory_processes.sort(key=(lambda p: p.memory_percent), reverse=True)
                for process in high_memory_processes[:3]:
                    self._create_alert(f'process_memory_{process.pid}', AlertLevel.MEDIUM, f'Processo {process.name} (PID: {process.pid}) usando {process.memory_percent:.1f}% RAM', process.memory_percent, 30, process_info=process)
                return
        except Exception as e:
            self.logger.error(f'Erro ao verificar alertas de processos: {str(e)}')
    def _create_alert(self, alert_type: str, level: AlertLevel, message: str, value: float, threshold: float, process_info: Optional[ProcessInfo]=None):
        '''
Cria um alerta do sistema - vers├úo otimizada com controle de spam
Args:
    alert_type: Tipo do alerta
    level: N├¡vel do alerta
    message: Mensagem do alerta
    value: Valor atual
    threshold: Limite configurado
    process_info: Informa├º├Áes do processo (se aplic├ível)
'''
        try:
            current_time = datetime.now()
            if alert_type in self.last_alerts:
                last_alert_time = self.last_alerts[alert_type]
                if (current_time - last_alert_time).total_seconds() < 10:
                    return
            self.last_alerts[alert_type] = current_time
            alert = AlertInfo(timestamp=current_time, alert_type=alert_type, level=level, message=message, value=value, threshold=threshold, process_info=process_info)
            self.alerts.append(alert)
            if len(self.alerts) > 50:
                self.alerts = self.alerts[-50:]
            for callback in self.alert_callbacks:
                pass
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f'Erro no callback de alerta: {str(e)}')
            else:
                if level in (AlertLevel.HIGH, AlertLevel.CRITICAL):
                    self.logger.warning(f'Alerta {level.value[1]} {message}')
        except Exception as e:
            self.logger.error(f'Erro ao criar alerta: {str(e)}')
    def get_process_from_alert(self, alert: AlertInfo) -> Optional[ProcessInfo]:
        '''
Obt├®m informa├º├Áes atualizadas do processo de um alerta
Args:
    alert: Alerta contendo informa├º├Áes do processo
Returns:
    Optional[ProcessInfo]: Processo atualizado ou None se n├úo encontrado
'''
        try:
            if not alert.process_info:
                return
            processes = self.get_processes(limit=50)
            for process in processes:
                if process.pid == alert.process_info.pid or process.name == alert.process_info.name:
                    return process
        except Exception as e:
            self.logger.error(f'Erro ao obter processo do alerta: {str(e)}')
        return alert.process_info
    def get_recent_alerts(self, limit: int=20) -> List[AlertInfo]:
        '''
Obt├®m alertas recentes
Args:
    limit: N├║mero m├íximo de alertas
Returns:
    List[AlertInfo]: Lista de alertas recentes
'''
        try:
            return sorted(self.alerts, key=(lambda a: a.timestamp), reverse=True)[:limit]
        except Exception as e:
            self.logger.error(f'Erro ao obter alertas recentes: {str(e)}')
            return []
    def add_alert_callback(self, callback: Callable):
        '''
Adiciona callback para alertas
Args:
    callback: Fun├º├úo a ser chamada quando houver alerta
'''
        self.alert_callbacks.append(callback)
    def remove_alert_callback(self, callback: Callable):
        '''
Remove callback de alertas
Args:
    callback: Fun├º├úo a ser removida
'''
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    def get_current_data(self) -> Dict:
        '''
Obt├®m dados atuais do monitoramento
Returns:
    Dict: Dados atuais
'''
        return {'system_info': self.current_system_info, 'processes': self.current_processes, 'last_update': self.last_update, 'is_monitoring': self.is_monitoring}
    def get_history(self, minutes: int=10) -> Dict:
        '''
Obt├®m hist├│rico de monitoramento
Args:
    minutes: N├║mero de minutos de hist├│rico
Returns:
    Dict: Hist├│rico dos dados
'''
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        filtered_system = [info for info in self.system_history if info.timestamp >= cutoff_time]
        filtered_processes = [processes for processes in self.process_history if processes if processes[0].timestamp >= cutoff_time]
        return {'system_history': filtered_system, 'process_history': filtered_processes, 'alert_history': list(self.alert_history)}
    def export_report(self, filename: str, format: str='json') -> bool:
        '''
Exporta relat├│rio de monitoramento
Args:
    filename: Nome do arquivo
    format: Formato do arquivo ("json", "csv")
Returns:
    bool: True se exportado com sucesso
'''
        try:
            if format.lower() == 'json':
                return self._export_json_report(filename)
            if format.lower() == 'csv':
                return self._export_csv_report(filename)
            self.logger.error(f'Formato n├úo suportado: {format}')
            return False
        except Exception as e:
            self.logger.error(f'Erro ao exportar relat├│rio: {str(e)}')
            return False
    def _export_json_report(self, filename: str) -> bool:
        '''
Exporta relat├│rio em formato JSON
Args:
    filename: Nome do arquivo
Returns:
    bool: True se exportado com sucesso
'''
        try:
            report_data = {'export_time': datetime.now().isoformat(), 'current_data': self.get_current_data(), 'history': self.get_history(60), 'alert_thresholds': self.alert_thresholds, 'summary': self._generate_summary()}
            def convert_dataclass(obj):
                if hasattr(obj, '__dict__'):
                    return obj.__dict__
                return obj
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=convert_dataclass, ensure_ascii=False)
            self.logger.info(f'Relat├│rio JSON exportado: {filename}')
        except Exception as e:
            self.logger.error(f'Erro ao exportar relat├│rio JSON: {str(e)}')
            return False
        return True
    def _export_csv_report(self, filename: str) -> bool:
        '''
Exporta relat├│rio em formato CSV
Args:
    filename: Nome do arquivo
Returns:
    bool: True se exportado com sucesso
'''
        try:
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'CPU_Total', 'CPU_User', 'CPU_System', 'CPU_Idle', 'Memory_Total_KB', 'Memory_Used_KB', 'Memory_Free_KB', 'Memory_Used_Percent', 'Processes_Total', 'Processes_Running', 'Load_1min', 'Load_5min', 'Load_15min'])
                for info in self.system_history:
                    writer.writerow([info.timestamp.isoformat(), info.cpu_usage.get('total_used', 0), info.cpu_usage.get('user', 0), info.cpu_usage.get('system', 0), info.cpu_usage.get('idle', 0), info.memory_usage.get('total', 0), info.memory_usage.get('used', 0), info.memory_usage.get('free', 0), info.memory_usage.get('used_percent', 0), info.processes_total, info.processes_running, info.load_average[0], info.load_average[1], info.load_average[2]])
                    continue
                writer.writerow([])
                writer.writerow(['=== PROCESSOS PRINCIPAIS ==='])
                writer.writerow(['Timestamp', 'PID', 'Name', 'CPU_Percent', 'Memory_Percent', 'Memory_KB', 'User', 'State'])
                for processes in self.process_history:
                    if processes:
                        for process in processes[:5]:
                            writer.writerow([process.timestamp.isoformat(), process.pid, process.name, process.cpu_percent, process.memory_percent, process.memory_kb, process.user, process.state])
        except Exception as e:
            self.logger.error(f'Erro ao exportar relat├│rio CSV: {str(e)}')
            return False
        try:
            self.logger.info(f'Relat├│rio CSV exportado: {filename}')
        except Exception as e:
            self.logger.error(f'Erro ao exportar relat├│rio CSV: {str(e)}')
            return False
        return True
    def _generate_summary(self) -> Dict:
        '''
Gera resumo dos dados de monitoramento
Returns:
    Dict: Resumo dos dados
'''
        try:
            if not self.system_history:
                return {}
        except Exception as e:
            self.logger.error(f'Erro ao gerar resumo: {str(e)}')
            return {}
        try:
            cpu_values = [info.cpu_usage.get('total_used', 0) for info in self.system_history]
        except Exception as e:
            self.logger.error(f'Erro ao gerar resumo: {str(e)}')
            return {}
        try:
            memory_values = [info.memory_usage.get('used_percent', 0) for info in self.system_history]
            summary = {'monitoring_duration_minutes': len(self.system_history) * (self.update_interval / 60), 'cpu_stats': {'min': min(cpu_values) if cpu_values else 0, 'max': max(cpu_values) if cpu_values else 0, 'avg': sum(cpu_values) / len(cpu_values) if cpu_values else 0}, 'memory_stats': {'min': min(memory_values) if memory_values else 0, 'max': max(memory_values) if memory_values else 0, 'avg': sum(memory_values) / len(memory_values) if memory_values else 0}, 'alert_count': len(self.alert_history), 'last_update': self.last_update.isoformat() if self.last_update else None}
            return summary
        except Exception as e:
            self.logger.error(f'Erro ao gerar resumo: {str(e)}')
            return {}
    def clear_history(self):
        '''Limpa o hist├│rico de monitoramento'''
        self.system_history.clear()
        self.process_history.clear()
        self.alerts.clear()
        self.last_alerts.clear()
        self.logger.info('Hist├│rico de monitoramento limpo')
    def set_alert_threshold(self, alert_type: str, threshold: float):
        '''
Define threshold para alertas
Args:
    alert_type: Tipo do alerta
    threshold: Valor do threshold
'''
        self.alert_thresholds[alert_type] = threshold
        self.logger.info(f'Threshold {alert_type} definido para {threshold}')
    def get_alert_thresholds(self) -> Dict[str, float]:
        '''
Obt├®m thresholds de alertas
Returns:
    Dict[str, float]: Thresholds atuais
'''
        return self.alert_thresholds.copy()
    def get_system_diagnostic(self) -> Dict:
        '''
Realiza diagn├│stico avan├ºado do sistema Android
Vers├úo corrigida com valida├º├úo de PIDs e m├®todos mais robustos
├Ütil para t├®cnicos identificarem problemas rapidamente
Returns:
    Dict: Relat├│rio de diagn├│stico com recomenda├º├Áes
'''
        diagnostic = {'timestamp': datetime.now().isoformat(), 'device_info': {}, 'performance': {}, 'storage': {}, 'battery': {}, 'network': {}, 'issues': [], 'recommendations': []}
        try:
            if not self.adb_manager or not self.adb_manager.adb_path:
                diagnostic['issues'].append('ADB n├úo est├í dispon├¡vel')
                diagnostic['recommendations'].append('Verifique se o ADB est├í instalado e configurado')
                return diagnostic
        except Exception as e:
            diagnostic['issues'].append(f'Erro na verifica├º├úo inicial: {str(e)}')
            diagnostic['recommendations'].append('Verifique as configura├º├Áes do sistema')
            self.logger.error(f'Erro na verifica├º├úo inicial: {str(e)}')
            return diagnostic
        try:
            device_connected = self.adb_manager.check_device()
            if not device_connected:
                diagnostic['issues'].append('Nenhum dispositivo Android conectado')
                diagnostic['recommendations'].append('Conecte um dispositivo Android via USB e habilite a depura├º├úo USB')
                self.logger.warning('Diagn├│stico cancelado: nenhum dispositivo conectado')
                return diagnostic
            self.logger.info('Dispositivo conectado detectado, iniciando diagn├│stico...')
        except Exception as e:
            diagnostic['issues'].append(f'Erro ao verificar dispositivo: {str(e)}')
            diagnostic['recommendations'].append('Verifique a conex├úo USB e as configura├º├Áes do ADB')
            self.logger.error(f'Erro ao verificar dispositivo: {str(e)}')
            try:
                return diagnostic
            except Exception as e:
                diagnostic['issues'].append(f'Erro na verifica├º├úo inicial: {str(e)}')
                diagnostic['recommendations'].append('Verifique as configura├º├Áes do sistema')
                self.logger.error(f'Erro na verifica├º├úo inicial: {str(e)}')
                return diagnostic
        try:
            model = self._execute_adb_command_safe(['shell', 'getprop', 'ro.product.model'])
            manufacturer = self._execute_adb_command_safe(['shell', 'getprop', 'ro.product.manufacturer'])
            android_version = self._execute_adb_command_safe(['shell', 'getprop', 'ro.build.version.release'])
            api_level = self._execute_adb_command_safe(['shell', 'getprop', 'ro.build.version.sdk'])
            diagnostic['device_info'] = {'model': model.strip(), 'manufacturer': manufacturer.strip(), 'android_version': android_version.strip(), 'api_level': api_level.strip()}
        except Exception as e:
            diagnostic['issues'].append(f'Erro ao obter informa├º├Áes do dispositivo: {str(e)}')
        try:
            system_info = self.get_system_info()
            if system_info:
                cpu_usage = 0
                if system_info.cpu_usage:
                    user_cpu = system_info.cpu_usage.get('user', 0)
                    system_cpu = system_info.cpu_usage.get('system', 0)
                    wait_cpu = system_info.cpu_usage.get('wait', 0)
                    cpu_usage = user_cpu + system_cpu + wait_cpu
                memory_usage_percent = 0
                memory_total_mb = 0
                memory_used_mb = 0
                memory_free_mb = 0
                if system_info.memory_usage:
                    if 'used_percent' in system_info.memory_usage:
                        memory_usage_percent = system_info.memory_usage['used_percent']
                    elif 'total' in system_info.memory_usage and 'used' in system_info.memory_usage:
                        total = system_info.memory_usage['total']
                        used = system_info.memory_usage['used']
                        memory_usage_percent = used / total * 100 if total > 0 else 0
                    memory_total_mb = round(system_info.memory_usage.get('total', 0) / 1024, 2)
                    memory_used_mb = round(system_info.memory_usage.get('used', 0) / 1024, 2)
                    memory_free_mb = round(system_info.memory_usage.get('free', 0) / 1024, 2)
                diagnostic['performance'] = {'cpu_usage': round(cpu_usage, 2), 'memory_usage_percent': round(memory_usage_percent, 2), 'memory_total_mb': memory_total_mb, 'memory_used_mb': memory_used_mb, 'memory_free_mb': memory_free_mb, 'load_average': system_info.load_average, 'processes_total': system_info.processes_total, 'processes_running': system_info.processes_running, 'processes_sleeping': system_info.processes_sleeping, 'processes_zombie': system_info.processes_zombie}
                if cpu_usage > 90:
                    diagnostic['issues'].append(f'CPU com uso muito alto ({cpu_usage:.1f}%)')
                    diagnostic['recommendations'].append('Verifique processos consumindo CPU e considere reiniciar')
                elif cpu_usage > 70:
                    diagnostic['issues'].append(f'CPU com uso elevado ({cpu_usage:.1f}%)')
                    diagnostic['recommendations'].append('Monitore processos com alto uso de CPU')
                if memory_usage_percent > 90:
                    diagnostic['issues'].append(f'Mem├│ria RAM quase esgotada ({memory_usage_percent:.1f}%)')
                    diagnostic['recommendations'].append('Feche aplicativos desnecess├írios ou reinicie o dispositivo')
                elif memory_usage_percent > 80:
                    diagnostic['issues'].append(f'Mem├│ria RAM com uso elevado ({memory_usage_percent:.1f}%)')
                    diagnostic['recommendations'].append('Considere fechar alguns aplicativos')
                if system_info.processes_zombie > 0:
                    diagnostic['issues'].append(f'Processos zumbi detectados: {system_info.processes_zombie}')
                    diagnostic['recommendations'].append('Processos zumbi podem indicar problemas no sistema')
        except Exception as e:
            diagnostic['issues'].append(f'Erro ao analisar performance: {str(e)}')
        try:
            storage_output = self._execute_adb_command_safe(['shell', 'df', '/data'])
            lines = storage_output.strip().split('\n')
            if len(lines) > 1:
                data_line = lines[1].split()
                if len(data_line) >= 5:
                    total_kb = int(data_line[1])
                    used_kb = int(data_line[2])
                    available_kb = int(data_line[3])
                    used_percent = used_kb / total_kb * 100
                    diagnostic['storage'] = {'total_gb': round(total_kb / 1024 / 1024, 2), 'used_gb': round(used_kb / 1024 / 1024, 2), 'available_gb': round(available_kb / 1024 / 1024, 2), 'used_percent': round(used_percent, 2)}
                    if used_percent > 95:
                        diagnostic['issues'].append(f'Armazenamento quase cheio ({used_percent:.1f}%)')
                        diagnostic['recommendations'].append('Libere espa├ºo deletando arquivos desnecess├írios')
                    elif used_percent > 85:
                        diagnostic['issues'].append(f'Armazenamento com pouco espa├ºo ({used_percent:.1f}%)')
                        diagnostic['recommendations'].append('Considere limpar cache e arquivos tempor├írios')
        except Exception as e:
            diagnostic['issues'].append(f'Erro ao verificar armazenamento: {str(e)}')
        try:
            battery_output = self._execute_adb_command_safe(['shell', 'dumpsys', 'battery'])
            level = None
            temp = None
            for line in battery_output.split('\n'):
                if 'level:' in line:
                    level_match = re.search('level:\\s*(\\d+)', line)
                    if level_match:
                        level = int(level_match.group(1))
                elif 'temperature:' in line:
                    temp_match = re.search('temperature:\\s*(\\d+)', line)
                    if temp_match:
                        temp = int(temp_match.group(1)) / 10
            if level is not None:
                diagnostic['battery']['level'] = level
                if level < 15:
                    diagnostic['issues'].append(f'Bateria com carga baixa ({level}%)')
                    diagnostic['recommendations'].append('Conecte o carregador')
            if temp is not None:
                diagnostic['battery']['temperature'] = round(temp, 1)
                if temp > 40:
                    diagnostic['issues'].append(f'Bateria com temperatura alta ({temp}┬░C)')
                    diagnostic['recommendations'].append('Deixe o dispositivo esfriar')
        except Exception as e:
            diagnostic['issues'].append(f'Erro ao verificar bateria: {str(e)}')
        try:
            wifi_output = self._execute_adb_command_safe(['shell', 'dumpsys', 'wifi'])
            if 'mWifiEnabled: true' in wifi_output:
                diagnostic['network']['wifi_enabled'] = True
            else:
                diagnostic['network']['wifi_enabled'] = False
                diagnostic['issues'].append('WiFi est├í desabilitado')
        except Exception as e:
            diagnostic['issues'].append(f'Erro ao verificar conectividade: {str(e)}')
        try:
            try:
                processes = self.get_processes(limit=50)
                mdm_processes = []
                high_cpu_processes = []
                for process in processes:
                    if self._is_mdm_process(process.name):
                        mdm_processes.append(process.name)
                    if process.cpu_percent > 20:
                        high_cpu_processes.append({'name': process.name, 'cpu': process.cpu_percent, 'pid': process.pid})
                if mdm_processes:
                    diagnostic['issues'].append(f'Processos MDM detectados: {', '.join(mdm_processes[:3])}')
                    diagnostic['recommendations'].append('Verifique se h├í bloqueios de tela ou MDM ativo')
                if high_cpu_processes:
                    top_cpu = high_cpu_processes[0]
                    diagnostic['issues'].append(f'Processo com alto CPU: {top_cpu['name']} ({top_cpu['cpu']:.1f}%)')
                    diagnostic['recommendations'].append(f'Considere finalizar o processo PID {top_cpu['pid']}')
            except Exception as e:
                diagnostic['issues'].append(f'Erro ao analisar processos: {str(e)}')
        except Exception as e:
            diagnostic['issues'].append(f'Erro geral no diagn├│stico: {str(e)}')
        if not diagnostic['issues']:
            diagnostic['recommendations'].append('Sistema funcionando normalmente')
        else:
            try:
                diagnostic['recommendations'].append('Execute os comandos ADB necess├írios para resolver os problemas')
            except Exception as e:
                diagnostic['issues'].append(f'Erro geral no diagn├│stico: {str(e)}')
        try:
            if hasattr(self.adb_manager, 'finalize_adb_operation'):
                self.adb_manager.finalize_adb_operation()
        except:
            pass
        return diagnostic
    def _is_mdm_process(self, process_name: str) -> bool:
        '''Verifica se um processo ├® relacionado ao MDM'''
        mdm_patterns = ['payjoy', 'paks', 'sysdll', 'mdm', 'deviceowner', 'managedprovisioning', 'knox', 'airwatch', 'mobileiron', 'intune', 'xenmobile', 'maas360']
        process_lower = process_name.lower()
        return any((pattern in process_lower for pattern in mdm_patterns))
    def is_device_responsive(self) -> bool:
        '''
Verifica se o dispositivo est├í responsivo
Returns:
    bool: True se responsivo
'''
        try:
            start_time = time.time()
            self._execute_adb_command(['shell', 'echo', 'test'], timeout=5)
            response_time = time.time() - start_time
            return response_time < 2.0
        except Exception:
            return False
    def get_process_details(self, pid: int) -> Optional[Dict]:
        '''
Obt├®m informa├º├Áes b├ísicas do processo - vers├úo segura para usu├írios finais
Args:
    pid: ID do processo
Returns:
    Optional[Dict]: Informa├º├Áes b├ísicas do processo ou None se n├úo encontrado
'''
        try:
            if not self._validate_single_pid(pid):
                return
            process_info = {'pid': pid, 'basic_info': {}, 'resource_usage': {}, 'status': 'Ativo'}
            try:
                cmdline_output = self._execute_adb_command_safe(['shell', 'cat', f'/proc/{pid}/cmdline'])
                if cmdline_output:
                    process_name = cmdline_output.replace('\x00', ' ').strip()
                    if process_name:
                        process_info['basic_info']['nome'] = process_name
            except Exception:
                process_info['basic_info']['nome'] = f'Processo {pid}'
        except Exception as e:
            self.logger.error(f'Erro ao obter detalhes do processo {pid}: {str(e)}')
        try:
            status_output = self._execute_adb_command_safe(['shell', 'cat', f'/proc/{pid}/status'])
            if status_output:
                status_lines = status_output.strip().split('\n')
                for line in status_lines:
                    if line.startswith('Name:'):
                        process_info['basic_info']['nome_sistema'] = line.split('\t')[1].strip()
                        continue
                    if line.startswith('State:'):
                        state_info = line.split('\t')[1].strip()
                        process_info['basic_info']['estado'] = state_info
                        continue
                    if line.startswith('Pid:'):
                        process_info['basic_info']['pid'] = line.split('\t')[1].strip()
                        continue
                    if line.startswith('PPid:'):
                        process_info['basic_info']['processo_pai'] = line.split('\t')[1].strip()
                        continue
                    if not line.startswith('Uid:'):
                        continue
                    uid_info = line.split('\t')[1].strip()
                    process_info['basic_info']['usuario'] = uid_info
                    continue
        except Exception:
            process_info['basic_info']['estado'] = 'N├úo dispon├¡vel'
        try:
            current_processes = self.get_processes(limit=100)
            for process in current_processes:
                if not process.pid == pid:
                    continue
                process_info['resource_usage'] = {'cpu_percent': f'{process.cpu_percent:.1f}%', 'memory_percent': f'{process.memory_percent:.1f}%', 'memory_mb': f'{process.memory_kb / 1024:.1f} MB', 'priority': process.priority, 'nice': process.nice}
                return process_info
        except Exception:
            process_info['resource_usage'] = {'cpu_percent': 'N├úo dispon├¡vel', 'memory_percent': 'N├úo dispon├¡vel', 'memory_mb': 'N├úo dispon├¡vel'}
        return process_info
        try:
            pass
        except Exception:
            process_info['resource_usage'] = {'cpu_percent': 'N├úo dispon├¡vel', 'memory_percent': 'N├úo dispon├¡vel', 'memory_mb': 'N├úo dispon├¡vel'}
        return process_info
        return process_info
    def _validate_single_pid(self, pid: int) -> bool:
        '''
Valida se um PID espec├¡fico ainda existe
Args:
    pid: PID para validar
Returns:
    bool: True se PID existe
'''
        try:
            result = self._execute_adb_command_safe(['shell', 'test', '-d', f'/proc/{pid}', '&&', 'echo', 'exists'])
        except:
            try:
                ps_output = self._execute_adb_command_safe(['shell', 'ps', '-p', str(pid)])
            except:
                return False
            return str(pid) in ps_output and len(ps_output.split('\n')) > 1
        return 'exists' in result
    def format_process_details_for_display(self, details: Dict) -> str:
        '''
Formata detalhes do processo para exibi├º├úo amig├ível ao usu├írio final
Args:
    details: Dicion├írio com informa├º├Áes b├ísicas do processo
Returns:
    str: Texto formatado para exibi├º├úo
'''
        if not details:
            return 'Informa├º├Áes do processo n├úo dispon├¡veis'
        lines = []
        lines.append('==================================================')
        lines.append('INFORMA├ç├òES DO PROCESSO')
        lines.append('==================================================')
        lines.append('')
        basic_info = details.get('basic_info', {})
        if basic_info:
            lines.append('INFORMACOES BASICAS:')
            lines.append(f'   Nome: {basic_info.get('nome', 'N├úo dispon├¡vel')}')
            if 'nome_sistema' in basic_info:
                lines.append(f'   Nome do Sistema: {basic_info['nome_sistema']}')
            lines.append(f'   PID: {details.get('pid', 'N├úo dispon├¡vel')}')
            if 'processo_pai' in basic_info:
                lines.append(f'   Processo Pai: {basic_info['processo_pai']}')
            if 'estado' in basic_info:
                estado = basic_info['estado']
                if 'S' in estado:
                    estado_amigavel = 'Executando normalmente'
                elif 'R' in estado:
                    estado_amigavel = 'Ativo (processando)'
                elif 'Z' in estado:
                    estado_amigavel = 'Finalizado'
                elif 'T' in estado:
                    estado_amigavel = 'Pausado'
                else:
                    estado_amigavel = 'Funcionando'
                lines.append(f'   Status: {estado_amigavel}')
            lines.append('')
        resource_usage = details.get('resource_usage', {})
        if resource_usage:
            lines.append('USO DE RECURSOS:')
            cpu = resource_usage.get('cpu_percent', 'N├úo dispon├¡vel')
            lines.append(f'   CPU: {cpu}')
            memory = resource_usage.get('memory_percent', 'N├úo dispon├¡vel')
            lines.append(f'   RAM: {memory}')
            memory_mb = resource_usage.get('memory_mb', 'N├úo dispon├¡vel')
            lines.append(f'   Mem├│ria: {memory_mb}')
            if 'priority' in resource_usage:
                priority = resource_usage['priority']
                if priority < 0:
                    priority_text = 'Alta prioridade'
                elif priority == 0:
                    priority_text = 'Prioridade normal'
                else:
                    priority_text = 'Baixa prioridade'
                lines.append(f'   Prioridade: {priority_text}')
            lines.append('')
        lines.append('STATUS GERAL:')
        status = details.get('status', 'Desconhecido')
        lines.append(f'   Processo: {status}')
        lines.append('')
        lines.append('INFORMACOES ADICIONAIS:')
        lines.append('   ÔÇó Este processo faz parte do sistema Android')
        lines.append('   ÔÇó Finalizar processos do sistema pode causar instabilidade')
        lines.append("   ÔÇó Use 'Kill' apenas se o processo n├úo responder")
        lines.append("   ÔÇó 'Force Kill' deve ser usado com extrema cautela")
        lines.append('')
        lines.append('==================================================')
        lines.append('TECH UNION SOLUTIONS - Monitor de Processos')
        lines.append('==================================================')
        return '\n'.join(lines)
    def _initialize_app_names_cache(self):
        '''
        Inicializa cache de nomes de aplica├º├Áes instaladas
        Executa em background para n├úo atrasar a inicializa├º├úo
        '''
        try:
            if not self.adb_manager or not hasattr(self.adb_manager, 'check_device'):
                return
            import threading
            cache_thread = threading.Thread(target=self._load_app_names_cache, daemon=True)
            cache_thread.start()
            return
        except Exception as e:
            self.logger.debug(f'Falha ao inicializar cache de nomes: {str(e)}')
    def _load_app_names_cache(self):
        '''
        Carrega cache de nomes de aplica├º├Áes (executado em thread separada)
        '''
        try:
            if not self.adb_manager.check_device():
                return
            packages_output = self._execute_adb_command_safe(['shell', 'pm', 'list', 'packages', '-3'])
            for line in packages_output.split('\n'):
                if line.startswith('package:'):
                    package_name = line.replace('package:', '').strip()
                    if package_name:
                        friendly_name = self._get_app_friendly_name(package_name)
                        if friendly_name and friendly_name != package_name:
                            self.app_names_cache[package_name] = friendly_name
                        self.package_names_cache[package_name] = True
            self.logger.info(f'Cache de nomes carregado: {len(self.app_names_cache)} apps')
            return
        except Exception as e:
            self.logger.debug(f'Erro ao carregar cache de nomes: {str(e)}')
    def _get_app_friendly_name(self, package_name: str) -> str:
        '''
Obt├®m nome amig├ível de um package Android
Args:
    package_name: Nome do package (ex: com.whatsapp)
Returns:
    str: Nome amig├ível ou package_name se n├úo conseguir obter
'''
        try:
            if package_name in self.app_names_cache:
                return self.app_names_cache[package_name]
            known_apps = {'com.whatsapp': 'WhatsApp', 'com.instagram.android': 'Instagram', 'com.facebook.katana': 'Facebook', 'com.google.android.youtube': 'YouTube', 'com.spotify.music': 'Spotify', 'com.android.chrome': 'Chrome', 'com.google.android.gms': 'Google Play Services', 'com.android.vending': 'Google Play Store', 'com.google.android.apps.photos': 'Google Photos', 'com.google.android.apps.docs': 'Google Drive', 'com.google.android.gm': 'Gmail', 'com.google.android.maps': 'Google Maps', 'com.uber.Rider': 'Uber', 'com.ubercab': 'Uber', 'com.zhiliaoapp.musically': 'TikTok', 'com.netflix.mediaclient': 'Netflix', 'com.amazon.mShop.android.shopping': 'Amazon', 'com.paypal.android.p2pmobile': 'PayPal', 'com.microsoft.office.word': 'Microsoft Word', 'com.adobe.reader': 'Adobe Reader', 'com.viber.voip': 'Viber', 'com.skype.raider': 'Skype', 'com.discord': 'Discord', 'com.zoom.us': 'Zoom', 'com.teamviewer.teamviewer.market.mobile': 'TeamViewer', 'com.dropbox.android': 'Dropbox', 'com.microsoft.teams': 'Microsoft Teams', 'com.slack': 'Slack'}
            if package_name in known_apps:
                friendly_name = known_apps[package_name]
                self.app_names_cache[package_name] = friendly_name
                return friendly_name
            device_model = self._get_device_model()
            skip_aapt = any((keyword in device_model.lower() for keyword in ('infinix', 'transsion', 'tecno', 'itel')))
            if not skip_aapt:
                pass
            try:
                aapt_output = self._execute_adb_command(['shell', 'aapt', 'dump', 'badging', f'$(pm path {package_name} | head -1 | cut -d: -f2)'], timeout=5)
                for line in aapt_output.split('\n'):
                    if 'application-label:' in line:
                        import re
                        match = re.search("application-label:'([^']*)'", line)
                        if match:
                            friendly_name = match.group(1)
                            self.app_names_cache[package_name] = friendly_name
                            return friendly_name
            except Exception:
                pass
            else:
                logger.debug(f'Pulando AAPT para dispositivo {device_model} (n├úo suportado)')
        except Exception as e:
            return package_name
        try:
            try:
                dump_output = self._execute_adb_command_safe(['shell', 'pm', 'dump', package_name], timeout=3)
                for line in dump_output.split('\n'):
                    if 'applicationLabel=' in line:
                        label = line.split('applicationLabel=')[1].strip()
                        if not label:
                            continue
                        if label != package_name:
                            self.app_names_cache[package_name] = label
                            return label
            except Exception:
                pass
        except Exception as e:
            return package_name
        friendly_name = self._create_friendly_name_from_package(package_name)
        self.app_names_cache[package_name] = friendly_name
        return friendly_name
    def _get_device_model(self):
        '''Obt├®m modelo do dispositivo para detectar Infinix/Transsion'''
        try:
            if hasattr(self, '_cached_device_model'):
                return self._cached_device_model
            model_output = self._execute_adb_command_safe(['shell', 'getprop', 'ro.product.model'], timeout=3)
            self._cached_device_model = model_output.strip() if model_output else 'Unknown'
        except Exception:
            return 'Unknown'
        return self._cached_device_model
    def _create_friendly_name_from_package(self, package_name: str) -> str:
        '''
Cria nome amig├ível baseado no nome do package
Args:
    package_name: Nome do package
Returns:
    str: Nome mais amig├ível
'''
        try:
            name = package_name
            prefixes_to_remove = ['com.', 'org.', 'net.', 'io.', 'app.']
            for prefix in prefixes_to_remove:
                if not name.startswith(prefix):
                    continue
                name = name[len(prefix):]
                break
            parts = name.split('.')
            if len(parts) > 0:
                main_part = parts[0]
                if main_part:
                    return main_part.capitalize()
            return package_name
        except Exception:
            return package_name
    def get_enhanced_process_name(self, process_name: str, pid: int) -> str:
        '''
Obt├®m nome melhorado do processo com informa├º├Áes adicionais
Args:
    process_name: Nome original do processo
    pid: PID do processo
Returns:
    str: Nome melhorado do processo
'''
        try:
            if '.' in process_name and len(process_name.split('.')) >= 2:
                if process_name in self.app_names_cache:
                    friendly_name = self.app_names_cache[process_name]
                    return f'{friendly_name} ({process_name})'
                if process_name in self.package_names_cache:
                    friendly_name = self._get_app_friendly_name(process_name)
                    if friendly_name != process_name:
                        return f'{friendly_name} ({process_name})'
            if process_name.startswith('android.'):
                return f'[SYS] {process_name.split('.')[-1]}'
            if 'google' in process_name.lower():
                return f'[GMS] {process_name}'
            mdm_indicators = ['mdm', 'knox', 'airwatch', 'mobileiron', 'payjoy', 'paks']
            if any((indicator in process_name.lower() for indicator in mdm_indicators)):
                return f'[MDM] {process_name}'
            if process_name.startswith('[') and process_name.endswith(']'):
                return f'[KRN] {process_name}'
            system_processes = ['init', 'kthreadd', 'systemd', 'zygote', 'servicemanager']
            if process_name in system_processes:
                return f'[CORE] {process_name}'
            return process_name
        except Exception:
            return process_name
