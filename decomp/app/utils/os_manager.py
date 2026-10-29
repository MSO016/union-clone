'''
Union OS Manager - Gerenciador de Servi├ºo Web
==============================================
Gerencia a execu├º├úo do Union OS Manager como servi├ºo Flask integrado ao
Tech Union Solutions. Suporta modo local e modo servidor de rede.
AUTOR: RESTORECELL - TECH UNION SOLUTIONS
DATA: 2025-12-25
VERS├âO: 1.0
ARQUITETURA:
- Servidor Flask roda em thread separada (daemon)
- Suporta modo local (127.0.0.1) e modo rede (0.0.0.0)
- N├úo exp├Áe estruturas internas em mensagens de erro
- Compat├¡vel com desenvolvimento e produ├º├úo (compilado)
MODOS DE OPERA├ç├âO:
- LOCAL: Apenas acess├¡vel na m├íquina (127.0.0.1:5000)
- REDE: Acess├¡vel por outros hosts na rede (0.0.0.0:5000)
SEGURAN├çA:
- Mensagens de erro gen├®ricas (n├úo revelam caminhos/estruturas)
- Logs t├®cnicos apenas em console de desenvolvimento
- Valida├º├úo de porta antes de iniciar
'''
import os
import sys
import socket
import threading
import time
import logging
import hmac
import hashlib
from typing import (Optional, Tuple, Dict, Any)
from enum import Enum
class ModoServidor(Enum):
    '''Modos de opera├º├úo do servidor'''
    LOCAL = 'local'
    REDE = 'rede'
