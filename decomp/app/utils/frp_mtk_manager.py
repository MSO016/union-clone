'''
FRP MTK Manager - Gerenciador de Execu├º├úo do FRP Xiaomi MTK
===========================================================
Gerencia a execu├º├úo do FRP Xiaomi MTK como processo separado,
garantindo isolamento completo de stdout/stderr e console pr├│prio.
IGUAL AO MTK MANAGER - PROCESSO SEPARADO!
AUTOR: RESTORECELL - TECH UNION SOLUTIONS
DATA: 15/11/2025
VERS├âO: 2.0.0
'''
import os
import sys
import subprocess
from typing import Optional, Tuple
from PyQt5.QtWidgets import QWidget, QMessageBox
class FRPMTKManager:
    '''Gerenciador de execu├º├úo do FRP Xiaomi MTK - PROCESSO SEPARADO'''
    def __init__(self):
        '''Inicializa o gerenciador FRP MTK'''
        self.frp_process = None
        self.frp_path = self._determinar_caminho_frp()
    def _determinar_caminho_frp(self) -> str:
        '''
Determina o caminho correto do FRP baseado no ambiente
Returns:
    str: Caminho para o script Python do FRP (.py ou .pyc)
'''
        try:
            from app.utils.path_manager import PathManager
            pm_frp = PathManager.get_frp_script()
            if pm_frp:
                return pm_frp
        except Exception:
            pass
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
            possible_paths = [os.path.join(base_path, '_internal', 'app', 'utils', 'frp_erase_xiaomi.pyc'), os.path.join(base_path, '_internal', 'app', 'utils', 'frp_erase_xiaomi.py'), os.path.join(base_path, 'app', 'utils', 'frp_erase_xiaomi.pyc'), os.path.join(base_path, 'app', 'utils', 'frp_erase_xiaomi.py')]
            for path in possible_paths:
                if not os.path.exists(path):
                    continue
                return path
            print('FRP script nao encontrado')
            for p in possible_paths:
                existe = 'Ô£à' if os.path.exists(p) else 'ÔØî'
                print(f'   {existe} {p}')
            return possible_paths[0]
        current_dir = os.path.dirname(os.path.abspath(__file__))
        frp_script = os.path.join(current_dir, 'frp_erase_xiaomi.py')
        print(f'Ô£à FRP encontrado (desenvolvimento): {frp_script}')
        return frp_script
    def verificar_disponibilidade(self) -> Tuple[bool, str]:
        '''
Verifica se o FRP est├í dispon├¡vel e pode ser executado
Returns:
    Tuple[bool, str]: (dispon├¡vel, mensagem_amigavel)
'''
        if not os.path.exists(self.frp_path):
            print(f'[DEBUG] FRP n├úo encontrado em: {self.frp_path}')
            return (False, 'ÔÜá´©Å M├│dulo FRP Xiaomi MTK n├úo encontrado.\n\n­ƒôï Poss├¡veis causas:\nÔÇó Instala├º├úo incompleta do software\nÔÇó Arquivos corrompidos ou faltando\n\n­ƒÆí Solu├º├úo:\nÔÇó Reinstale o TECH UNION SOLUTIONS\nÔÇó Entre em contato com o suporte t├®cnico')
        if not (self.frp_path.endswith('.py') or self.frp_path.endswith('.pyc')):
            print(f'[DEBUG] Arquivo FRP inv├ílido: {self.frp_path}')
            return (False, 'ÔÜá´©Å M├│dulo FRP Xiaomi MTK corrompido.\n\n­ƒÆí Solu├º├úo:\nÔÇó Reinstale o TECH UNION SOLUTIONS\nÔÇó Verifique a integridade dos arquivos')
        if not sys.executable:
            print('[DEBUG] Python n├úo encontrado no sistema')
            return (False, 'ÔÜá´©Å Python n├úo detectado no sistema.\n\n­ƒôï O FRP Xiaomi MTK precisa do Python instalado.\n\n­ƒÆí Solu├º├úo:\nÔÇó Entre em contato com o suporte t├®cnico')
        formato = 'bytecode (.pyc)' if self.frp_path.endswith('.pyc') else 'script (.py)'
        print(f'[DEBUG] FRP dispon├¡vel: {formato}')
        return (True, 'Ô£à FRP Xiaomi MTK pronto para uso')
    def esta_rodando(self) -> bool:
        '''
Verifica se o FRP est├í rodando
Returns:
    bool: True se o processo FRP est├í ativo
'''
        if self.frp_process is None:
            return False
        return self.frp_process.poll() is None
    def abrir(self, parent: QWidget=None) -> Tuple[bool, str]:
        '''
Abre o FRP Xiaomi MTK SEM console vis├¡vel (modo stealth)
FRP sempre roda como script Python (.py), nunca compilado
Returns:
    Tuple[bool, str]: (sucesso, mensagem)
'''
        try:
            disponivel, mensagem = self.verificar_disponibilidade()
            if not disponivel:
                return False, mensagem
            if self.esta_rodando():
                return (True, 'FRP Xiaomi MTK j├í est├í em execu├º├úo')
            if parent:
                reply = self._mostrar_aviso_responsabilidade(parent)
                if not reply:
                    return (False, 'Usu├írio cancelou abertura do FRP')
            python_executable = sys.executable
            if getattr(sys, 'frozen', False):
                import shutil
                system_python = shutil.which('python')
                if not system_python:
                    system_python = shutil.which('python3')
                if system_python:
                    python_executable = system_python
                    print(f'­ƒöº [COMPILADO] Usando Python do sistema: {python_executable}')
                else:
                    possible_paths = ['C:\\Python39\\python.exe', 'C:\\Python310\\python.exe', 'C:\\Python311\\python.exe', 'C:\\Program Files\\Python39\\python.exe', 'C:\\Program Files\\Python310\\python.exe', 'C:\\Program Files\\Python311\\python.exe', os.path.expandvars('%LOCALAPPDATA%\\Programs\\Python\\Python39\\python.exe'), os.path.expandvars('%LOCALAPPDATA%\\Programs\\Python\\Python310\\python.exe'), os.path.expandvars('%LOCALAPPDATA%\\Programs\\Python\\Python311\\python.exe')]
                    for path in possible_paths:
                        if not os.path.exists(path):
                            continue
                        python_executable = path
                        print(f'­ƒöº [COMPILADO] Python encontrado: {python_executable}')
                    else:
                        print('[DEBUG] Python n├úo encontrado em nenhum path comum')
                        return (False, "ÔÜá´©Å FRP Xiaomi MTK requer Python instalado.\n\n­ƒôï O que aconteceu:\nO Python n├úo foi detectado no seu computador.\n\n­ƒÆí Solu├º├Áes:\n1´©ÅÔâú Entre em contato com o suporte t├®cnico\n2´©ÅÔâú WhatsApp: (85) 99750-7465\n3´©ÅÔâú Mencione: 'FRP MTK - Python n├úo encontrado'\n\nÔä╣´©Å O suporte ir├í orient├í-lo na configura├º├úo.")
            comando = [python_executable, self.frp_path]
            env = os.environ.copy()
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
                qt_plugin_path = os.path.join(base_path, 'PyQt5', 'Qt5', 'plugins')
                if os.path.exists(qt_plugin_path):
                    env['QT_PLUGIN_PATH'] = qt_plugin_path
                    env['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(qt_plugin_path, 'platforms')
                    print(f'­ƒöº [COMPILADO] QT_PLUGIN_PATH configurado: {qt_plugin_path}')
            if sys.platform == 'win32':
                pythonw_path = None
                python_dir = os.path.dirname(python_executable)
                pythonw_candidate = os.path.join(python_dir, 'pythonw.exe')
                if os.path.exists(pythonw_candidate):
                    pythonw_path = pythonw_candidate
                    comando[0] = pythonw_path
                    print(f'Ô£à Usando pythonw.exe: {pythonw_path}')
                if pythonw_path:
                    self.frp_process = subprocess.Popen(comando, cwd=os.path.dirname(self.frp_path), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    print('ÔÜá´©Å pythonw n├úo encontrado, usando SW_HIDE')
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0
                    self.frp_process = subprocess.Popen(comando, startupinfo=startupinfo, cwd=os.path.dirname(self.frp_path), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                self.frp_process = subprocess.Popen(comando, cwd=os.path.dirname(self.frp_path), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, start_new_session=True)
            print(f'Ô£à FRP Xiaomi MTK iniciado em modo stealth (PID: {self.frp_process.pid})')
            print(f'Ô£à Comando: {' '.join(comando)}')
            return (True, 'Ô£à FRP Xiaomi MTK iniciado com sucesso!')
        except FileNotFoundError as e:
            print(f'ÔØî Arquivo n├úo encontrado: {str(e)}')
            import traceback
            traceback.print_exc()
            return (False, 'ÔÜá´©Å N├úo foi poss├¡vel iniciar o FRP Xiaomi MTK.\n\n­ƒôï Poss├¡vel causa:\nÔÇó Arquivos do m├│dulo FRP est├úo faltando\n\n­ƒÆí Solu├º├úo:\nÔÇó Reinstale o TECH UNION SOLUTIONS\nÔÇó Contate o suporte: (85) 99750-7465')
        except PermissionError as e:
            print(f'ÔØî Erro de permiss├úo: {str(e)}')
            import traceback
            traceback.print_exc()
            return (False, 'ÔÜá´©Å Permiss├úo negada ao iniciar FRP Xiaomi MTK.\n\n­ƒôï Poss├¡veis causas:\nÔÇó Antiv├¡rus bloqueando a execu├º├úo\nÔÇó Falta de privil├®gios administrativos\n\n­ƒÆí Solu├º├Áes:\n1´©ÅÔâú Execute como Administrador\n2´©ÅÔâú Adicione exce├º├úo no antiv├¡rus\n3´©ÅÔâú Contate o suporte se persistir')
        except Exception as e:
            print(f'ÔØî Erro inesperado ao iniciar FRP: {str(e)}')
            import traceback
            traceback.print_exc()
            return (False, "ÔÜá´©Å Erro ao iniciar o FRP Xiaomi MTK.\n\n­ƒÆí Solu├º├úo:\nÔÇó Tente novamente em alguns instantes\nÔÇó Se o erro persistir, contate o suporte\n\n­ƒô× Suporte T├®cnico:\nWhatsApp: (85) 99750-7465\nMencione: 'Erro ao abrir FRP Xiaomi MTK'")
    def fechar(self) -> bool:
        '''
Fecha o processo FRP se estiver rodando
Returns:
    bool: True se conseguiu fechar
'''
        if not self.esta_rodando():
            return True
        try:
            self.frp_process.terminate()
            self.frp_process.wait(timeout=5)
            self.frp_process = None
            return True
        except Exception as e:
            print(f'Erro ao fechar FRP: {e}')
            return False
    def _mostrar_aviso_responsabilidade(self, parent: QWidget) -> bool:
        '''
Mostra aviso de responsabilidade ao usu├írio.
Returns:
    bool: True se usu├írio aceitou, False se cancelou
'''
        reply = QMessageBox.question(parent, '­ƒöº XIAOMI FRP MTK', '<b style="color: #ff9900;">­ƒº¬ Ferramenta em teste - Use por sua conta e risco</b><br><br><b>­ƒô▒ Remove FRP de Xiaomi MTK</b><br>Ô£à Redmi 9A/9C/10A/10C, POCO C3, outros MTK<br>Ô£à Backup autom├ítico antes de apagar<br><br><b>ÔÜá´©Å Importante:</b><br>ÔÇó Recomendado para t├®cnicos experientes<br>ÔÇó Funciona bem, mas em constante evolu├º├úo<br><br><b>ÔØî N├úo funcionou ou ├® Qualcomm?</b><br>ÔÇó Use o <b>Procedimento Remoto UNION</b><br>ÔÇó Dispon├¡vel no bot├úo "FRP XIAOMI REMOTE USB"<br>ÔÇó Suporte para todos os chipsets<br><br><b>­ƒôï Procedimento:</b><br>1. Xiaomi MTK em modo BROM (Vol- + USB)<br>2. Conectar ÔåÆ Aguardar ÔåÆ Apagar FRP<br><br><b style="color: #ff9900;">ÔÜû´©Å Confirmo:</b><br>ÔÇó Sou t├®cnico qualificado<br>ÔÇó Uso por minha conta e risco<br>ÔÇó Fiz backup dos dados<br>', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        return reply == QMessageBox.Yes
_frp_mtk_manager_instance: Optional[FRPMTKManager] = None
def get_frp_mtk_manager() -> FRPMTKManager:
    '''
Obt├®m a inst├óncia singleton do FRPMTKManager
Returns:
    FRPMTKManager: Inst├óncia do gerenciador
'''
    global _frp_mtk_manager_instance
    if _frp_mtk_manager_instance is None:
        _frp_mtk_manager_instance = FRPMTKManager()
    return _frp_mtk_manager_instance
