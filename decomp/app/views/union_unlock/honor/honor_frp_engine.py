'''
TECH UNION SOLUTIONS ÔÇö Honor FRP Engine
Orquestra leitura de serial e FRP unlock via fastboot do unlock_tools.
Logs sanitizados ÔÇö ZERO vazamento de paths, comandos OEM ou chave.
NAO compilar com Cython (usa subprocess).
'''
import os
import subprocess
import logging
from typing import Callable, Optional
from . import _honor_core as _core
logger = logging.getLogger(__name__)
_CW = 134217728
_SI = None
if os.name == 'nt':
    _SI = subprocess.STARTUPINFO()
    _SI.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    _SI.wShowWindow = subprocess.SW_HIDE
def _resolver_fastboot() -> Optional[str]:
    '''Resolve fastboot.exe do unlock_tools (ZIP AES).'''
    try:
        from app.utils.unlock_tools_manager import get_unlock_tools_manager
        mgr = get_unlock_tools_manager()
        tools_dir = mgr.get_tools_dir()
        if not mgr.ja_extraido():
            ok, _ = mgr.extrair()
            if not ok and not mgr.ja_extraido():
                return
        for nome in ('fastboot.exe', 'fastboot2.exe'):
            caminho = os.path.join(tools_dir, nome)
            if not os.path.isfile(caminho):
                continue
            return caminho
        return
    except Exception as e:
        logger.debug('Falha ao resolver fastboot unlock_tools: %s', e)
class HonorFrpEngine:
    '''Engine Honor/Huawei FRP ÔÇö mesma logica do piloto Tkinter.'''
    def __init__(self):
        self._fastboot = None
        self._tools_dir = None
    def _ensure_fastboot(self) -> bool:
        if self._fastboot and os.path.isfile(self._fastboot):
            return True
        self._fastboot = _resolver_fastboot()
        if self._fastboot:
            self._tools_dir = os.path.dirname(self._fastboot)
            return True
        return False
    def _fb(self, args: list, timeout: int=30) -> tuple:
        '''Executa fastboot. Retorna (ok, combined_output).
        Nunca inclui o path do exe no output.'''
        if not self._ensure_fastboot():
            return (False, '')
        try:
            r = subprocess.run([self._fastboot] + args, capture_output=True, text=True, timeout=timeout, cwd=self._tools_dir, creationflags=_CW if os.name == 'nt' else 0, startupinfo=_SI, encoding='utf-8', errors='replace')
            out = f'{r.stdout or ''}\n{r.stderr or ''}'.strip()
            return True, out
        except subprocess.TimeoutExpired:
            return (False, '')
        except Exception:
            return (False, '')
    def read_info(self, log_cb: Callable=None) -> dict:
        '''Le serial/IMEI/modelo ÔÇö mesma sequencia do piloto Tkinter.'''
        def _log(msg):
            if log_cb:
                log_cb(msg)
        info = {'serial': '', 'imei': '', 'modelo': '', 'conectado': False}
        if not self._ensure_fastboot():
            _log('Ferramenta de comunicacao indisponivel')
            _log('Abra o Diagnostico novamente para carregar as ferramentas')
            return info
        _log('Lendo informacoes do dispositivo...')
        ok, out = self._fb(['devices'], timeout=15)
        serial = _core.parse_serial_from_devices(out) if ok else None
        if not serial:
            _log('Nenhum dispositivo em fastboot detectado')
            return info
        info['conectado'] = True
        info['serial'] = serial
        _log('Dispositivo detectado em fastboot')
        imei = None
        ok2, out2 = self._fb(['oem', 'get-psid'], timeout=15)
        if ok2 and out2 and ('SN' in out2 or 'IMEI' in out2 or 'OKAY' in out2):
            sn = _core.parse_serial(out2)
            if sn:
                serial = sn
            im = _core.parse_imei(out2)
            if im:
                imei = im
        if not imei or not serial:
            ok3, out3 = self._fb(['oem', 'getpsid'], timeout=15)
            if ok3 and out3 and ('SN' in out3 or 'IMEI' in out3 or 'OKAY' in out3):
                sn = _core.parse_serial(out3)
                if sn:
                    serial = sn
                im = _core.parse_imei(out3)
                if im:
                    imei = im
        if not serial or serial == info['serial']:
            ok4, out4 = self._fb(['oem', 'get-bootinfo'], timeout=15)
            if ok4 and out4 and 'FAILED' not in out4:
                sn = _core.parse_serial(out4)
                if sn:
                    serial = sn
        if not serial:
            ok5, out5 = self._fb(['getvar', 'nve:SN@SN'], timeout=15)
            if ok5 and out5:
                sn = _core.parse_nve_sn(out5)
                if sn:
                    serial = sn
        if not serial:
            ok6, out6 = self._fb(['getvar', 'serialno'], timeout=15)
            if ok6 and out6 and 'not allowed' not in out6.lower() and 'FAILED' not in out6:
                sn = _core.parse_serial(out6)
                if sn:
                    serial = sn
        okm, outm = self._fb(['oem', 'get-product-model'], timeout=15)
        if okm and outm:
            modelo = _core.parse_modelo(outm)
            if modelo:
                info['modelo'] = modelo
                _log(f'  Modelo: {modelo}')
        info['serial'] = serial or info['serial']
        info['imei'] = imei or ''
        if info['serial']:
            _log(f'  Serial: {info['serial']}')
        else:
            _log('  Serial nao detectada')
        if info['imei']:
            _log(f'  IMEI: {info['imei']}')
        return info
    def executar_unlock(self, chave: str, log_cb: Callable=None) -> tuple:
        '''Executa FRP unlock. Nunca loga a chave nem o comando OEM.'''
        def _log(msg):
            if log_cb:
                log_cb(msg)
        chave = (chave or '').strip()
        if not chave or chave.lower().startswith('cole a chave'):
            return (False, 'Chave invalida')
        if not self._ensure_fastboot():
            return (False, 'Ferramenta de comunicacao indisponivel')
        ok_dev, out_dev = self._fb(['devices'], timeout=10)
        if not ok_dev or not _core.parse_serial_from_devices(out_dev):
            return (False, 'Nenhum dispositivo em fastboot')
        _log('Enviando dados processados...')
        cmd = _core.oem_unlock_cmd()
        ok, out = self._fb(['oem', cmd, chave], timeout=60)
        if not ok:
            _log('Falha na comunicacao com o dispositivo')
            return (False, 'Falha na comunicacao com o dispositivo')
        out_l = (out or '').lower()
        if 'okay' in out_l and 'failed' not in out_l:
            _log('Operacao aceita')
            _log('Reinicie o dispositivo para aplicar as alteracoes')
            return (True, 'Operacao concluida')
        if 'failed' in out_l or 'error' in out_l:
            _log('Operacao rejeitada pelo dispositivo')
            return (False, 'Operacao rejeitada ÔÇö verifique a chave')
        _log('Resposta inesperada do dispositivo')
        return (False, 'Nao foi possivel confirmar a operacao')
    def reboot(self, log_cb: Callable=None) -> tuple:
        '''Reinicia o dispositivo.'''
        def _log(msg):
            if log_cb:
                log_cb(msg)
        if not self._ensure_fastboot():
            return (False, 'Ferramenta de comunicacao indisponivel')
        _log('Reiniciando dispositivo...')
        ok, out = self._fb(['reboot'], timeout=15)
        if not ok:
            if 'status read failed' in (out or '').lower():
                _log('Reinicio aceito pelo dispositivo')
                return (True, 'Reiniciando')
        _log('Reinicie o dispositivo manualmente')
        return (False, 'Reinicie manualmente')