class UnionOSManager:
    '''
    Gerenciador do servidor Union OS Manager.
    Responsabilidades:
    - Iniciar/parar servidor Flask em thread separada
    - Gerenciar modos de opera├º├úo (local/rede)
    - Verificar disponibilidade e status
    - Fornecer URLs de acesso
    Seguran├ºa:
    - Mensagens de erro n├úo revelam estruturas internas
    - Logs t├®cnicos apenas em DEBUG
    '''
    PORTA_PADRAO: int = 5000
    TIMEOUT_INICIALIZACAO: int = 10
    TIMEOUT_INICIALIZACAO_ESTENDIDO: int = 30
    _OS_BUNDLE_ARQUIVO = 'union_os_runtime.zip'
    _OS_RUNTIME_SUBDIR = 'os_runtime'
    def __init__(self):
        '''Inicializa o gerenciador com valores padr├úo'''
        self._logger = logging.getLogger('UnionOSManager')
        self._server_thread = None
        self._server_process = None
        self._is_running = False
        self._modo_atual = ModoServidor.LOCAL
        self._porta = self.PORTA_PADRAO
        self._using_embeddable_runtime = False
        self._last_provision_failure = None
        self._python_sistema_compat_cache = None
        self._os_path = self._determinar_caminho()
    @property
    def porta(self) -> int:
        '''Porta do servidor'''
        return self._porta
    @property
    def modo(self) -> ModoServidor:
        '''Modo atual de opera├º├úo'''
        return self._modo_atual
    @property
    def host(self) -> str:
        '''Host baseado no modo atual'''
        return '0.0.0.0' if self._modo_atual == ModoServidor.REDE else '127.0.0.1'
    @property
    def url_local(self) -> str:
        '''URL para acesso local'''
        return f'http://127.0.0.1:{self._porta}'
    @property
    def url_rede(self) -> str:
        '''URL para acesso na rede (IP da m├íquina)'''
        ip = self._obter_ip_local()
        return f'http://{ip}:{self._porta}'
    def _determinar_caminho(self) -> str:
        '''
Determina o caminho do Union OS Manager baseado no ambiente.
Returns:
    str: Caminho para o diret├│rio do Union OS Manager
'''
        try:
            try:
                from app.utils.path_manager import PathManager
                pm_dir = PathManager.get_os_manager_dir()
                if pm_dir and os.path.isdir(pm_dir):
                    caminhos = [pm_dir]
                else:
                    caminhos = []
            except Exception:
                caminhos = []
        except Exception as e:
            self._log_debug(f'Erro ao determinar caminho: {e}')
            return ''
        if not caminhos:
            if getattr(sys, 'frozen', False):
                base = os.path.dirname(sys.executable)
                caminhos = [os.path.join(base, '_internal', 'app', 'views', 'ordem_servico'), os.path.join(base, 'app', 'views', 'ordem_servico')]
            else:
                current = os.path.dirname(os.path.abspath(__file__))
                app_dir = os.path.dirname(current)
                caminhos = [os.path.join(app_dir, 'views', 'ordem_servico')]
        for caminho in caminhos:
            if not os.path.exists(caminho):
                continue
            try:
                pass
            except Exception as e:
                self._log_debug(f'Erro ao determinar caminho: {e}')
                return ''
            if not os.path.isdir(caminho):
                continue
            try:
                app_init_py = os.path.join(caminho, 'app', '__init__.py')
                app_init_pyc = os.path.join(caminho, 'app', '__init__.pyc')
                app_pycache = os.path.join(caminho, 'app', '__pycache__')
                has_module = os.path.exists(app_init_py) or os.path.exists(app_init_pyc) or os.path.exists(app_pycache) and os.path.isdir(app_pycache)
            except Exception as e:
                self._log_debug(f'Erro ao determinar caminho: {e}')
                return ''
            if not has_module:
                continue
            try:
                self._log_debug('M├│dulo encontrado: [path-hidden]')
                return caminho
                self._log_debug('M├│dulo n├úo encontrado nos caminhos esperados')
                if not caminhos:
                    break
                return caminhos[0]
            except Exception as e:
                self._log_debug(f'Erro ao determinar caminho: {e}')
                return ''
        return ''
    def _obter_ip_local(self) -> str:
        '''
Obt├®m o IP local da m├íquina na rede local (Wi-Fi/Ethernet).
Filtra interfaces VPN (Radmin, Hamachi, etc) para pegar IP real.
Returns:
    str: IP da rede local (192.168.x.x, 10.x.x.x) ou 127.0.0.1
'''
        try:
            import subprocess
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            output = result.stdout
            vpn_keywords = ['radmin', 'hamachi', 'vpn', 'virtual', 'vmware', 'vbox']
            current_adapter = ''
            found_ips = []
            for line in output.split('\n'):
                line_lower = line.lower()
                if 'adaptador' in line_lower or 'adapter' in line_lower:
                    current_adapter = line_lower
                    continue
                is_vpn = any((kw in current_adapter for kw in vpn_keywords))
                if is_vpn:
                    continue
                if 'ipv4' not in line_lower and 'endere├ºo ipv4' not in line_lower:
                    continue
                parts = line.split(':')
                if not len(parts) >= 2:
                    continue
                ip = parts[-1].strip()
                if ip.count('.') != 3:
                    continue
                if ip.startswith('192.168.') or ip.startswith('10.'):
                    return ip
                if ip.startswith('172.'):
                    octets = ip.split('.')
                    if 16 <= int(octets[1]) <= 31:
                        return int(octets[1])
                found_ips.append(ip)
                continue
            if found_ips:
                return found_ips[0]
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.1)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return '127.0.0.1'
    def _log_debug(self, mensagem: str):
        '''Log interno - apenas em modo DEBUG, n├úo exp├Áe ao usu├írio'''
        self._logger.debug(f'[OS-Manager] {mensagem}')
        if not getattr(sys, 'frozen', False):
            print(f'[DEBUG OS-Manager] {mensagem}')
    def _ler_erro_servidor(self) -> str:
        '''L├¬ as ├║ltimas linhas do stderr log para diagn├│stico de falhas.'''
        try:
            self._fechar_stderr_log()
            log_path = getattr(self, '_stderr_log_path', None)
            if log_path and os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    linhas = f.readlines()
                if linhas:
                    return ''.join(linhas[-20:]).strip()
                return ''
        except Exception:
            pass
        return ''
    def _fechar_stderr_log(self):
        '''Fecha o arquivo de stderr log de forma segura.'''
        try:
            stderr_file = getattr(self, '_stderr_file', None)
            if stderr_file and not stderr_file.closed:
                stderr_file.close()
            self._stderr_file = None
            return
        except Exception:
            return
    def _detectar_peliculas_cache(self) -> str:
        '''
Detecta se o cache de pel├¡culas existe e retorna o caminho absoluto.
O cache ├® criado pelo m├│dulo peliculas do app principal ao sincronizar.
Returns:
    str: Caminho absoluto do pc_data.db ou string vazia se n├úo existir
'''
        try:
            app_dir = os.path.dirname(self._os_path)
            peliculas_cache = os.path.join(app_dir, 'peliculas', 'cache_local', 'pc_data.db')
            if os.path.isfile(peliculas_cache):
                return os.path.abspath(peliculas_cache)
        except Exception:
            pass
        return ''
    _AUTH_SECRET = b'TUS_OS_INTEGRATED_2025'
    def _gerar_token_auth(self) -> str:
        '''
        Gera token HMAC-SHA256 para autentica├º├úo do subprocess.
        Garante que o servidor s├│ inicia quando chamado pelo app principal.
        '''
        try:
            pid_pai = str(os.getpid())
            timestamp = str(int(time.time()))
            payload = f'{pid_pai}:{timestamp}'.encode('utf-8')
            token = hmac.new(self._AUTH_SECRET, payload, hashlib.sha256).hexdigest()
            return f'{pid_pai}:{timestamp}:{token}'
        except Exception:
            return ''
    def verificar_porta_disponivel(self, porta: Optional[int]=None) -> bool:
        '''
Verifica se uma porta est├í dispon├¡vel para uso.
Args:
    porta: Porta a verificar (usa padr├úo se None)
Returns:
    bool: True se a porta est├í livre
'''
        porta = porta or self._porta
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('127.0.0.1', porta))
        except OSError:
            return False
        return True
    def verificar_servidor_respondendo(self, timeout: float=1.0) -> bool:
        '''
Verifica se o servidor est├í respondendo na porta.
Args:
    timeout: Tempo m├íximo de espera em segundos
Returns:
    bool: True se o servidor responde
'''
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                result = s.connect_ex(('127.0.0.1', self._porta))
                return result == 0
        except Exception:
            return False
    def esta_rodando(self) -> bool:
        '''
Verifica se o servidor est├í em execu├º├úo.
Returns:
    bool: True se est├í rodando
'''
        if self._is_running:
            return self.verificar_servidor_respondendo()
        return False
    def verificar_disponibilidade(self) -> Tuple[bool, str]:
        '''
Verifica se o m├│dulo est├í dispon├¡vel para uso.
IMPORTANTE: Funciona tanto em desenvolvimento (.py) quanto
compilado (.pyc), verificando arquivos de ambos os tipos.
Returns:
    Tuple[bool, str]: (dispon├¡vel, mensagem_amigavel)
Nota:
    Mensagens s├úo gen├®ricas por seguran├ºa
'''
        if not self._os_path or not os.path.exists(self._os_path):
            self._log_debug('Diret├│rio do m├│dulo n├úo encontrado')
            return (False, 'ÔÜá´©Å M├│dulo de Ordens de Servi├ºo n├úo encontrado.\n\n­ƒôï Poss├¡veis causas:\nÔÇó Instala├º├úo incompleta\nÔÇó Arquivos corrompidos\n\n­ƒÆí Solu├º├úo:\nÔÇó Reinstale o TECH UNION SOLUTIONS\nÔÇó Entre em contato com o suporte')
        app_init_py = os.path.join(self._os_path, 'app', '__init__.py')
        app_init_pyc = os.path.join(self._os_path, 'app', '__init__.pyc')
        app_pycache = os.path.join(self._os_path, 'app', '__pycache__')
        has_pycache = os.path.exists(app_pycache) and any((f.endswith('.pyc') for f in os.listdir(app_pycache) if os.path.isfile(os.path.join(app_pycache, f)) or f.startswith('__init__'))) if os.path.exists(app_pycache) else False
        if not os.path.exists(app_init_py) and not os.path.exists(app_init_pyc) and not has_pycache:
            self._log_debug('Estrutura do m├│dulo incompleta')
            return (False, 'ÔÜá´©Å M├│dulo de Ordens de Servi├ºo corrompido.\n\n­ƒÆí Solu├º├úo:\nÔÇó Reinstale o TECH UNION SOLUTIONS\nÔÇó Verifique a integridade dos arquivos')
        app_dir = os.path.join(self._os_path, 'app')
        if not os.path.isdir(app_dir):
            self._log_debug('Diret├│rio app n├úo encontrado')
            return (False, 'ÔÜá´©Å M├│dulo de Ordens de Servi├ºo corrompido.\n\n­ƒÆí Solu├º├úo:\nÔÇó Reinstale o TECH UNION SOLUTIONS')
        self._log_debug('M├│dulo verificado e dispon├¡vel')
        return (True, 'Ô£à Sistema de O.S. pronto para uso')
    def iniciar(self, modo: ModoServidor=ModoServidor.LOCAL) -> Tuple[bool, str]:
        '''
Inicia o servidor Union OS Manager.
Args:
    modo: Modo de opera├º├úo (LOCAL ou REDE)
Returns:
    Tuple[bool, str]: (sucesso, mensagem_amigavel)
'''
        if self.esta_rodando():
            url = self.url_rede if self._modo_atual == ModoServidor.REDE else self.url_local
            return True, f'Ô£à Sistema j├í est├í em execu├º├úo\n\n­ƒöù Acesse: {url}'
        disponivel, msg = self.verificar_disponibilidade()
        if not disponivel:
            return False, msg
        if not self.verificar_porta_disponivel():
            porta_alternativa = self._porta + 1
            if self.verificar_porta_disponivel(porta_alternativa):
                self._log_debug(f'Porta {self._porta} em uso, usando alternativa {porta_alternativa}')
                self._porta = porta_alternativa
            else:
                self._matar_processos_porta(self._porta)
                time.sleep(1)
                if not self.verificar_porta_disponivel():
                    return False, f'ÔÜá´©Å A porta {self._porta} est├í em uso.\n\n­ƒôï Poss├¡veis causas:\nÔÇó Outra inst├óncia do sistema est├í ativa\nÔÇó Outro programa est├í usando a porta\n\n­ƒÆí Solu├º├Áes:\nÔÇó Feche outros programas na porta\nÔÇó Reinicie o TECH UNION SOLUTIONS'
        self._modo_atual = modo
        try:
            self._server_thread = threading.Thread(target=self._executar_servidor, name='UnionOS-Server', daemon=True)
            self._server_thread.start()
            self._is_running = True
            timeout_init = self.TIMEOUT_INICIALIZACAO_ESTENDIDO if self._using_embeddable_runtime else self.TIMEOUT_INICIALIZACAO
            inicio = time.time()
            while time.time() - inicio < timeout_init:
                if self._server_process and self._server_process.poll() is not None:
                    exit_code = self._server_process.returncode
                    erro_detalhes = self._ler_erro_servidor()
                    self._log_debug(f'Servidor encerrou prematuramente (c├│digo: {exit_code})')
                    if erro_detalhes:
                        self._log_debug(f'Detalhes: {erro_detalhes}')
                    self._is_running = False
                    self._server_process = None
                    self._fechar_stderr_log()
                    return (False, 'ÔÜá´©Å O servidor encerrou inesperadamente.\n\n­ƒôï Poss├¡veis causas:\nÔÇó Erro na inicializa├º├úo do banco de dados\nÔÇó Depend├¬ncia faltando no sistema\nÔÇó Conflito de porta\n\n­ƒÆí Solu├º├Áes:\nÔÇó Tente novamente\nÔÇó Reinicie o TECH UNION SOLUTIONS\nÔÇó Entre em contato com o suporte')
                if self.verificar_servidor_respondendo():
                    url = self.url_rede if modo == ModoServidor.REDE else self.url_local
                    if modo == ModoServidor.REDE:
                        return True, f'Ô£à Sistema iniciado em Modo Servidor!\n\n­ƒîÉ Acesso Local: {self.url_local}\n­ƒîÉ Acesso na Rede: {self.url_rede}\n\n­ƒô▒ Outros dispositivos na rede podem acessar\nusando o endere├ºo de rede acima.'
                    return True, f'Ô£à Sistema iniciado com sucesso!\n\n­ƒöù Acesse: {url}'
                time.sleep(0.5)
            if self._server_process and self._server_process.poll() is not None:
                erro_detalhes = self._ler_erro_servidor()
                if erro_detalhes:
                    self._log_debug(f'Erro no servidor: {erro_detalhes}')
                self._is_running = False
                self._server_process = None
                self._fechar_stderr_log()
                return (False, 'ÔÜá´©Å O servidor n├úo conseguiu iniciar.\n\n­ƒÆí Solu├º├Áes:\nÔÇó Tente novamente em alguns segundos\nÔÇó Reinicie o TECH UNION SOLUTIONS')
            self._log_debug('Timeout aguardando servidor, mas processo est├í ativo')
            return (True, 'ÔÅ│ Sistema iniciando...\n\nO servidor est├í sendo preparado.\nAguarde alguns segundos e tente novamente.')
        except Exception as e:
            self._log_debug(f'Erro ao iniciar servidor: {e}')
            self._is_running = False
            self._fechar_stderr_log()
            return (False, 'ÔÜá´©Å Erro ao iniciar o sistema.\n\n­ƒÆí Solu├º├Áes:\nÔÇó Tente novamente em alguns segundos\nÔÇó Reinicie o TECH UNION SOLUTIONS\nÔÇó Entre em contato com o suporte')
    def iniciar_modo_rede(self) -> Tuple[bool, str]:
        '''
Atalho para iniciar em modo rede (acess├¡vel por outros hosts).
Returns:
    Tuple[bool, str]: (sucesso, mensagem_amigavel)
'''
        return self.iniciar(modo=ModoServidor.REDE)
    def _obter_python_embeddable(self, progress_callback=None) -> Optional[str]:
        '''
Provisiona um runtime Python isolado para o servidor.
Estrategia em camadas:
  1. Reuso do runtime ja preparado (cache local validado por hash)
  2. Reuso do pacote ja transferido (validado por hash)
  3. Aquisicao do pacote via canal primario (cliente seguro)
  4. Aquisicao via canal secundario (fallback)
progress_callback opcional: callable(percent: int, message: str)
recebe atualizacoes durante download e materializacao.
Returns:
    str  : caminho do interpretador pronto para uso
    None : nao foi possivel provisionar (chamador faz fallback)
'''
        def _emit(pct, msg):
            if callable(progress_callback):
                try:
                    progress_callback(int(pct), str(msg))
                    return
                except Exception:
                    pass
        try:
            from app.utils._res_loader import (_cache_dir, _sha256, _download_r2, _download_http, consultar_catalogo)
            from app.utils._app_cfg import REFS
        except Exception:
            self._log_debug('RT:imports indisponiveis')
        self._last_provision_failure = None
        try:
            base = _cache_dir()
            pkg = os.path.join(base, self._OS_BUNDLE_ARQUIVO)
            rt = os.path.join(base, self._OS_RUNTIME_SUBDIR)
            marker = os.path.join(rt, '.runtime.sha')
            interp = os.path.join(rt, 'python.exe')
            _emit(2, 'Verificando recursos...')
            cat = consultar_catalogo(self._OS_BUNDLE_ARQUIVO) or {}
            ref_hash = (cat.get('sha256') or '').strip()
            alt = (cat.get('url') or '').strip()
            if not cat:
                self._log_debug('RT:catalog miss ÔÇö best effort')
                self._last_provision_failure = 'catalog'
            if ref_hash and os.path.isfile(interp) and os.path.isfile(marker):
                pass
            try:
                with open(marker, 'r', encoding='utf-8') as f:
                    if f.read().strip() == ref_hash:
                        self._log_debug('RT:hit')
                        self._last_provision_failure = None
                        _emit(100, 'Pronto!')
                        return interp
            except Exception:
                pass
            else:
                need_fetch = True
                if os.path.isfile(pkg) and ref_hash:
                    _emit(5, 'Verificando integridade do cache...')
        except Exception as exc_top:
            self._log_debug(f'RT:unexpected {type(exc_top).__name__}')
            self._last_provision_failure = 'unknown'
        if need_fetch:
            self._log_debug('RT:fetch primary')
            _emit(8, 'Iniciando download...')
            def _dl_cb(pct, msg):
                mapped = 8 + int(pct * 0.7)
                _emit(mapped, msg)
            try:
                ok_primary = _download_r2(self._OS_BUNDLE_ARQUIVO, pkg, progress_callback=_dl_cb)
            except TypeError:
                self._log_debug('RT:loader legacy')
                try:
                    ok_primary = _download_r2(self._OS_BUNDLE_ARQUIVO, pkg)
                except Exception as exc_legacy:
                    self._log_debug(f'RT:loader legacy fail {type(exc_legacy).__name__}')
                    ok_primary = False
            if not ok_primary:
                self._log_debug('RT:primary fail')
                self._last_provision_failure = 'r2_down'
                _emit(8, 'Tentando canal alternativo...')
                try:
                    if alt:
                        try:
                            try:
                                ok_secondary = bool(_download_http(alt, pkg, progress_callback=_dl_cb))
                            except TypeError:
                                self._log_debug('RT:http loader legacy')
                                ok_secondary = bool(_download_http(alt, pkg))
                        except Exception as exc_secondary:
                            self._log_debug(f'RT:secondary exc {type(exc_secondary).__name__}')
                            ok_secondary = False
                    else:
                        ok_secondary = False
                except Exception as exc_secondary:
                    self._log_debug(f'RT:secondary exc {type(exc_secondary).__name__}')
                    ok_secondary = False
                if ok_secondary:
                    self._log_debug('RT:secondary ok')
                    self._last_provision_failure = None
                    _emit(78, 'Download alternativo concluido')
                else:
                    self._log_debug('RT:fetch failed')
                    return
            try:
                if ref_hash:
                    _emit(80, 'Verificando autenticidade...')
                try:
                    if _sha256(pkg) != ref_hash:
                        self._log_debug('RT:integrity fail')
                        self._last_provision_failure = 'integrity'
                except Exception:
                    self._last_provision_failure = 'integrity'
                else:
                    try:
                        try:
                            os.remove(pkg)
                        except Exception:
                            pass
                    except Exception:
                        self._last_provision_failure = 'integrity'
                    return
            except Exception as exc_top:
                self._log_debug(f'RT:unexpected {type(exc_top).__name__}')
                self._last_provision_failure = 'unknown'
        try:
            import pyzipper
            import shutil as _sh
            import ctypes
            _emit(82, 'Preparando recursos...')
            if os.path.isdir(rt):
                _sh.rmtree(rt, ignore_errors=True)
            os.makedirs(rt, exist_ok=True)
            if sys.platform == 'win32':
                pass
            try:
                ctypes.windll.kernel32.SetFileAttributesW(rt, 8198)
            except Exception:
                pass
            else:
                erros_materializacao = []
                _MAX_ERROS_TOLERADOS = 50
                _MAX_ERROS_LOG = 10
        except Exception as exc_outer:
            self._log_debug(f'RT:materialize unexpected {type(exc_outer).__name__}')
            self._last_provision_failure = 'unknown'
            try:
                import shutil as _sh2
                _sh2.rmtree(rt, ignore_errors=True)
            except Exception:
                pass
        try:
            with pyzipper.AESZipFile(pkg, 'r') as zf:
                zf.setpassword(REFS.PK_Z)
                nomes = zf.namelist()
                n = len(nomes) or 1
                for i, nome in enumerate(nomes):
                    try:
                        try:
                            zf.extract(nome, rt)
                        except Exception as exc_item:
                            erros_materializacao.append(type(exc_item).__name__)
                            if len(erros_materializacao) > _MAX_ERROS_TOLERADOS:
                                self._log_debug(f'RT:materialize abort errs={len(erros_materializacao)}')
                    finally:
                        pass
                    if i % max(1, n // 30) == 0:
                        pct_extracao = (i + 1) / n
                        mapped = 82 + int(pct_extracao * 16)
                        _emit(mapped, f'Preparando ambiente... ({i + 1}/{n})')
        except RuntimeError:
            self._log_debug('RT:auth fail')
            self._last_provision_failure = 'auth'
            _sh.rmtree(rt, ignore_errors=True)
            try:
                os.remove(pkg)
            except Exception:
                pass
            return
        try:
            pass
        except RuntimeError:
            self._log_debug('RT:auth fail')
            self._last_provision_failure = 'auth'
            _sh.rmtree(rt, ignore_errors=True)
            try:
                os.remove(pkg)
            except Exception:
                pass
            return
        if erros_materializacao:
            amostra = erros_materializacao[:_MAX_ERROS_LOG]
            self._log_debug(f'RT:materialize partial errs={len(erros_materializacao)} sample={amostra}')
            self._last_provision_failure = 'partial'
            _sh.rmtree(rt, ignore_errors=True)
            return
        try:
            if not os.path.isfile(interp):
                self._log_debug('RT:materialize fail (interp missing)')
                self._last_provision_failure = 'partial'
                _sh.rmtree(rt, ignore_errors=True)
                return
        except Exception as exc_outer:
            self._log_debug(f'RT:materialize unexpected {type(exc_outer).__name__}')
            self._last_provision_failure = 'unknown'
            try:
                import shutil as _sh2
                _sh2.rmtree(rt, ignore_errors=True)
            except Exception:
                pass
        try:
            qtde_arquivos = sum((1 for _ in os.scandir(rt) if _.is_file() or _.is_dir()))
        except Exception:
            qtde_arquivos = 1
        if qtde_arquivos < 2:
            self._log_debug('RT:materialize sparse')
            self._last_provision_failure = 'partial'
            _sh.rmtree(rt, ignore_errors=True)
            return
        try:
            if ref_hash:
                pass
            try:
                with open(marker, 'w', encoding='utf-8') as f:
                    f.write(ref_hash)
            except Exception as exc_marker:
                self._log_debug(f'RT:marker fail {type(exc_marker).__name__}')
                self._last_provision_failure = 'disk'
                _sh.rmtree(rt, ignore_errors=True)
            else:
                self._log_debug('RT:ready')
                self._last_provision_failure = None
                _emit(100, 'Pronto!')
        except Exception as exc_outer:
            self._log_debug(f'RT:materialize unexpected {type(exc_outer).__name__}')
            self._last_provision_failure = 'unknown'
            try:
                import shutil as _sh2
                _sh2.rmtree(rt, ignore_errors=True)
            except Exception:
                pass
        return interp
    def precisa_provisionar_runtime(self) -> bool:
        '''
Indica se o runtime externo precisa ser provisionado/atualizado
antes de iniciar o servidor.
Retorna False quando:
  - Em desenvolvimento (usa Python local)
  - Em producao com Python ja instalado no sistema (fallback OK)
  - Em producao com runtime ja em cache valido
Retorna True quando:
  - Em producao + Python sistema ausente + cache vazio/invalido
    (ai precisa baixar antes de iniciar, com feedback visual)
'''
        if not getattr(sys, 'frozen', False):
            return False
        try:
            import shutil as _sh
            if _sh.which('python') or _sh.which('python3'):
                pass
        except Exception:
            pass
        try:
            from app.utils._res_loader import _cache_dir, consultar_catalogo
            cache = _cache_dir()
            interp = os.path.join(cache, self._OS_RUNTIME_SUBDIR, 'python.exe')
            marker = os.path.join(cache, self._OS_RUNTIME_SUBDIR, '.runtime.sha')
            if not (os.path.isfile(interp) and os.path.isfile(marker)):
                return True
            cat = consultar_catalogo(self._OS_BUNDLE_ARQUIVO)
            if not cat:
                return False
            ref = (cat.get('sha256') or '').strip()
            if not ref:
                return False
            with open(marker, 'r', encoding='utf-8') as f:
                cached = f.read().strip()
        except Exception:
            return False
        return cached != ref
    def provisionar_runtime(self, progress_callback=None) -> Tuple[bool, str]:
        '''
Provisiona o runtime externo de forma SINCRONA com feedback de progresso.
Deve ser chamado pela UI ANTES de iniciar() quando precisa_provisionar_runtime()
retornar True. Use uma QThread para nao travar a UI.
progress_callback: callable(percent: int, message: str) ÔÇö opcional.
Returns:
    Tuple[bool, str]: (sucesso, mensagem amigavel diferenciada por motivo)
'''
        try:
            interp = self._obter_python_embeddable(progress_callback=progress_callback)
            if interp and os.path.isfile(interp):
                return (True, 'Ô£à Recursos preparados com sucesso')
            return False, self._mensagem_falha_provisionamento(self._last_provision_failure)
        except Exception as exc_provision:
            self._log_debug(f'provisionar_runtime: {type(exc_provision).__name__}')
            self._last_provision_failure = 'unknown'
            return (False, 'ÔÜá´©Å Erro inesperado ao preparar o sistema.\n\n­ƒÆí Tente novamente ou contate o suporte.')
    def _mensagem_falha_provisionamento(self, motivo: Optional[str]) -> str:
        '''Retorna mensagem amigavel diferenciada para o usuario final.
        Mensagens evitam termos tecnicos (paths, exceptions, hashes) e
        oferecem orientacao acionavel. Quando ``motivo`` e desconhecido,
        retorna a mensagem generica anterior (compat retro).
        Adicionalmente, quando o detector passivo (C1 conservador)
        identificou um Python compativel no sistema, anexa uma dica
        amigavel ao usuario indicando que o sistema pode tentar abrir
        novamente ÔÇö o ``_executar_servidor`` ja faz fallback automatico
        para esse Python sem novo download.
        '''
        base = {'catalog': 'ÔÜá´©Å Servidor de cat├ílogo temporariamente indispon├¡vel.\n\n­ƒÆí Solu├º├Áes:\nÔÇó Verifique sua conex├úo\nÔÇó Tente novamente em alguns minutos\nÔÇó Se persistir, contate o suporte', 'r2_down': 'ÔÜá´©Å Servidor de download temporariamente indispon├¡vel.\n\n­ƒÆí Solu├º├Áes:\nÔÇó Verifique sua conex├úo com a internet\nÔÇó Tente novamente em alguns minutos\nÔÇó Se persistir, contate o suporte', 'integrity': 'ÔÜá´©Å Falha na verifica├º├úo de integridade.\n\n­ƒÆí Solu├º├Áes:\nÔÇó Tente novamente em alguns segundos\nÔÇó Verifique seu antiv├¡rus\nÔÇó Se persistir, contate o suporte', 'auth': 'ÔÜá´©Å Falha na verifica├º├úo de seguran├ºa.\n\n­ƒÆí Solu├º├Áes:\nÔÇó Reinstale o programa\nÔÇó Contate o suporte se persistir', 'corrupt': 'ÔÜá´©Å Arquivo de recursos corrompido.\n\n­ƒÆí Solu├º├Áes:\nÔÇó Verifique seu antiv├¡rus\nÔÇó Tente novamente em alguns minutos\nÔÇó Se persistir, contate o suporte', 'partial': 'ÔÜá´©Å Falha ao preparar arquivos do sistema.\n\n­ƒÆí Solu├º├Áes:\nÔÇó Verifique seu antiv├¡rus (pode ter removido arquivos)\nÔÇó Verifique espa├ºo em disco\nÔÇó Tente novamente em alguns minutos', 'disk': 'ÔÜá´©Å Falha ao salvar arquivos no computador.\n\n­ƒÆí Solu├º├Áes:\nÔÇó Verifique espa├ºo em disco\nÔÇó Verifique permiss├Áes da pasta de instala├º├úo\nÔÇó Execute como Administrador se persistir'}
        msg = base.get(motivo or 'unknown', 'ÔÜá´©Å N├úo foi poss├¡vel preparar o sistema.\n\n­ƒôï Poss├¡veis causas:\nÔÇó Sem conex├úo com a internet (primeiro uso)\nÔÇó Servidor temporariamente indispon├¡vel\n\n­ƒÆí Solu├º├Áes:\nÔÇó Verifique sua conex├úo\nÔÇó Tente novamente em alguns minutos\nÔÇó Se persistir, contate o suporte')
        try:
            py_compat = self._detectar_python_sistema_compativel()
            if py_compat:
                msg = f'{msg}\n\nÔä╣´©Å Foi detectado um Python compat├¡vel instalado.\nVoc├¬ pode tentar abrir novamente ÔÇö o sistema usa\nautomaticamente o Python instalado quando dispon├¡vel.'
        except Exception:
            pass
        return msg
    def _detectar_python_sistema_compativel(self) -> Optional[str]:
        '''Detecta Python instalado no sistema com modulos do OS Manager.
Versao CONSERVADORA (PR3 ÔÇö C1):
    - Apenas DIAGNOSTICO PASSIVO. Nao altera precisa_provisionar_runtime.
    - Resultado e cacheado por instancia (executa subprocess uma vez).
    - Usado em mensagens de erro para informar o usuario que existe
      alternativa ja disponivel ÔÇö o _executar_servidor ja faz o
      fallback automatico de interpretador (linhas 1009+).
Returns:
    str  : caminho do python.exe quando os modulos estao disponiveis;
    None : sistema nao tem Python compativel (ou subprocess falhou).
'''
        if self._python_sistema_compat_cache is not None:
            return self._python_sistema_compat_cache or None
        try:
            import shutil as _sh
            import subprocess as _sp
            py = _sh.which('python') or _sh.which('python3')
            if not py:
                candidatos = ['C:\\Python311\\python.exe', 'C:\\Python312\\python.exe', 'C:\\Python313\\python.exe', 'C:\\Program Files\\Python311\\python.exe', 'C:\\Program Files\\Python312\\python.exe', 'C:\\Program Files\\Python313\\python.exe', os.path.expandvars('%LOCALAPPDATA%\\Programs\\Python\\Python311\\python.exe'), os.path.expandvars('%LOCALAPPDATA%\\Programs\\Python\\Python312\\python.exe'), os.path.expandvars('%LOCALAPPDATA%\\Programs\\Python\\Python313\\python.exe')]
                for path in candidatos:
                    if not os.path.isfile(path):
                        continue
                    py = path
                    break
            if not py:
                self._python_sistema_compat_cache = ''
                return
            probe_script = 'import flask, waitress; print("OK")'
            creation_flags = 0
            if sys.platform == 'win32':
                creation_flags = _sp.CREATE_NO_WINDOW
            result = _sp.run([py, '-c', probe_script], capture_output=True, text=True, timeout=3, creationflags=creation_flags)
            if result.returncode == 0:
                if 'OK' in (result.stdout or ''):
                    self._python_sistema_compat_cache = py
                    self._log_debug('rt:python_sistema_compat ok')
                    return py
            self._log_debug('rt:python_sistema_compat fail')
            self._python_sistema_compat_cache = ''
            return
        except Exception as exc:
            self._log_debug(f'rt:python_sistema_compat exc {type(exc).__name__}')
            self._python_sistema_compat_cache = ''
    def _executar_servidor(self):
        '''
Executa o servidor em subprocess isolado (sem console visivel).
Caracteristicas:
  - Tolera scripts em formato fonte ou bytecode
  - Captura stderr em log para diagnostico de falhas silenciosas
  - Resolve interpretador apropriado segundo o ambiente
Uso interno apenas ÔÇö chamar via iniciar().
'''
        import subprocess
        import shutil
        try:
            self._log_debug(f'Iniciando servidor em {self.host}:{self._porta}')
            log_dir = os.path.join(self._os_path, 'logs')
            os.makedirs(log_dir, exist_ok=True)
            self._stderr_log_path = os.path.join(log_dir, 'server_stderr.log')
            try:
                self._stderr_file = open(self._stderr_log_path, 'w', encoding='utf-8')
            except Exception:
                self._stderr_file = None
            else:
                run_script = self._determinar_script_run()
                if not run_script or not os.path.exists(run_script):
                    self._log_debug('Script de inicializa├º├úo n├úo encontrado')
                    self._is_running = False
                    return
                formato = 'BYTECODE (.pyc)' if run_script.endswith('.pyc') else 'SCRIPT (.py)'
                self._log_debug(f'Script encontrado ({formato}): [path-hidden]')
                python_executable = sys.executable
                self._using_embeddable_runtime = False
                if getattr(sys, 'frozen', False):
                    py_emb = self._obter_python_embeddable()
                    if py_emb and os.path.isfile(py_emb):
                        python_executable = py_emb
                        self._using_embeddable_runtime = True
                        self._log_debug('interp:isolated')
                    else:
                        system_python = shutil.which('python') or shutil.which('python3')
                        if system_python:
                            python_executable = system_python
                            self._log_debug('interp:system PATH')
                        else:
                            common_paths = ['C:\\Python39\\python.exe', 'C:\\Python310\\python.exe', 'C:\\Python311\\python.exe', 'C:\\Python312\\python.exe', 'C:\\Python313\\python.exe', 'C:\\Program Files\\Python39\\python.exe', 'C:\\Program Files\\Python310\\python.exe', 'C:\\Program Files\\Python311\\python.exe', 'C:\\Program Files\\Python312\\python.exe', 'C:\\Program Files\\Python313\\python.exe', os.path.expandvars('%LOCALAPPDATA%\\Programs\\Python\\Python39\\python.exe'), os.path.expandvars('%LOCALAPPDATA%\\Programs\\Python\\Python310\\python.exe'), os.path.expandvars('%LOCALAPPDATA%\\Programs\\Python\\Python311\\python.exe'), os.path.expandvars('%LOCALAPPDATA%\\Programs\\Python\\Python312\\python.exe'), os.path.expandvars('%LOCALAPPDATA%\\Programs\\Python\\Python313\\python.exe')]
                            for path in common_paths:
                                if not os.path.exists(path):
                                    continue
                                python_executable = path
                                self._log_debug('interp:standard path')
                            else:
                                self._log_debug('interp:unavailable')
                                self._is_running = False
                                return
                env = os.environ.copy()
                env['UNION_OS_INTEGRATED'] = '1'
                env['UNION_OS_HOST'] = self.host
                env['UNION_OS_PORT'] = str(self._porta)
                env['UNION_OS_NO_WEBVIEW'] = '1'
                auth_token = self._gerar_token_auth()
                if auth_token:
                    env['UNION_OS_AUTH_TOKEN'] = auth_token
                peliculas_db = self._detectar_peliculas_cache()
                if peliculas_db:
                    env['UNION_PELICULAS_DB'] = peliculas_db
                    self._log_debug('Pel├¡culas cache detectado')
                if getattr(sys, 'frozen', False):
                    base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
                    qt_plugin_path = os.path.join(base_path, 'PyQt5', 'Qt5', 'plugins')
                    if os.path.exists(qt_plugin_path):
                        env['QT_PLUGIN_PATH'] = qt_plugin_path
                        env['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(qt_plugin_path, 'platforms')
                comando = [python_executable, run_script, '--no-webview', '--host', self.host, '--port', str(self._porta)]
                if sys.platform == 'win32':
                    python_dir = os.path.dirname(python_executable)
                    pythonw_path = os.path.join(python_dir, 'pythonw.exe')
                    stderr_target = self._stderr_file or subprocess.DEVNULL
                    creation_flags = subprocess.CREATE_NO_WINDOW | 134217728
                    if os.path.exists(pythonw_path):
                        comando[0] = pythonw_path
                        self._log_debug('interp:windowless mode')
                        self._server_process = subprocess.Popen(comando, cwd=self._os_path, env=env, stdout=subprocess.DEVNULL, stderr=stderr_target, creationflags=creation_flags)
                    else:
                        self._log_debug('interp:hidden window mode')
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        startupinfo.wShowWindow = 0
                        self._server_process = subprocess.Popen(comando, cwd=self._os_path, env=env, stdout=subprocess.DEVNULL, stderr=stderr_target, startupinfo=startupinfo, creationflags=creation_flags)
                else:
                    self._server_process = subprocess.Popen(comando, cwd=self._os_path, env=env, stdout=subprocess.DEVNULL, stderr=self._stderr_file or subprocess.DEVNULL, stdin=subprocess.DEVNULL, start_new_session=True)
                self._log_debug(f'Processo iniciado PID: {self._server_process.pid}')
        except FileNotFoundError as e:
            self._log_debug(f'Arquivo n├úo encontrado: {e}')
            self._is_running = False
        except Exception as e:
            self._log_debug(f'Erro ao iniciar servidor: {e}')
            import traceback
            traceback.print_exc()
            self._is_running = False
    def _determinar_script_run(self) -> Optional[str]:
        '''
Resolve o caminho do script de inicializacao segundo o ambiente.
Aceita formato fonte ou bytecode.
Returns:
    str ou None
'''
        try:
            from app.utils.path_manager import PathManager
            pm_script = PathManager.get_os_manager_script()
            if pm_script:
                return pm_script
        except Exception:
            pass
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
            possible_paths = [os.path.join(base, '_internal', 'app', 'views', 'ordem_servico', 'run.pyc'), os.path.join(base, '_internal', 'app', 'views', 'ordem_servico', 'run.py'), os.path.join(base, 'app', 'views', 'ordem_servico', 'run.pyc'), os.path.join(base, 'app', 'views', 'ordem_servico', 'run.py')]
            for path in possible_paths:
                if not os.path.exists(path):
                    continue
                return path
            self._log_debug('script:not found in any layout')
            return
        run_script = os.path.join(self._os_path, 'run.py')
        if os.path.exists(run_script):
            return run_script
    def obter_url(self) -> str:
        '''
Obt├®m a URL principal de acesso.
Returns:
    str: URL baseada no modo atual
'''
        if self._modo_atual == ModoServidor.REDE:
            return self.url_rede
        return self.url_local
    def obter_info_rede(self) -> Dict[str, Any]:
        '''
Obt├®m informa├º├Áes de rede do servidor.
Returns:
    Dict com informa├º├Áes de rede
'''
        return {'modo': self._modo_atual.value, 'host': self.host, 'porta': self._porta, 'url_local': self.url_local, 'url_rede': self.url_rede, 'ip_local': self._obter_ip_local(), 'rodando': self.esta_rodando()}
    def obter_status(self) -> str:
        '''
Obt├®m status descritivo do servidor.
Returns:
    str: Status amig├ível para exibi├º├úo
'''
        if self.esta_rodando():
            if self._modo_atual == ModoServidor.REDE:
                return f'­ƒîÉ Servidor ativo (Rede: {self.url_rede})'
            return f'Ô£à Servidor ativo (Local: {self.url_local})'
        disponivel, _ = self.verificar_disponibilidade()
        if disponivel:
            return 'ÔÅ©´©Å Sistema pronto para iniciar'
        return 'ÔØî Sistema indispon├¡vel'
    def parar(self) -> Tuple[bool, str]:
        '''
Para o servidor Flask em execu├º├úo.
Mata processos pela porta para garantir limpeza completa.
MELHORIA: Usa /T para matar ├üRVORE de processos (pai + filhos)
Returns:
    Tuple[bool, str]: (sucesso, mensagem_amigavel)
'''
        import subprocess
        processos_mortos = 0
        try:
            if self._server_process and self._server_process.pid:
                pid = self._server_process.pid
            try:
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
                processos_mortos += 1
                self._log_debug(f'├ürvore de processos {pid} encerrada')
            except Exception:
                try:
                    self._server_process.terminate()
                    self._server_process.wait(timeout=2)
                except Exception:
                    try:
                        try:
                            self._server_process.kill()
                        except Exception:
                            pass
                    except Exception as e:
                        self._log_debug(f'Erro ao parar servidor: {e}')
                        self._is_running = False
                        return (False, 'ÔÜá´©Å Erro ao parar servidor')
            else:
                self._server_process = None
                processos_mortos += self._matar_processos_porta(self._porta)
                self._is_running = False
                if processos_mortos > 0:
                    self._log_debug(f'Servidor parado ({processos_mortos} processos encerrados)')
                    return True, f'Ô£à Servidor parado ({processos_mortos} processos encerrados)'
                self._log_debug('Servidor parado (nenhum processo ativo)')
        except Exception as e:
            self._log_debug(f'Erro ao parar servidor: {e}')
            self._is_running = False
            return (False, 'ÔÜá´©Å Erro ao parar servidor')
        return (True, 'Ô£à Servidor parado')
    def _matar_processos_porta(self, porta: int) -> int:
        '''
Mata todos os processos escutando em uma porta espec├¡fica.
MELHORIA: Usa /T para matar ├üRVORE (processo + filhos Waitress)
Args:
    porta: N├║mero da porta
Returns:
    int: Quantidade de processos mortos
'''
        import subprocess
        processos_mortos = 0
        try:
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            pids_para_matar = set()
            for line in result.stdout.split('\n'):
                if f':{porta}' in line and ('LISTENING' in line or 'ESTABLISHED' in line):
                    parts = line.split()
                    if not parts:
                        continue
                    try:
                        pid = int(parts[-1])
                        if pid > 0:
                            pids_para_matar.add(pid)
                    except ValueError:
                        continue
        except Exception as e:
            self._log_debug(f'Erro ao matar processos: {e}')
            return processos_mortos
        for pid in pids_para_matar:
            try:
                try:
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
                    processos_mortos += 1
                    self._log_debug(f'├ürvore {pid} encerrada')
                except Exception:
                    continue
            except Exception as e:
                self._log_debug(f'Erro ao matar processos: {e}')
                return processos_mortos
        return processos_mortos
    def reiniciar(self, modo: ModoServidor=None) -> Tuple[bool, str]:
        '''
Reinicia o servidor Flask.
Args:
    modo: Modo de opera├º├úo (usa modo atual se None)
Returns:
    Tuple[bool, str]: (sucesso, mensagem_amigavel)
'''
        modo = modo or self._modo_atual
        self.parar()
        time.sleep(1)
        return self.iniciar(modo=modo)
    def iniciar_servidor_rede(self, abrir_navegador: bool=False) -> Tuple[bool, str]:
        '''
Inicia o servidor em modo REDE (acess├¡vel por outros hosts na LAN).
├Ütil para permitir acesso de outros terminais/recep├º├úo.
Args:
    abrir_navegador: Se True, abre o navegador ap├│s iniciar
Returns:
    Tuple[bool, str]: (sucesso, mensagem_amigavel)
'''
        if self.esta_rodando():
            if self._modo_atual == ModoServidor.REDE:
                return True, f'Ô£à Servidor j├í est├í ativo em modo REDE!\n\n­ƒîÉ URL Local: {self.url_local}\n­ƒîÉ URL Rede: {self.url_rede}\n\n­ƒô▒ Outros dispositivos na rede podem acessar\nusando o endere├ºo de rede acima.'
            self._log_debug('Reiniciando servidor em modo REDE')
            return self.reiniciar(modo=ModoServidor.REDE)
        return self.iniciar(modo=ModoServidor.REDE)
    def alternar_modo(self) -> Tuple[bool, str]:
        '''
Alterna entre modo LOCAL e REDE.
Returns:
    Tuple[bool, str]: (sucesso, mensagem_amigavel)
'''
        novo_modo = ModoServidor.LOCAL if self._modo_atual == ModoServidor.REDE else ModoServidor.REDE
        if self.esta_rodando():
            return self.reiniciar(modo=novo_modo)
        self._modo_atual = novo_modo
        modo_str = 'REDE (acess├¡vel na LAN)' if novo_modo == ModoServidor.REDE else 'LOCAL (apenas esta m├íquina)'
        return True, f'Ô£à Modo alterado para: {modo_str}'
_os_manager_instance: Optional[UnionOSManager] = None
def get_os_manager() -> UnionOSManager:
    '''
Obt├®m a inst├óncia singleton do UnionOSManager.
Returns:
    UnionOSManager: Inst├óncia ├║nica do gerenciador
Uso:
    >>> from app.utils.os_manager import get_os_manager
    >>> manager = get_os_manager()
    >>> sucesso, msg = manager.iniciar()
'''
    global _os_manager_instance
    if _os_manager_instance is None:
        _os_manager_instance = UnionOSManager()
    return _os_manager_instance
if __name__ == '__main__':
    print('======================================================================')
    print('TESTE: UNION OS MANAGER')
    print('======================================================================')
    manager = get_os_manager()
    print(f'\n­ƒôè Status: {manager.obter_status()}')
    print('­ƒôé Caminho: [verificado internamente]')
    disponivel, msg = manager.verificar_disponibilidade()
    print(f'\nÔ£à Dispon├¡vel: {disponivel}')
    print(f'­ƒÆ¼ Mensagem:\n{msg}')
    if disponivel:
        print('\n----------------------------------------------------------------------')
        print('Op├º├Áes de teste:')
        print('1. Iniciar em modo LOCAL (127.0.0.1)')
        print('2. Iniciar em modo REDE (0.0.0.0)')
        print('3. Sair')
        opcao = input('\nEscolha (1/2/3): ').strip()
        if opcao == '1':
            sucesso, msg = manager.iniciar(ModoServidor.LOCAL)
            print(f'\n{'Ô£à' if sucesso else 'ÔØî'} {msg}')
            if sucesso:
                print(f'\n­ƒîÉ URL: {manager.url_local}')
                input('\nÔÅ©´©Å Pressione ENTER para encerrar...')
        elif opcao == '2':
            sucesso, msg = manager.iniciar_modo_rede()
            print(f'\n{'Ô£à' if sucesso else 'ÔØî'} {msg}')
            if sucesso:
                info = manager.obter_info_rede()
                print('\n­ƒôè Informa├º├Áes de Rede:')
                print(f'   - Modo: {info['modo']}')
                print(f'   - IP Local: {info['ip_local']}')
                print(f'   - URL Local: {info['url_local']}')
                print(f'   - URL Rede: {info['url_rede']}')
                input('\nÔÅ©´©Å Pressione ENTER para encerrar...')
    print('\n======================================================================')
    print('Teste finalizado!')
    print('======================================================================')
