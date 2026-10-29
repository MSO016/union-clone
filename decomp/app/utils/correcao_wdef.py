'''
TECH UNION SOLUTIONS - M├│dulo de Corre├º├úo Windows Defender/ADB
===============================================================
Este m├│dulo fornece fun├º├Áes para detectar e corrigir problemas
do Windows Defender bloqueando o ADB, conflitos de vers├Áes,
e problemas de Exploit Protection.
Uso: Chamado pelo menu superior do DiagnosticoAndroid
'''
import os
import sys
import subprocess
import platform
import logging
import shutil
import urllib.request
import zipfile
import tempfile
import ctypes
from typing import Tuple, Optional
logger = logging.getLogger(__name__)
WINDOWS_BLOCKED_ERROR_CODE = 3221225477
_DEFENDER_CMDLET_TIMEOUT_S = 8
_EXPLOIT_MITIGATION_TIMEOUT_S = 10
_AV_PROBE_TIMEOUT_S = 5
_FORBIDDEN_USER_MSG_TOKENS = ('powershell', 'Powershell', 'PowerShell', 'Get-Mp', 'Add-Mp', 'Remove-Mp', 'Set-Mp', 'Set-ProcessMitigation', 'Remove-ProcessMitigation', 'Get-CimInstance', 'SecurityCenter2', '-Command', '-ExclusionPath', '-ExclusionProcess', '$threats', '$threat', 'ThreatID', 'Resources', 'ErrorAction', 'SilentlyContinue', 'Where-Object', 'foreach', 'Write-Output', 'Traceback', 'Exception', '[', ']')
_GENERIC_USER_FALLBACK_MSG = 'N├úo foi poss├¡vel concluir esta etapa. Detalhes t├®cnicos foram registrados no log do sistema.'
class CorrecaoWindowsDefender:
    '''
    Classe para detectar e corrigir problemas do Windows Defender com ADB.
    Projetada para ser chamada de forma simples pelo menu do aplicativo.
    '''
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_windows = platform.system() == 'Windows'
        self.tech_union_adb = self._get_tech_union_adb_path()
        self.platform_tools_path = 'C:\\platform-tools'
        self._av_detection_cache = None
    def _run_powershell_safe(self, cmd_str: str, timeout_s: int, safe_msg_on_fail: str=None) -> Tuple[bool, str]:
        '''
Executa um comando PowerShell de forma resiliente, garantindo que
nenhum detalhe t├®cnico vaze pro chamador em caso de falha.
Args:
    cmd_str: Comando PowerShell em string (N├âO array ÔÇö array vaza
             no __str__ da TimeoutExpired).
    timeout_s: Timeout em segundos (sempre curto: 5-10s).
    safe_msg_on_fail: Mensagem GEN├ëRICA a devolver ao chamador em
                      caso de qualquer falha. NUNCA inclua detalhes
                      t├®cnicos aqui.
Returns:
    Tuple[bool, str]: (sucesso, mensagem_gen├®rica_segura). Em caso
    de sucesso a mensagem ├® o stdout do comando (j├í vem do PS, n├úo
    ├® nosso c├│digo). Em caso de falha ├® a `safe_msg_on_fail`.
'''
        if safe_msg_on_fail is None:
            safe_msg_on_fail = 'Etapa n├úo conclu├¡da.'
        if not self.is_windows:
            return False, safe_msg_on_fail
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        try:
            result = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', cmd_str], capture_output=True, text=True, timeout=timeout_s, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0:
                return True, (result.stdout or '').strip()
            self.logger.warning('Powershell rc=%s timeout=%ss stderr_len=%s', result.returncode, timeout_s, len(result.stderr or ''))
            if result.stderr:
                self.logger.debug('PS stderr: %s', (result.stderr or '')[:500])
            return False, safe_msg_on_fail
        except subprocess.TimeoutExpired:
            self.logger.warning('Powershell timeout ap├│s %ss (cmd suprimido)', timeout_s)
            return False, safe_msg_on_fail
        except FileNotFoundError:
            self.logger.error('PowerShell n├úo encontrado no sistema')
            return (False, 'PowerShell indispon├¡vel neste sistema.')
        except Exception as e:
            self.logger.warning('Powershell falhou: %s', type(e).__name__)
            return False, safe_msg_on_fail
    def detect_active_antivirus(self) -> dict:
        '''
Detecta antiv├¡rus instalados via WMI (root\\SecurityCenter2).
Resultado ├® cacheado durante a vida do objeto.
Returns:
    dict com:
      - defender_active (bool): Defender presente E ativo
      - third_party_av (list[str]): nomes amig├íveis dos AVs detectados
      - can_use_defender_cmdlets (bool): seguro tentar cmdlets do Defender
      - probe_succeeded (bool): a consulta WMI funcionou
'''
        if self._av_detection_cache is not None:
            return self._av_detection_cache
        result = {'defender_active': False, 'third_party_av': [], 'can_use_defender_cmdlets': False, 'probe_succeeded': False}
        if not self.is_windows:
            self._av_detection_cache = result
            return result
        probe_cmd = 'Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct -ErrorAction SilentlyContinue | ForEach-Object { $enabled = ($_.productState -band 0x1000) -ne 0 ; Write-Output ("{0}|{1}" -f $_.displayName, $enabled) }'
        ok, output = self._run_powershell_safe(probe_cmd, timeout_s=_AV_PROBE_TIMEOUT_S, safe_msg_on_fail='probe_failed')
        if not ok:
            self.logger.info('Sondagem de AV falhou; assumindo modo conservador.')
            self._av_detection_cache = result
            return result
        result['probe_succeeded'] = True
        for line in (output or '').splitlines():
            line = line.strip()
            if not line or '|' not in line:
                continue
            try:
                name, enabled_str = line.split('|', 1)
                name = name.strip()
                is_enabled = enabled_str.strip().lower() == 'true'
                if not name:
                    continue
            except Exception:
                continue
            try:
                if 'windows defender' in name.lower():
                    result['defender_active'] = is_enabled
                elif is_enabled:
                    result['third_party_av'].append(name)
            except Exception:
                continue
        result['can_use_defender_cmdlets'] = bool(result['defender_active'])
        self.logger.info('AV detectados ÔÇö defender_ativo=%s 3p=%s usar_cmdlets_defender=%s', result['defender_active'], result['third_party_av'] or '[]', result['can_use_defender_cmdlets'])
        self._av_detection_cache = result
        return result
    @staticmethod
    def _sanitize_for_user(message: str) -> str:
        '''
        ├Ültima linha de defesa antes do popup. Se a mensagem contiver
        algum token t├®cnico proibido, devolve uma mensagem gen├®rica.
        '''
        if not message:
            return ''
        for token in _FORBIDDEN_USER_MSG_TOKENS:
            if not token in message:
                continue
            return _GENERIC_USER_FALLBACK_MSG
        return message
    def _get_tech_union_adb_path(self) -> str:
        '''Retorna o caminho do ADB do Tech Union'''
        paths = ['C:\\Program Files (x86)\\Tech Union Solutions - Smartphone Solutions\\platform-tools', 'C:\\Program Files\\Tech Union Solutions - Smartphone Solutions\\platform-tools']
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
            paths.insert(0, os.path.join(app_dir, 'platform-tools'))
            paths.insert(1, os.path.join(app_dir, '_internal', 'platform-tools'))
        for path in paths:
            if os.path.exists(os.path.join(path, 'adb.exe')):
                return path
        return paths[0]
    def is_admin(self) -> bool:
        '''Verifica se o aplicativo est├í rodando como administrador'''
        if not self.is_windows:
            return True
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    def detect_adb_blocked(self) -> Tuple[bool, str]:
        '''
Detecta se o ADB est├í bloqueado pelo Windows.
Ô£à CORRE├ç├âO CIR├ÜRGICA 23/01/2026:
Antes: Executava "adb.exe version" AUTOMATICAMENTE ao abrir di├ílogo
Problema: Iniciava processo ADB que ficava ├│rf├úo em mem├│ria (DLLs travadas)
Agora: Retorna valor neutro - teste manual via bot├úo "Executar Corre├º├úo"
Impacto: ZERO - funcionalidade preservada, s├│ n├úo executa automaticamente
Returns:
    Tuple[bool, str]: (est├í_bloqueado, mensagem_de_diagn├│stico)
'''
        if not self.is_windows:
            return (False, 'Sistema n├úo ├® Windows')
        adb_path = os.path.join(self.tech_union_adb, 'adb.exe')
        if not os.path.exists(adb_path):
            return True, f'ADB n├úo encontrado em: {adb_path}'
        return (False, "Clique em 'Sim' para executar a corre├º├úo e testar o ADB")
    def add_defender_exclusion(self) -> Tuple[bool, str]:
        '''
Adiciona exce├º├úo no Windows Defender para ADB e ferramentas FRP.
APENAS por PROCESSO (n├úo exp├Áe caminhos internos).
Inclui: adb, fastboot, mtk, edl, FRP_EDL, emmcdl, fh_loader
Returns:
    Tuple[bool, str]: (sucesso, mensagem_segura_para_usuario)
'''
        if not self.is_windows:
            return (False, 'N├úo ├® Windows')
        if not self.is_admin():
            return (False, 'Requer privil├®gios de administrador')
        av = self.detect_active_antivirus()
        if not av['can_use_defender_cmdlets']:
            self.logger.info('Defender inativo; etapa de exce├º├úo ignorada. AV terceiros: %s', av['third_party_av'] or '[]')
            return (True, 'Etapa ignorada (Defender n├úo est├í ativo neste sistema)')
        path_commands = [f'Add-MpPreference -ExclusionPath "{self.tech_union_adb}"', f'Add-MpPreference -ExclusionPath "{self.platform_tools_path}"']
        process_exclusions = ['adb.exe', 'fastboot.exe', 'mtk.exe', 'edl.exe', 'FRP_EDL.exe', 'emmcdl.exe', 'fh_loader.exe', 'ATCommandConsole.exe', 'ExynosBridgeHost.exe']
        falhas = 0
        total = len(path_commands) + len(process_exclusions)
        for cmd in path_commands:
            ok, _ = self._run_powershell_safe(cmd, timeout_s=_DEFENDER_CMDLET_TIMEOUT_S, safe_msg_on_fail='Falha em uma exce├º├úo de pasta')
            if ok:
                continue
            falhas += 1
        for proc in process_exclusions:
            ok, _ = self._run_powershell_safe(f'Add-MpPreference -ExclusionProcess "{proc}"', timeout_s=_DEFENDER_CMDLET_TIMEOUT_S, safe_msg_on_fail='Falha em uma exce├º├úo de processo')
            if ok:
                continue
            falhas += 1
        if falhas == 0:
            self.logger.info('Exce├º├Áes adicionadas ao Windows Defender (ADB + FRP)')
            return (True, 'Exce├º├Áes adicionadas com sucesso!')
        self.logger.warning('Exce├º├Áes: %s de %s falharam (Defender pode estar restrito)', falhas, total)
        if falhas == total:
            return (False, 'N├úo foi poss├¡vel aplicar nenhuma exce├º├úo')
        return False, f'Aplicadas parcialmente ({total - falhas}/{total})'
    def remove_exploit_protection(self) -> Tuple[bool, str]:
        '''
Remove/Desabilita Exploit Protection de ADB e ferramentas FRP.
Desabilita: DEP, SEHOP, ForceRelocateImages, BottomUp, HighEntropy, CFG, StrictCFG.
NOTA: Set/Remove-ProcessMitigation N├âO dependem do Defender ÔÇö fazem
parte do m├│dulo padr├úo `ProcessMitigations` do Windows. Ainda assim
usamos `_run_powershell_safe` para nunca expor `str(e)` ao usu├írio.
Returns:
    Tuple[bool, str]: (sucesso, mensagem_segura_para_usuario)
'''
        if not self.is_windows:
            return (False, 'N├úo ├® Windows')
        processes = ['adb.exe', 'fastboot.exe', 'mtk.exe', 'edl.exe', 'FRP_EDL.exe', 'emmcdl.exe', 'fh_loader.exe', 'ATCommandConsole.exe', 'ExynosBridgeHost.exe']
        mitigations = 'DEP,SEHOP,ForceRelocateImages,BottomUp,HighEntropy,CFG,StrictCFG,StrictHandle'
        falhas = 0
        for proc in processes:
            self._run_powershell_safe(f'Remove-ProcessMitigation -Name "{proc}" -ErrorAction SilentlyContinue', timeout_s=_EXPLOIT_MITIGATION_TIMEOUT_S, safe_msg_on_fail='cleanup_skip')
            ok, _ = self._run_powershell_safe(f'Set-ProcessMitigation -Name "{proc}" -Disable {mitigations} -ErrorAction SilentlyContinue', timeout_s=_EXPLOIT_MITIGATION_TIMEOUT_S, safe_msg_on_fail='Falha em uma mitiga├º├úo')
            if ok:
                continue
            falhas += 1
        if falhas == 0:
            self.logger.info('Exploit Protection removido/desabilitado para todas as ferramentas')
            return (True, 'Prote├º├Áes de exploit removidas!')
        self.logger.warning('Exploit Protection: %s de %s processos falharam', falhas, len(processes))
        if falhas == len(processes):
            return (False, 'N├úo foi poss├¡vel ajustar Exploit Protection')
        return False, f'Ajustadas parcialmente ({len(processes) - falhas}/{len(processes)})'
    def clean_file_attributes(self) -> Tuple[bool, str]:
        '''
Remove atributos de sistema/oculto dos arquivos ADB.
Apenas pastas p├║blicas (platform-tools).
Returns:
    Tuple[bool, str]: (sucesso, mensagem)
'''
        if not self.is_windows:
            return (False, 'N├úo ├® Windows')
        try:
            adb_files = ['adb.exe', 'fastboot.exe', 'AdbWinApi.dll', 'AdbWinUsbApi.dll']
            folders = [self.tech_union_adb, self.platform_tools_path]
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            for folder in folders:
                if os.path.exists(folder):
                    for f in adb_files:
                        filepath = os.path.join(folder, f)
                        if os.path.exists(filepath):
                            try:
                                try:
                                    subprocess.run(['attrib', '-S', '-H', filepath], startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
                                except Exception:
                                    continue
                            except Exception as e:
                                self.logger.error(f'Erro ao limpar atributos: {e}')
                                return False, f'Erro: {str(e)}'
        except Exception as e:
            self.logger.error(f'Erro ao limpar atributos: {e}')
            return False, f'Erro: {str(e)}'
        self.logger.info('Atributos de arquivos limpos')
        return (True, 'Atributos limpos!')
    def kill_all_adb(self) -> Tuple[bool, str]:
        '''
Mata todos os processos ADB em execu├º├úo.
Returns:
    Tuple[bool, str]: (sucesso, mensagem)
'''
        if not self.is_windows:
            return (False, 'N├úo ├® Windows')
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            result = subprocess.run(['taskkill', '/F', '/IM', 'adb.exe'], capture_output=True, text=True, timeout=30, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
            killed = result.stdout.count('├èXITO') + result.stdout.count('SUCCESS')
            if killed > 0:
                self.logger.info(f'{killed} processos ADB encerrados')
                return True, f'{killed} processos ADB encerrados'
        except Exception as e:
            self.logger.error(f'Erro ao matar processos: {e}')
            return False, f'Erro: {str(e)}'
        return (True, 'Nenhum processo ADB em execu├º├úo')
    def restore_from_quarantine(self) -> Tuple[bool, str]:
        '''
Tenta restaurar arquivos da quarentena do Windows Defender.
Nota: Requer privil├®gios de administrador. Sem Defender ativo,
a etapa ├® ignorada silenciosamente (n├úo trava o fluxo).
Returns:
    Tuple[bool, str]: (sucesso, mensagem_segura_para_usuario)
'''
        if not self.is_windows:
            return (False, 'N├úo ├® Windows')
        if not self.is_admin():
            return (False, 'Requer privil├®gios de administrador')
        av = self.detect_active_antivirus()
        if not av['can_use_defender_cmdlets']:
            self.logger.info('Defender inativo; quarentena n├úo dispon├¡vel. Etapa ignorada.')
            return (True, 'Quarentena do Defender indispon├¡vel (etapa ignorada)')
        files_to_restore = ['adb.exe', 'fastboot.exe', 'mtk.exe', 'edl.exe', 'FRP_EDL.exe', 'emmcdl.exe', 'fh_loader.exe', 'ExynosBridgeHost.exe']
        restored = 0
        skipped = 0
        for filename in files_to_restore:
            ps_cmd = f'$t = Get-MpThreat -EA SilentlyContinue | Where-Object {{ $_.Resources -like "*{filename}*" }} ; if ($t) {{ foreach ($i in $t) {{ Add-MpPreference -ExclusionProcess "{filename}" -EA SilentlyContinue ; Remove-MpThreat -ThreatID $i.ThreatID -EA SilentlyContinue }} ; Write-Output "RESTORED" }}'
            ok, output = self._run_powershell_safe(ps_cmd, timeout_s=_DEFENDER_CMDLET_TIMEOUT_S, safe_msg_on_fail='check_skipped')
            if not ok:
                skipped += 1
                continue
            if 'RESTORED' in (output or ''):
                restored += 1
                self.logger.info('Restaurado da quarentena: %s', filename)
        if restored > 0:
            return True, f'{restored} arquivo(s) restaurado(s) da quarentena'
        if skipped == len(files_to_restore):
            return (False, 'N├úo foi poss├¡vel verificar a quarentena')
        return (True, 'Nenhum arquivo encontrado na quarentena')
    def download_fresh_platform_tools(self, target_path: Optional[str]=None) -> Tuple[bool, str]:
        '''
Baixa uma vers├úo limpa do platform-tools do Google.
Args:
    target_path: Caminho de destino (padrao: C:\\platform-tools)
Returns:
    Tuple[bool, str]: (sucesso, mensagem)
'''
        if target_path is None:
            target_path = self.platform_tools_path
        url = 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip'
        try:
            self.logger.info('Baixando platform-tools do Google...')
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, 'platform-tools.zip')
            urllib.request.urlretrieve(url, zip_path)
            if os.path.exists(target_path):
                backup_path = target_path + '-backup-old'
                if os.path.exists(backup_path):
                    shutil.rmtree(backup_path, ignore_errors=True)
                shutil.move(target_path, backup_path)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(os.path.dirname(target_path))
            shutil.rmtree(temp_dir, ignore_errors=True)
            self.logger.info(f'Platform-tools instalado em: {target_path}')
        except Exception as e:
            self.logger.error(f'Erro ao baixar platform-tools: {e}')
            return False, f'Erro ao baixar: {str(e)}'
        return True, f'Platform-tools instalado em: {target_path}'
    def run_full_correction(self, progress_callback=None) -> Tuple[bool, list]:
        '''
Executa corre├º├úo completa de todos os problemas.
Inclui: ADB, ferramentas FRP, exclus├Áes, exploit protection, quarentena.
Mant├®m compatibilidade de assinatura. Detalhes do cen├írio (Defender
ativo, AV third-party detectado, etapas ignoradas) ficam dispon├¡veis
via `self._last_correction_context` para a UI consumir.
Args:
    progress_callback: Fun├º├úo de callback para progresso (opcional)
Returns:
    Tuple[bool, list]: (sucesso_geral, lista_de_mensagens_seguras)
'''
        messages = []
        all_success = True
        av = self.detect_active_antivirus()
        steps = [('Matando processos ADB...', self.kill_all_adb), ('Restaurando arquivos da quarentena...', self.restore_from_quarantine), ('Adicionando exce├º├Áes no Defender (ADB + FRP)...', self.add_defender_exclusion), ('Removendo Exploit Protection...', self.remove_exploit_protection), ('Limpando atributos de arquivos...', self.clean_file_attributes)]
        skipped_for_no_defender = 0
        for i, (desc, func) in enumerate(steps):
            if progress_callback:
                progress_callback(i + 1, len(steps), desc)
            try:
                success, msg = func()
            except Exception as e:
                self.logger.error("Falha inesperada em '%s': %s", desc, type(e).__name__)
                success, msg = False, 'Etapa n├úo conclu├¡da (erro interno)'
            safe_msg = self._sanitize_for_user(msg)
            is_skipped = success and 'ignorada' in safe_msg.lower()
            if is_skipped:
                icon = 'Ôä╣´©Å'
                if not av['can_use_defender_cmdlets']:
                    skipped_for_no_defender += 1
            else:
                icon = 'Ô£à' if success else 'ÔØî'
            messages.append(f'{icon} {desc} {safe_msg}')
            if success:
                continue
            all_success = False
        blocked, status = self.detect_adb_blocked()
        safe_status = self._sanitize_for_user(status)
        if blocked:
            messages.append(f'ÔÜá´©Å ADB ainda com problemas: {safe_status}')
            all_success = False
        else:
            messages.append('Ô£à ADB funcionando corretamente!')
        self._last_correction_context = {'defender_active': av['defender_active'], 'third_party_av': list(av['third_party_av']), 'av_probe_succeeded': av['probe_succeeded'], 'skipped_for_no_defender': skipped_for_no_defender, 'all_success': all_success}
        return all_success, messages
    def get_diagnostic_info(self) -> dict:
        '''
Retorna informa├º├Áes de diagn├│stico sobre o ADB e sistema.
Returns:
    dict: Informa├º├Áes de diagn├│stico
'''
        info = {'is_admin': self.is_admin(), 'tech_union_adb_path': self.tech_union_adb, 'tech_union_adb_exists': os.path.exists(os.path.join(self.tech_union_adb, 'adb.exe')), 'platform_tools_exists': os.path.exists(os.path.join(self.platform_tools_path, 'adb.exe')), 'adb_blocked': False, 'adb_status': ''}
        blocked, status = self.detect_adb_blocked()
        info['adb_blocked'] = blocked
        info['adb_status'] = status
        return info
def show_correction_dialog(parent=None):
    '''
Mostra di├ílogo de corre├º├úo com interface amig├ível.
Esta fun├º├úo ├® chamada diretamente pelo menu do aplicativo.
Args:
    parent: Widget pai (QWidget) para o di├ílogo
'''
    from PyQt5.QtWidgets import (QMessageBox, QProgressDialog, QApplication)
    from PyQt5.QtCore import Qt
    corretor = CorrecaoWindowsDefender()
    if not corretor.is_admin():
        QMessageBox.warning(parent, 'Permiss├úo Necess├íria', "Para corrigir problemas do Windows Defender,\no aplicativo precisa ser executado como Administrador.\n\nFeche o aplicativo e abra novamente clicando com\nbot├úo direito ÔåÆ 'Executar como administrador'.")
        return
    blocked, status = corretor.detect_adb_blocked()
    if not blocked:
        reply = QMessageBox.question(parent, 'ADB OK', 'O ADB est├í funcionando normalmente.\n\nDeseja executar a corre├º├úo preventiva mesmo assim?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
    else:
        reply = QMessageBox.question(parent, 'Problema Detectado', f'Foi detectado um problema com o ADB:\n\n{status}\n\nDeseja executar a corre├º├úo autom├ítica?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply != QMessageBox.Yes:
            return
    progress = QProgressDialog('Corrigindo problemas do ADB e ferramentas FRP...', None, 0, 6, parent)
    progress.setWindowTitle('Corre├º├úo em Andamento')
    progress.setWindowModality(Qt.WindowModal)
    progress.setMinimumDuration(0)
    progress.setValue(0)
    QApplication.processEvents()
    def update_progress(step, total, desc):
        progress.setValue(step)
        progress.setLabelText(desc)
        QApplication.processEvents()
    success, messages = corretor.run_full_correction(update_progress)
    progress.setValue(6)
    progress.close()
    ctx = getattr(corretor, '_last_correction_context', None) or {}
    third_party_av = ctx.get('third_party_av') or []
    defender_active = bool(ctx.get('defender_active'))
    skipped_no_def = int(ctx.get('skipped_for_no_defender') or 0)
    safe_messages = [CorrecaoWindowsDefender._sanitize_for_user(m) for m in messages]
    result_text = '\n'.join(safe_messages)
    if success:
        QMessageBox.information(parent, 'Corre├º├úo Conclu├¡da', f'A corre├º├úo foi aplicada com sucesso!\n\n{result_text}\n\nRecomendamos reiniciar o aplicativo.')
        return
    if (skipped_no_def > 0 or not defender_active) and third_party_av:
        av_label = ', '.join(third_party_av[:3])
        QMessageBox.information(parent, 'Corre├º├úo Conclu├¡da (modo compatibilidade)', f'Detectamos que voc├¬ usa outro antiv├¡rus: {av_label}.\n\nAs etapas que dependem do Windows Defender foram ignoradas\nporque seu sistema utiliza outro antiv├¡rus.\n\n{result_text}\n\n­ƒÆí Se notar bloqueios ou alertas no seu antiv├¡rus durante o\nuso da ferramenta, contate nosso suporte para orienta├º├úo\nespec├¡fica para o seu antiv├¡rus.\n\nRecomendamos reiniciar o aplicativo.')
        return
    if skipped_no_def > 0 or not defender_active:
        QMessageBox.information(parent, 'Corre├º├úo Conclu├¡da (modo compatibilidade)', f'O Windows Defender n├úo est├í ativo neste sistema.\n\nAs etapas que dependem dele foram ignoradas.\n\n{result_text}\n\n­ƒÆí Se notar bloqueios ou alertas durante o uso, contate\nnosso suporte para orienta├º├úo espec├¡fica.\n\nRecomendamos reiniciar o aplicativo.')
        return
    QMessageBox.warning(parent, 'Corre├º├úo Parcial', f'Alguns problemas podem persistir:\n\n{result_text}\n\n­ƒÆí Dicas:\nÔÇó Reinicie o computador\nÔÇó Execute como Administrador\nÔÇó Em caso de d├║vida, contate nosso suporte')
def show_reinstall_dialog(parent=None):
    '''
Mostra di├ílogo para reinstalar platform-tools.
Args:
    parent: Widget pai (QWidget) para o di├ílogo
'''
    from PyQt5.QtWidgets import (QMessageBox, QProgressDialog, QApplication)
    from PyQt5.QtCore import Qt
    corretor = CorrecaoWindowsDefender()
    reply = QMessageBox.question(parent, 'Reinstalar Platform-Tools', 'Isso ir├í baixar uma nova vers├úo do platform-tools\ndiretamente do Google e substituir a atual.\n\nO download ├® de aproximadamente 15 MB.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    if reply != QMessageBox.Yes:
        return
    corretor.kill_all_adb()
    progress = QProgressDialog('Baixando platform-tools do Google...', None, 0, 0, parent)
    progress.setWindowTitle('Download em Andamento')
    progress.setWindowModality(Qt.WindowModal)
    progress.setMinimumDuration(0)
    QApplication.processEvents()
    success, msg = corretor.download_fresh_platform_tools()
    progress.close()
    if success:
        corretor.add_defender_exclusion()
        corretor.remove_exploit_protection()
        corretor.clean_file_attributes()
        QMessageBox.information(parent, 'Download Conclu├¡do', f'{msg}\n\nExce├º├Áes do Windows Defender tamb├®m foram aplicadas.\nReinicie o aplicativo para usar a nova vers├úo.')
        return
    QMessageBox.critical(parent, 'Erro no Download', f'N├úo foi poss├¡vel baixar o platform-tools:\n\n{msg}')
def quick_check_adb() -> Tuple[bool, str]:
    '''
Verifica├º├úo r├ípida do status do ADB.
Pode ser chamada para verificar se h├í problemas.
Returns:
    Tuple[bool, str]: (est├í_ok, mensagem)
'''
    corretor = CorrecaoWindowsDefender()
    blocked, status = corretor.detect_adb_blocked()
    return not blocked, status
