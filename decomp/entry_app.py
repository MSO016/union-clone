pycdc-new.exe : D:\MSO\Projects\union-clone\pyz\RESTORECELL.exe_extracted\app.pyc: WARNING: decompilation incomplete 
(Python 3.13)
No linha:7 caractere:1
+ & "$t\pycdc-new.exe" $test 2>&1 | Out-File "D:\MSO\Projects\union-clo ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (D:\MSO\Projects...e (Python 3.13):String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
import sys
import os
import ctypes
if sys.platform == 'win32':
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass
if getattr(sys, 'frozen', False):
    try:
        import win32com
        _gen_py = os.path.join(os.environ.get('LOCALAPPDATA', os.environ.get('TEMP', os.path.expanduser('~'))), 'RESTORECELL', 'gen_py')
        os.makedirs(_gen_py, exist_ok=True)
        win32com.__gen_path__ = _gen_py
    except Exception:
        pass
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import (QSharedMemory, Qt, QSettings)
try:
    from app.utils._import_hook import activate as _activate_hook
    _activate_hook()
except Exception:
    pass
try:
    from app.views.login_window import LoginWindow
    from app.utils.path_manager import PathManager
except ImportError as _imp_err:
    _msg_low = str(_imp_err).lower()
    _is_policy_block = any((_k in _msg_low for _k in ('dll load failed', 'policy', 'pol├¡', 'bloqueou', 'blocked')))
    if _is_policy_block:
        _user_msg = "TECH UNION SOLUTIONS - Inicializacao Bloqueada\n\nUm componente do sistema foi bloqueado pela politica de\nseguranca do Windows.\n\nPossiveis solucoes:\n  1. Clique com o botao direito no programa e escolha\n     'Executar como Administrador'\n\n  2. Mova o programa para a pasta C:\\UNION\\ e tente novamente\n\n  3. No Windows 11: Configuracoes > Privacidade e seguranca >\n     Seguranca do Windows > Controle de aplicativos e navegador\n     > desative o 'Controle inteligente de aplicativos'\n\n  4. Se o problema persistir, contate o suporte tecnico\n\nCodigo: INIT-001"
    else:
        _user_msg = 'TECH UNION SOLUTIONS - Erro de Inicializacao\n\nNao foi possivel iniciar um componente do sistema.\n\nTente reinstalar o aplicativo ou contate o suporte tecnico.\n\nCodigo: INIT-002'
    try:
        import datetime as _dt
        _log_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.environ.get('TEMP', os.path.expanduser('~'))), 'RESTORECELL')
        os.makedirs(_log_dir, exist_ok=True)
        with open(os.path.join(_log_dir, 'startup_error.log'), 'a', encoding='utf-8') as _lf:
            _lf.write(f'[{_dt.datetime.now().isoformat()}] {'INIT-001' if _is_policy_block else 'INIT-002'} type={type(_imp_err).__name__} is_policy={_is_policy_block}\n')
    except Exception:
        pass
    if not None:
        pass
    try:
        if sys.platform == 'win32':
            ctypes.windll.user32.MessageBoxW(0, _user_msg, 'TECH UNION SOLUTIONS', 16)
        else:
            print(_user_msg)
    except Exception:
        pass
    sys.exit(1)

def is_admin():
    '''Verifica se o programa est├í rodando como administrador'''

    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    '''
    Solicita eleva├º├úo para administrador de forma gentil.
    Retorna True se j├í ├® admin ou se o usu├írio aceitou reiniciar.
    Retorna False se o usu├írio recusou (continua sem admin).
    '''

    if is_admin():
        return True
    MB_YESNO = 4
    MB_ICONQUESTION = 32
    IDYES = 6
    resultado = ctypes.windll.user32.MessageBoxW(0, 'TECH UNION SOLUTIONS\n\nPara melhor desempenho do sistema,\nrecomendamos executar como Administrador.\n\nDeseja continuar como Administrador?\n\nÔÇó SIM = Melhor desempenho (recomendado)\nÔÇó N├âO = Continuar normalmente\n\nÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ\nAo prosseguir, voc├¬ declara ser t├®cnico autorizado\ne assume total responsabilidade pelo uso desta\nferramenta. Consulte os Termos de Uso para mais\ninforma├º├Áes.', 'TECH UNION SOLUTIONS', MB_YESNO | MB_ICONQUESTION)
    if resultado == IDYES:
        try:
            ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, ' '.join(sys.argv), None, 1)
            sys.exit(0)
        except Exception as e:
            ctypes.windll.user32.MessageBoxW(0, 'N├úo foi poss├¡vel obter permiss├Áes.\n\nO programa continuar├í normalmente.\nSe tiver problemas, tente executar como Administrador.', 'Aviso', 48)
            return False
        return True
    print('[AVISO] Executando SEM permissoes de administrador')
    print('   Algumas funcoes de ADB/Fastboot podem apresentar erro 0xc0000005')
    return False

