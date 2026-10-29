import ctypes
from ctypes import wintypes
from PyQt5.QtWidgets import QWidget, QMessageBox
import subprocess
import platform
import logging
logger = logging.getLogger(__name__)
WDA_NONE = 0
WDA_MONITOR = 1
WDA_EXCLUDEFROMCAPTURE = 17
class DriverSignatureManager:
    '''
    Gerencia a verifica├º├úo de assinatura de drivers do Windows.
    IMPORTANTE: Requer privil├®gios de administrador para modificar.
    Necess├írio reiniciar o PC ap├│s altera├º├Áes.
    Uso tipico para tecnicos:
    - Instalar drivers de aparelhos em modo download
    - Instalar drivers de boxes profissionais
    - Instalar drivers de ferramentas tecnicas
    '''
    @staticmethod
    def check_status() -> dict:
        '''
Verifica o status atual das configura├º├Áes de assinatura de drivers.
Returns:
    dict: Dicion├írio com status de cada configura├º├úo
        - testsigning: bool ou None (se n├úo conseguiu verificar)
        - integrity_checks_disabled: bool ou None
        - nointegritychecks: bool ou None
        - error: str ou None (mensagem de erro se houver)
'''
        result = {'testsigning': None, 'integrity_checks_disabled': None, 'nointegritychecks': None, 'error': None}
        if platform.system() != 'Windows':
            result['error'] = 'Esta fun├º├úo s├│ est├í dispon├¡vel no Windows'
            return result
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            proc = subprocess.run(['bcdedit', '/enum', '{current}'], capture_output=True, text=True, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
            output = proc.stdout.lower()
            if 'testsigning' in output:
                result['testsigning'] = 'yes' in output.split('testsigning')[1].split('\n')[0]
            else:
                result['testsigning'] = False
            if 'nointegritychecks' in output:
                result['nointegritychecks'] = 'yes' in output.split('nointegritychecks')[1].split('\n')[0]
            else:
                result['nointegritychecks'] = False
            if 'loadoptions' in output:
                loadoptions_line = output.split('loadoptions')[1].split('\n')[0]
                result['integrity_checks_disabled'] = 'disable_integrity_checks' in loadoptions_line
            else:
                result['integrity_checks_disabled'] = False
            logger.info(f'Status Driver Signature: {result}')
        except FileNotFoundError:
            result['error'] = 'bcdedit n├úo encontrado'
        except PermissionError:
            result['error'] = 'Permiss├úo negada. Execute como administrador.'
        except Exception as e:
            result['error'] = str(e)
            logger.error(f'Erro ao verificar status: {e}')
        return result
    @staticmethod
    def is_admin() -> bool:
        '''Verifica se o processo est├í rodando como administrador'''
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    @staticmethod
    def enable_test_signing() -> tuple:
        '''
Habilita o Test Signing Mode (permite drivers n├úo assinados).
Returns:
    tuple: (sucesso: bool, mensagem: str)
'''
        if not DriverSignatureManager.is_admin():
            return (False, 'Necess├írio executar como Administrador')
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            proc1 = subprocess.run(['bcdedit', '/set', 'testsigning', 'on'], capture_output=True, text=True, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
            if proc1.returncode != 0:
                erro = (proc1.stderr or proc1.stdout).lower()
                if 'secure boot' in erro:
                    return (False, 'Desative o Secure Boot no BIOS.')
                if 'protected' in erro or 'protegido' in erro:
                    return (False, 'Desative o Secure Boot no BIOS.')
                return (False, 'Falha ao aplicar. Tente como Administrador.')
            logger.info('Test Signing habilitado')
            return (True, 'Habilitado. Reinicie o PC.')
        except Exception as e:
            logger.error(f'Erro ao habilitar Test Signing: {e}')
            return False, f'Erro: {str(e)}'
    @staticmethod
    def disable_test_signing() -> tuple:
        '''
Desabilita o Test Signing Mode.
Returns:
    tuple: (sucesso: bool, mensagem: str)
'''
        if not DriverSignatureManager.is_admin():
            return (False, 'Necess├írio executar como Administrador')
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            proc = subprocess.run(['bcdedit', '/set', 'testsigning', 'off'], capture_output=True, text=True, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
            if proc.returncode != 0:
                return (False, 'Falha ao desativar.')
            logger.info('Test Signing desabilitado')
            return (True, 'Desativado. Reinicie o PC.')
        except Exception as e:
            logger.error(f'Erro ao desabilitar Test Signing: {e}')
            return (False, 'Falha ao desativar.')
    @staticmethod
    def disable_integrity_checks() -> tuple:
        '''
Desabilita verifica├º├úo de integridade de drivers.
AVISO: Use apenas em m├íquinas de desenvolvimento/unlock.
Returns:
    tuple: (sucesso: bool, mensagem: str)
'''
        if not DriverSignatureManager.is_admin():
            return (False, 'Necess├írio executar como Administrador')
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            proc1 = subprocess.run(['bcdedit', '/set', 'nointegritychecks', 'on'], capture_output=True, text=True, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
            proc2 = subprocess.run(['bcdedit', '/set', 'loadoptions', 'DISABLE_INTEGRITY_CHECKS'], capture_output=True, text=True, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
            if proc1.returncode != 0 and proc2.returncode != 0:
                error_msg = (proc1.stderr or proc1.stdout or proc2.stderr or proc2.stdout).lower()
                if 'secure boot' in error_msg or 'protected' in error_msg or 'protegido' in error_msg:
                    return (False, 'Desative o Secure Boot no BIOS.')
                return (False, 'Falha ao aplicar.')
            logger.info('Integrity Checks desabilitados')
            return (True, 'Habilitado. Reinicie o PC.')
        except Exception as e:
            logger.error(f'Erro ao desabilitar Integrity Checks: {e}')
            return (False, 'Falha ao aplicar.')
    @staticmethod
    def enable_integrity_checks() -> tuple:
        '''
Reabilita verifica├º├úo de integridade de drivers.
Returns:
    tuple: (sucesso: bool, mensagem: str)
'''
        if not DriverSignatureManager.is_admin():
            return (False, 'Necess├írio executar como Administrador')
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            subprocess.run(['bcdedit', '/set', 'nointegritychecks', 'off'], capture_output=True, text=True, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(['bcdedit', '/deletevalue', 'loadoptions'], capture_output=True, text=True, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
            logger.info('Integrity Checks reabilitados')
            return (True, 'Restaurado. Reinicie o PC.')
        except Exception as e:
            logger.error(f'Erro ao reabilitar Integrity Checks: {e}')
            return (False, 'Falha ao restaurar.')
    @staticmethod
    def get_status_formatted() -> str:
        '''
Retorna status formatado para exibi├º├úo no terminal/log.
Returns:
    str: Status formatado com emojis
'''
        status = DriverSignatureManager.check_status()
        if status['error']:
            return f'ÔØî Erro ao verificar: {status['error']}'
        lines = ['ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ', '       DRIVER SIGNATURE ENFORCEMENT        ', 'ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ']
        if status['testsigning']:
            lines.append('Ô£à Test Signing          : HABILITADO')
        else:
            lines.append('­ƒöÆ Test Signing          : Desabilitado')
        if status['nointegritychecks']:
            lines.append('Ô£à No Integrity Checks   : HABILITADO')
        else:
            lines.append('­ƒöÆ No Integrity Checks   : Desabilitado')
        if status['integrity_checks_disabled']:
            lines.append('Ô£à DISABLE_INTEGRITY     : HABILITADO')
        else:
            lines.append('­ƒöÆ DISABLE_INTEGRITY     : Desabilitado')
        lines.append('ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ')
        all_disabled = status['testsigning'] and (status['nointegritychecks'] or status['integrity_checks_disabled'])
        if all_disabled:
            lines.append('Ô£à Sistema pronto para drivers n├úo assinados')
        else:
            lines.append('ÔÜá´©Å Drivers n├úo assinados podem n├úo funcionar')
            lines.append("­ƒÆí Use 'Habilitar Drivers N├úo Assinados' no menu Ajustes")
        return '\n'.join(lines)
def protect_window_from_capture(window: QWidget, enable: bool=True) -> bool:
    '''
Protege uma janela contra capturas de tela usando SetWindowDisplayAffinity.
Args:
    window: A janela QWidget que ser├í protegida
    enable: True para ativar a prote├º├úo, False para desativar
Returns:
    bool: True se a opera├º├úo foi bem-sucedida, False caso contr├írio
'''
    try:
        user32 = ctypes.WinDLL('user32')
        SetWindowDisplayAffinity = user32.SetWindowDisplayAffinity
        SetWindowDisplayAffinity.argtypes = [wintypes.HWND, ctypes.c_uint]
        SetWindowDisplayAffinity.restype = wintypes.BOOL
        hwnd = int(window.winId())
        affinity = WDA_MONITOR if enable else WDA_NONE
        result = SetWindowDisplayAffinity(hwnd, affinity)
        return bool(result)
    except Exception as e:
        print(f'Erro ao proteger janela: {e}')
        return False
def protect_window_from_capture_extended(window: QWidget, enable: bool=True) -> bool:
    '''
Vers├úo estendida que tenta usar o modo mais recente de prote├º├úo (WDA_EXCLUDEFROMCAPTURE)
e volta para o modo legado se necess├írio.
Args:
    window: A janela QWidget que ser├í protegida
    enable: True para ativar a prote├º├úo, False para desativar
Returns:
    bool: True se a opera├º├úo foi bem-sucedida, False caso contr├írio
'''
    if not enable:
        return protect_window_from_capture(window, False)
    try:
        user32 = ctypes.WinDLL('user32')
        SetWindowDisplayAffinity = user32.SetWindowDisplayAffinity
        SetWindowDisplayAffinity.argtypes = [wintypes.HWND, ctypes.c_uint]
        SetWindowDisplayAffinity.restype = wintypes.BOOL
        hwnd = int(window.winId())
        result = SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        if result:
            return True
        return protect_window_from_capture(window, True)
    except Exception as e:
        print(f'Erro ao proteger janela (modo estendido): {e}')
        return False
