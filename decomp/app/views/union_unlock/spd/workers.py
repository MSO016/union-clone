'''
QThread workers do modulo SPD.
Ver: alan/documentacao/16-08-2026-ARQUITETURA-SPD-INTERNA/01_MAPA_REFERENCIAS_INTERNAS.md
'''
import time
import os
from PyQt5.QtCore import QThread, pyqtSignal
class SPDFullWorker(QThread):
    '''
Worker completo: escuta -> detecta -> FDL -> operacao -> reset.
Fluxo unico sequencial:
  1. Aguarda dispositivo na porta COM (polling)
  2. Carrega FDL1 (CRC16) + FDL2 (ADD)
  3. Executa operacao selecionada
  4. Reset dispositivo
     ÔåÆ abre porta ÔåÆ Download_FDL1 ÔåÆ Download_FDL2
     ÔåÆ CkFDLLoaded.Checked = true ÔåÆ UniworkerTodo()
Sinais:
    log_signal(str, str)       ÔÇö (mensagem, tipo) para TerminalLog
    progress_signal(int, int)  ÔÇö (current, total) para StatusBar
    status_signal(str)         ÔÇö status textual para ResponseLabel
    fdl_loaded_signal(bool)    ÔÇö FDL carregado
    device_found_signal(str)   ÔÇö porta COM detectada
    finished_signal(bool, str) ÔÇö (sucesso, mensagem)
'''
    log_signal = pyqtSignal(str, str)
    progress_signal = pyqtSignal(int, int)
    status_signal = pyqtSignal(str)
    fdl_loaded_signal = pyqtSignal(bool)
    device_found_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, operation: str, model_config, engine: str='binary', timeout: int=120, use_advanced_auth: bool=True, force_kick: bool=False, parent=None):
        '''
Args:
    operation: nome da opera├º├úo (ex: "ERASE FRP ONLY")
    model_config: ModelConfig com FDL paths e endere├ºos
    engine: "internal" (Python puro) ou "binary" (spd_dump.exe)
    timeout: timeout em segundos para aguardar dispositivo
    use_advanced_auth: quando False, ignora exec_addr do modelo
        (autorizacao avancada desligada). Default True mantem
        compatibilidade com o comportamento historico.
    force_kick: quando True, passa --kick ao spd_dump. Usado
        para forcar a rota `boot_diag -> cali_diag -> dl_diag`
        em devices/portas USB instaveis. Default False (rota
        padrao autodetect).
'''
        super().__init__(parent)
        self.operation = operation
        self.model_config = model_config
        self.engine = engine
        self.timeout = timeout
        self.use_advanced_auth = use_advanced_auth
        self.force_kick = force_kick
        self._stop_requested = False
    def stop(self):
        '''
Solicita parada da opera├º├úo.
     cts.Cancel() ÔåÆ Thread.Sleep(3000) ÔåÆ CkFDLLoaded = false
'''
        self._stop_requested = True
    def run(self):
        '''
        Executa o fluxo completo: escuta ÔåÆ FDL ÔåÆ opera├º├úo ÔåÆ reset.
        '''
        try:
            self._start_time = time.time()
            mc = self.model_config
            self.log_signal.emit(f'Opera├º├úo      : {self.operation}', 'op')
            self.log_signal.emit(f'Marca         : {mc.brand}', 'label_value')
            self.log_signal.emit(f'Modelo        : {mc.model}', 'label_value')
            self.log_signal.emit(f'Chipset       : {mc.chipset}', 'label_value')
            self.log_signal.emit('Plataforma    : Spreadtrum', 'label_value')
            self.log_signal.emit('Conex├úo       : Modo SPD', 'label_value')
            modo_label = 'Auth Tech Union' if self.use_advanced_auth else 'Normal'
            self.log_signal.emit(f'Modo          : {modo_label}', 'label_value')
            self.log_signal.emit('ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ', 'debug')
            port = self._wait_for_device()
            if port is None:
                return
            if self.engine == 'binary':
                self._run_binary_full(port)
                return
            self._run_internal_full(port)
            return
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f'SPDFullWorker erro: {e}')
            safe_msg = self._sanitize_error(str(e))
            self.log_signal.emit(f'Erro: {safe_msg}', 'error')
            self.status_signal.emit(f'Erro: {safe_msg}')
            self.fdl_loaded_signal.emit(False)
            self.finished_signal.emit(False, safe_msg)
    def _wait_for_device(self):
        '''
        Aguarda dispositivo SPD aparecer numa porta COM.
        Retorna porta COM (str) ou None se cancelado/timeout.
        '''
        from app.views.union_unlock.spd.device_detect import DeviceDetector
        self.log_signal.emit('', 'info')
        self.log_signal.emit('Searching for usb device...', 'warning')
        self.log_signal.emit('Conecte o celular em Modo SPD (Test Point)', 'info')
        self.log_signal.emit('', 'info')
        self.status_signal.emit('Aguardando dispositivo SPD...')
        detector = DeviceDetector()
        def on_waiting(elapsed, total):
            '''Callback chamado a cada poll ÔÇö atualiza status.'''
            remaining = int(total - elapsed)
            self.status_signal.emit(f'Aguardando dispositivo SPD... ({remaining}s)')
        device = detector.wait_for_device(timeout=self.timeout, poll_interval=0.5, on_waiting=on_waiting)
        if self._stop_requested:
            self.log_signal.emit('Cancelado pelo usu├írio', 'warning')
            self.finished_signal.emit(False, 'Cancelado')
            return
        if device is None:
            self.log_signal.emit('Timeout ÔÇö nenhum dispositivo SPD detectado', 'error')
            self.status_signal.emit('Timeout ÔÇö dispositivo n├úo encontrado')
            self.finished_signal.emit(False, 'Timeout')
            return
        port = device.port
        self.device_found_signal.emit(port)
        self.log_signal.emit('Searching for usb device... Found', 'success')
        if device.name:
            self.log_signal.emit(f'{device.name}', 'info')
        self.log_signal.emit('', 'debug')
        return port
    def _run_internal_full(self, port: str):
        '''
        Fluxo completo via Engine Interna: FDL ÔåÆ opera├º├úo ÔåÆ reset.
        '''
        from app.views.union_unlock.spd.transport import SerialTransport
        from app.views.union_unlock.spd.protocol import SPDProtocol
        from app.views.union_unlock.spd.checksum import Checksum
        from app.views.union_unlock.spd.loader import FDLLoader
        from app.views.union_unlock.spd.operations import SPDOperations
        mc = self.model_config
        self.log_signal.emit('Preparando dados...', 'info')
        srv_id = getattr(mc, '_srv_id', None)
        if srv_id and (not mc.data_dir or not os.path.isdir(mc.data_dir)):
            try:
                from app.views.union_unlock.spd.spd_sync import get_sync
                fdl_set = get_sync().download_fdls(srv_id)
                if not fdl_set:
                    raise RuntimeError('Falha ao preparar dados. Verifique a conexao.')
                fdl1_data = fdl_set.fdl1
                fdl2_data = fdl_set.fdl2
            except ImportError:
                raise RuntimeError('Componente de sincronizacao indisponivel.')
        else:
            try:
                fdl1_data = mc.load_fdl1()
                fdl2_data = mc.load_fdl2()
            except FileNotFoundError:
                raise RuntimeError('Dados do modelo nao encontrados. Verifique a instalacao.')
        if self._stop_requested:
            self.finished_signal.emit(False, 'Cancelado pelo usu├írio')
            return
        self.log_signal.emit('Connecting with device... ', 'info')
        self.status_signal.emit('Conectando ao dispositivo...')
        transport = SerialTransport()
        if not transport.connect(port):
            raise RuntimeError('Falha ao conectar. Verifique o cabo e os drivers.')
        try:
            checksum = Checksum()
            protocol = SPDProtocol(transport, checksum)
            loader = FDLLoader(protocol, checksum, progress_callback=self._on_progress)
            self.log_signal.emit('Sending preloader... ', 'info')
            self.status_signal.emit('Enviando dados...')
            if not loader.load_fdl1(fdl1_data, mc.fdl1_addr, exec_addr=mc.exec_addr):
                raise RuntimeError('Falha ao enviar dados. Reconecte o dispositivo.')
            if self._stop_requested:
                self.finished_signal.emit(False, 'Cancelado pelo usu├írio')
                transport.disconnect()
                return
        finally:
            transport.disconnect()
        try:
            self.log_signal.emit('Sending preloader... Ok', 'success')
            self.log_signal.emit('Initializing device... ', 'info')
            self.status_signal.emit('Inicializando dispositivo...')
            if not loader.load_fdl2(fdl2_data, mc.fdl2_addr):
                raise RuntimeError('Falha na inicializacao. Reconecte o dispositivo.')
            self.log_signal.emit('Initializing device... Ok', 'success')
            self.fdl_loaded_signal.emit(True)
            ops = SPDOperations(protocol, progress_callback=self._on_progress)
            success = self._execute_operation_internal(ops)
            if success:
                self.log_signal.emit('Rebooting device... Ok', 'success')
                protocol.send_reset()
                self._finish_success()
            else:
                self._finish_error('Opera├º├úo falhou')
        finally:
            transport.disconnect()
    def _execute_operation_internal(self, ops) -> bool:
        '''
        Executa a opera├º├úo via Engine Interna (Auth-2).
        Suporta nomes legado e nomes do banco (labels).
        '''
        op = self.operation.upper()
        self.status_signal.emit(f'Executando: {self.operation}')
        if 'FRP ONLY' in op or 'REMOVER FRP' in op:
            self.log_signal.emit('Formatting desired partition... ', 'info')
            result = ops.erase_frp()
            if result:
                self.log_signal.emit('Formatting desired partition... Ok', 'success')
            return result
        if 'DATA + FRP' in op or 'APAGAR DATA' in op:
            self.log_signal.emit('Formatting desired partition... ', 'info')
            result = ops.erase_data_and_frp()
            if result:
                self.log_signal.emit('Formatting desired partition... Ok', 'success')
            return result
        if 'FACTORY' in op:
            self.log_signal.emit('Formatting desired partition... ', 'info')
            result = ops.erase_data_and_frp()
            if result:
                self.log_signal.emit('Formatting desired partition... Ok', 'success')
            return result
        if 'FULL FRP REMOVE' in op or 'UNION' in op:
            self.log_signal.emit('Formatting desired partition... ', 'info')
            persist_data = self.model_config.load_persist()
            result = ops.full_frp_remove(persist_data=persist_data)
            if result:
                self.log_signal.emit('Formatting desired partition... Ok', 'success')
            return result
        self.log_signal.emit(f'Operacao: {op}', 'info')
        return ops.erase_frp()
    _RETRIABLE_MARKERS = ('conexao usb perdida', 'verifique o cabo', 'dispositivo nao detectado', 'porta de comunicacao nao encontrada', 'falha na comunicacao com o dispositivo', 'tempo limite atingido', 'falha na inicializacao', 'possivel erro nas conexoes')
    def _is_retriable_error(self, msg: str) -> bool:
        '''Detecta se o erro veio da fase de conexao (seguro pra retry).'''
        if not msg:
            return False
        lo = msg.lower()
        return any((m in lo for m in self._RETRIABLE_MARKERS))
    def _run_binary_full(self, port: str):
        '''
        Fluxo completo via Auth-1 usando SPDDumpProcess (bin_spd.py).
        Usa a MESMA classe que faz leitura de parti├º├Áes com sucesso.
        Suporta configuracoes vindas do cache local sincronizado com o servidor
        (extrair_fdls_temp) ou de arquivos previamente disponibilizados via data_dir.
        Retry externo: se a fase de conexao falhar com erro fisico (cabo,
        driver, USB), tenta 1x adicional apos ~2s de pausa. Isso NAO se
        aplica apos operacao iniciada (evita erase duplicado).
        '''
        max_attempts = 2
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                self._run_binary_attempt(port, attempt=attempt)
            except RuntimeError as e:
                last_error = str(e)
                op_started = getattr(self, '_op_started', False)
                if attempt < max_attempts:
                    if not op_started:
                        if self._is_retriable_error(last_error):
                            import logging as _l
                            _l.getLogger(__name__).info(f'[retry] tentativa {attempt} falhou (conexao). Nova tentativa em 2s...')
                            self.log_signal.emit('Reconectando ao dispositivo...', 'warning')
                            self.status_signal.emit('Reconectando...')
                            time.sleep(2.0)
                            if self._stop_requested:
                                self.finished_signal.emit(False, 'Cancelado')
                        else:
                            raise
                    else:
                        raise
                else:
                    raise
                continue
            return
        if last_error:
            raise RuntimeError(last_error)
    def _run_binary_attempt(self, port: str, attempt: int=1):
        '''Uma tentativa isolada do fluxo Auth-1 (chamado por _run_binary_full).'''
        from app.views.union_unlock.spd.bin_spd import SPDDumpProcess
        from app.views.union_unlock.spd.config import SPD_DUMP_PATH
        self._op_started = False
        mc = self.model_config
        self._sync_temp_paths = None
        if not os.path.isfile(SPD_DUMP_PATH):
            raise RuntimeError('Componente de comunicacao nao encontrado. Verifique a instalacao.')
        srv_id = getattr(mc, '_srv_id', None)
        model_dir = mc.data_dir
        if srv_id and (not model_dir or not os.path.isdir(model_dir)):
            try:
                from app.views.union_unlock.spd.spd_sync import get_sync
                sync = get_sync()
                paths = sync.extrair_fdls_temp(srv_id)
                if not paths:
                    raise RuntimeError('Falha ao preparar dados. Verifique a conexao com o servidor.')
                self._sync_temp_paths = paths
                fdl1_path = paths['fdl1']
                fdl2_path = paths['fdl2']
                model_dir = paths['dir']
            except ImportError:
                raise RuntimeError('Componente de sincronizacao indisponivel.')
        else:
            fdl1_dl = os.path.join(model_dir, 'fdl1-dl.bin')
            fdl2_dl = os.path.join(model_dir, 'fdl2-dl.bin')
            fdl1_path = fdl1_dl if os.path.isfile(fdl1_dl) else os.path.join(model_dir, mc.fdl1_file)
            fdl2_path = fdl2_dl if os.path.isfile(fdl2_dl) else os.path.join(model_dir, mc.fdl2_file)
        if not os.path.isfile(fdl1_path):
            raise RuntimeError('Dados do modelo incompletos. Verifique a instalacao.')
        if not os.path.isfile(fdl2_path):
            raise RuntimeError('Dados do modelo incompletos. Verifique a instalacao.')
        exec_addr = getattr(mc, 'exec_addr', None) or 0
        if not self.use_advanced_auth:
            exec_addr = 0
        _stage_holder = {'stage': ''}
        def _log_proxy(msg, level):
            '''Filtra output para o terminal da GUI ÔÇö WHITELIST estrita.
            Nunca propaga output cru ÔÇö apenas traduz eventos operacionais
            conhecidos em mensagens amigaveis. Ultimo escudo antes da GUI.
            '''
            lo = msg.lower()
            if 'bsl_rep_ver' in lo:
                if 'sprd3' in lo:
                    _stage_holder['stage'] = 'SPRD3'
                    return
                if 'sprd4' in lo:
                    _stage_holder['stage'] = 'SPRD4'
                return
            if 'check_baud' in lo and 'bootrom' in lo:
                stage = _stage_holder['stage']
                if stage:
                    self.log_signal.emit(f'Connecting with device... ({stage})', 'success')
                    return
                self.log_signal.emit('Connecting with device... Ok', 'success')
                return
            if 'exec fdl2' in lo or 'enable_write_raw_data' in lo:
                self.log_signal.emit('Initializing device... Ok', 'success')
                return
            if 'fdl2' in lo:
                if 'incompatible' in lo:
                    self.log_signal.emit('Sending data... Ok', 'success')
        spd = SPDDumpProcess(spd_dump_path=SPD_DUMP_PATH, fdl1_path=fdl1_path, fdl2_path=fdl2_path, fdl1_addr=mc.fdl1_addr, fdl2_addr=mc.fdl2_addr, exec_addr=exec_addr, cwd=model_dir, log_cb=_log_proxy, use_kick=self.force_kick)
        self.log_signal.emit('Connecting with device... ', 'info')
        self.status_signal.emit('Conectando ao dispositivo...')
        if not spd.start(wait_seconds=300):
            raise RuntimeError('Falha ao iniciar conexao. Verifique os drivers e o dispositivo.')
        try:
            ready = False
            for _ in range(120):
                if spd.wait_ready(timeout=0.5):
                    ready = True
                    break
                if spd.has_fatal_error:
                    raise RuntimeError(spd.fatal_error)
                if not spd.is_running:
                    error_msg = spd.fatal_error or 'Falha na comunicacao com o dispositivo. Verifique o cabo e tente novamente.'
                    raise RuntimeError(error_msg)
                if self._stop_requested:
                    spd.stop()
                    self.finished_signal.emit(False, 'Cancelado')
                    spd.stop()
                    if self._sync_temp_paths:
                        try:
                            from app.views.union_unlock.spd.spd_sync import SpdSync
                            SpdSync.limpar_fdls_temp(self._sync_temp_paths)
                        except Exception:
                            pass
                        return
                    return
        except Exception:
            spd.stop()
            raise
        if not ready:
            raise RuntimeError('Tempo limite atingido. Reconecte o dispositivo.')
        if self._stop_requested:
            spd.stop()
            self.finished_signal.emit(False, 'Cancelado')
            spd.stop()
            if self._sync_temp_paths:
                try:
                    from app.views.union_unlock.spd.spd_sync import SpdSync
                    SpdSync.limpar_fdls_temp(self._sync_temp_paths)
                except Exception:
                    pass
                return
            return
        try:
            self.fdl_loaded_signal.emit(True)
            time.sleep(0.5)
            try:
                if spd.set_blk_size(65535):
                    import logging as _l
                    _l.getLogger(__name__).info('[bin_spd] blk_size=65535 aplicado')
                    time.sleep(0.2)
            except Exception:
                pass
            else:
                self._op_started = True
                self._execute_operation_spd(spd)
                self.log_signal.emit('Rebooting device... Ok', 'success')
                spd.reset_device()
                time.sleep(1)
                self._finish_success()
        except Exception:
            spd.stop()
            raise
        spd.stop()
        if self._sync_temp_paths:
            try:
                from app.views.union_unlock.spd.spd_sync import SpdSync
                SpdSync.limpar_fdls_temp(self._sync_temp_paths)
            except Exception:
                return
    def _execute_operation_spd(self, spd):
        '''
Executa opera├º├úo via SPDDumpProcess.
Interpreta corretamente cada comando da sequencia JSON:
  "e <part>"              ÔåÆ erase_partition
  "w <part> <blob_ref>"   ÔåÆ write_partition (grava imagem na particao)
Fallback: matching por nome (modelos legado do Devices.json).
'''
        op = self.operation.upper()
        mc = self.model_config
        self.log_signal.emit(f'Operacao: {self.operation}', 'op')
        ops_json = getattr(mc, '_ops_json', None)
        sequencia = self._resolve_sequencia(op, ops_json)
        if sequencia:
            brand = getattr(mc, 'brand', '').upper()
            is_force_reset = 'FORCE' in op and 'RESET' in op
            filtered = []
            for cmd in sequencia:
                parts = cmd.strip().split()
                if len(parts) >= 2 and parts[0].lower() == 'e' and parts[1] == 'metadata' and not is_force_reset:
                    self.log_signal.emit('Erase metadata bloqueado por politica de seguranca', 'warning')
                    continue
                if len(parts) >= 2 and parts[0].lower() == 'e' and parts[1] == 'persist':
                    if brand == 'SAMSUNG':
                        continue
                filtered.append(cmd)
            total = len(filtered)
            for i, cmd in enumerate(filtered):
                step = f'[{i + 1}/{total}]' if total > 1 else ''
                self._execute_single_cmd(spd, cmd, step)
            return
        brand = getattr(mc, 'brand', '').upper()
        self.log_signal.emit('Formatting desired partition... ', 'info')
        if brand != 'SAMSUNG':
            spd.erase_partition('persist')
            time.sleep(2)
        spd.erase_partition('persistent')
        time.sleep(2)
        self.log_signal.emit('Formatting desired partition... Ok', 'success')
    def _execute_single_cmd(self, spd, cmd: str, step: str):
        '''
Interpreta e executa um unico comando da sequencia JSON.
Formatos suportados:
  "e <partition>"            ÔåÆ apaga particao
  "w <partition> <blob_ref>" ÔåÆ grava blob na particao
'''
        parts = cmd.strip().split()
        if not parts:
            return
        action = parts[0].lower()
        if action == 'w' and len(parts) >= 3:
            part_name = parts[1]
            blob_ref = parts[2]
            blob_path = self._resolve_blob_path(blob_ref)
            if not blob_path:
                self.log_signal.emit(f'Dados nao encontrados para operacao {step}', 'error')
                raise RuntimeError(f'Dados nao disponiveis para gravacao na etapa {step}')
            self.log_signal.emit(f'Writing desired partition {step}... ', 'info')
            ok = spd.write_partition(part_name, blob_path)
            if not ok:
                self.log_signal.emit(f'Writing desired partition {step}... Falhou', 'error')
                raise RuntimeError(f'Falha ao gravar dados na etapa {step}. Verifique a conexao e tente novamente. Se persistir, esta versao pode nao ser suportada ÔÇö tente o metodo por CPU.')
            self.log_signal.emit(f'Writing desired partition {step}... Ok', 'success')
            return
        if action == 'e' and len(parts) >= 2:
            part_name = parts[1]
            brand = getattr(self.model_config, 'brand', '').upper()
            if part_name == 'persist' and brand == 'SAMSUNG':
                self.log_signal.emit(f'Skipping protected area {step}... Ok', 'info')
                return
            self.log_signal.emit(f'Formatting desired partition {step}... ', 'info')
            ok = spd.erase_partition(part_name)
            if not ok:
                self.log_signal.emit(f'Formatting desired partition {step}... Falhou', 'error')
                raise RuntimeError(f'Falha ao apagar area {step}. Verifique a conexao e tente novamente. Se persistir, esta versao pode nao ser suportada ÔÇö tente o metodo por CPU.')
            self.log_signal.emit(f'Formatting desired partition {step}... Ok', 'success')
            return
        part_name = cmd.replace('e ', '').strip()
        self.log_signal.emit(f'Formatting desired partition {step}... ', 'info')
        ok = spd.erase_partition(part_name)
        if not ok:
            self.log_signal.emit(f'Formatting desired partition {step}... Falhou', 'error')
            raise RuntimeError(f'Falha ao apagar area {step}. Verifique a conexao e tente novamente. Se persistir, esta versao pode nao ser suportada ÔÇö tente o metodo por CPU.')
        self.log_signal.emit(f'Formatting desired partition {step}... Ok', 'success')
    def _resolve_blob_path(self, blob_ref: str) -> str:
        '''
        Resolve referencia de blob para caminho de arquivo no disco.
        Fontes (em ordem de prioridade):
        1. Arquivos temporarios extraidos do cache local (self._sync_temp_paths)
        2. Arquivo previamente disponibilizado no data_dir do modelo
        '''
        temp_paths = getattr(self, '_sync_temp_paths', None)
        blob_map = {'persist_blob': 'persist', 'exploit_blob': 'exploit', 'fdl1_blob': 'fdl1', 'fdl2_blob': 'fdl2'}
        key = blob_map.get(blob_ref)
        if key and temp_paths and key in temp_paths:
            path = temp_paths[key]
            if os.path.isfile(path):
                return path
        mc = self.model_config
        model_dir = getattr(mc, 'data_dir', '') or ''
        if model_dir and os.path.isdir(model_dir) and 'persist' in blob_ref:
            for name in ('persist_clean.img', 'persist.img', 'persist_moto_g35.img'):
                candidate = os.path.join(model_dir, name)
                if not os.path.isfile(candidate):
                    continue
                return candidate
        return ''
    def _resolve_sequencia(self, op_upper, ops_json):
        '''Resolve a sequencia de comandos para a operacao.'''
        if ops_json:
            for key, val in ops_json.items():
                if isinstance(val, dict):
                    label = val.get('label', '').upper()
                    if label == op_upper or label in op_upper:
                        seq = val.get('sequencia', [])
                        if not seq:
                            continue
                    return seq
        if 'FRP ONLY' in op_upper or 'REMOVER FRP' in op_upper:
            return ['e persist', 'e persistent', 'e frp']
        if 'DATA + FRP' in op_upper or 'APAGAR DATA' in op_upper:
            return ['e persist', 'e persistent', 'e frp', 'e userdata']
        if 'FACTORY' in op_upper:
            return ['e persist', 'e persistent', 'e frp', 'e userdata', 'e cache']
        if 'FORMAT SEGURO' in op_upper or 'SAFE FORMAT' in op_upper:
            return ['e userdata', 'e cache']
        if 'FORCE' in op_upper:
            if 'RESET' in op_upper or 'FRP' in op_upper:
                return ['e metadata', 'e cache', 'e persistent', 'e persist', 'e userdata']
    @staticmethod
    def _sanitize_error(msg: str) -> str:
        '''Remove caminhos, nomes internos e dados tecnicos da mensagem.
        Aplicado em toda mensagem antes de ir para a GUI ou terminal.
        Ultimo escudo contra vazamento de arquitetura interna.
        '''
        import re as _re
        msg = _re.sub('[A-Za-z]:\\\\[^\\s"\\\']+', '', msg)
        msg = _re.sub('/[^\\s"\\\']+', '', msg)
        msg = _re.sub('0x[0-9A-Fa-f]+', '', msg)
        msg = _re.sub('\\b\\w+\\.py:?\\d*\\b', '', msg)
        msg = _re.sub('Traceback \\(most recent call last\\):.*', '', msg, flags=_re.DOTALL)
        for token in ('FDL1', 'FDL2', 'fdl1', 'fdl2', 'Auth-1', 'Auth-2', 'spd_dump', 'spd_sync', 'ums9230', 'ums9620', 'UMS9230', 'UMS9620', 'exec_addr', 'loaders_spd', 'partition_ops', 'partition_tab', 'bin_spd', '.bin', '.exe', '.dll', '.pyd', '.py'):
            msg = msg.replace(token, '')
        msg = ' '.join(msg.split())
        if not msg or len(msg) < 5:
            msg = 'Erro na operacao. Verifique o dispositivo e tente novamente.'
        return msg
    def _finish_success(self):
        '''Finaliza com sucesso ÔÇö rodap├® profissional.'''
        elapsed = int(time.time() - getattr(self, '_start_time', time.time()))
        self.log_signal.emit('', 'info')
        self.log_signal.emit('ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ', 'footer_line')
        self.log_signal.emit('TECH UNION SOLUTIONS v1.3.4.1', 'footer_title')
        self.log_signal.emit(f'Elapsed Time : {elapsed} seconds', 'footer_time')
        self.status_signal.emit('Conclu├¡do com sucesso!')
        self.finished_signal.emit(True, 'Opera├º├úo conclu├¡da')
    def _finish_error(self, message: str):
        '''Finaliza com erro ÔÇö rodap├® profissional.'''
        elapsed = int(time.time() - getattr(self, '_start_time', time.time()))
        self.log_signal.emit(f'Falha: {message}', 'error')
        self.log_signal.emit('', 'info')
        self.log_signal.emit('ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ', 'footer_line')
        self.log_signal.emit('TECH UNION SOLUTIONS v1.3.4.1', 'footer_title')
        self.log_signal.emit(f'Elapsed Time : {elapsed} seconds', 'footer_time')
        self.status_signal.emit(f'Erro: {message}')
        self.finished_signal.emit(False, message)
    def _on_progress(self, sent: int, total: int):
        '''Callback de progresso.'''
        self.progress_signal.emit(sent, total)