if __name__ == '__main__':
    try:
        admin_status = run_as_admin()
    except KeyboardInterrupt:
        sys.exit(0)
    if admin_status:
        print('[OK] Executando como Administrador')
    if hasattr(Qt, 'AA_ShareOpenGLContexts'):
        QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    try:
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        print('[OK] PyQtWebEngine inicializado com sucesso')
    except ImportError:
        print('[AVISO] PyQtWebEngine nao disponivel - navegador interno desabilitado')
    except Exception as e:
        print(f'[AVISO] Erro ao inicializar PyQtWebEngine: {type(e).__name__}')
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    try:
        _user32 = ctypes.windll.user32
        _gdi32 = ctypes.windll.gdi32
        _hdc = _user32.GetDC(0)
        if _hdc:
            _phys_w = _gdi32.GetDeviceCaps(_hdc, 118)
            _phys_h = _gdi32.GetDeviceCaps(_hdc, 117)
            _dpi = _gdi32.GetDeviceCaps(_hdc, 88)
            _user32.ReleaseDC(0, _hdc)
            _scale = round(_dpi / 96.0, 2)
            _log_w = int(_phys_w / _scale)
            _log_h = int(_phys_h / _scale)
            print(f'[DPI] Fisico={_phys_w}x{_phys_h} Logico={_log_w}x{_log_h} Escala={int(_scale * 100)}% DPI={_dpi}')
        else:
            print('[DPI] GetDC falhou (RDP headless?) - HiDPI ativado por padrao')
    except Exception:
        print('[DPI] Diagnostico de resolucao falhou - HiDPI ativado por padrao')
    app = QApplication(sys.argv)
    shared_memory = QSharedMemory('UNION_TECHNICAL_SINGLE_INSTANCE')
    if shared_memory.attach():
        QMessageBox.warning(None, 'UNION TECHNICAL', 'O UNION TECHNICAL j├í est├í em execu├º├úo!\n\nVerifique na barra de tarefas ou feche a aplica├º├úo anterior antes de abrir novamente.')
        sys.exit(1)
    if not shared_memory.create(1):
        QMessageBox.warning(None, 'UNION TECHNICAL', 'N├úo foi poss├¡vel iniciar a aplica├º├úo.\n\nO UNION TECHNICAL pode j├í estar em execu├º├úo.')
        sys.exit(1)
    try:
        from app.utils._cfg_probe import (scan as _guard_scan, has_blocking as _guard_has_blocking, is_debugger_attached as _guard_is_dbg, generic_user_message as _guard_msg)
        _guard_dets = _guard_scan()
        _guard_dbg = _guard_is_dbg()
        if _guard_has_blocking(_guard_dets) or _guard_dbg:
            QMessageBox.critical(None, 'TECH UNION SOLUTIONS', _guard_msg('pre_login'))
        try:
            shared_memory.detach()
        except Exception:
            pass
        else:
            sys.exit(0)
    except SystemExit:
        raise
    except Exception:
        pass
    app.setStyle('Fusion')
    _settings = QSettings('TechUnion', 'UNION')
    if _settings.value('theme/dark_mode', False, type=bool):
        try:
            import qdarkstyle
            app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
            print('[TEMA] Tema escuro (QDarkStyle) aplicado')
        except Exception as e:
            print(f'[AVISO] qdarkstyle indisponivel: {type(e).__name__}')
    else:
        print('[TEMA] Tema claro (Fusion padrao)')
    icon = QIcon(PathManager.get_resource_path('icon.png'))
    app.setWindowIcon(icon)
    login = LoginWindow()
    login.show()
    exit_code = app.exec_()
    shared_memory.detach()
    sys.exit(exit_code)
else:
    try:
        if sys.platform == 'win32':
            ctypes.windll.user32.MessageBoxW(0, _user_msg, 'TECH UNION SOLUTIONS', 16)
        else:
            print(_user_msg)
    except Exception:
        pass
    sys.exit(1)
    _imp_err = None
    del _imp_err, _imp_err
    _imp_err = None
# WARNING: Decompyle incomplete
