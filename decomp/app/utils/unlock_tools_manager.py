'''
Unlock Tools Manager - Gerenciador de Ferramentas Union Unlock
================================================================
Gerencia extra├º├úo e limpeza do ZIP protegido (AES-256) contendo
os bin├írios da pasta union_unlock/tools/.
Padr├úo id├¬ntico ao MTK Manager (mtk_manager.py) j├í em produ├º├úo.
AUTOR: RESTORECELL - TECH UNION SOLUTIONS
DATA: 2026-03-25
VERS├âO: 1.1
FLUXO:
  1. Usu├írio clica "Ferramentas" ÔåÆ DiagnosticoAndroid.__init__()
  2. Se ZIP existe e bin├írios n├úo est├úo presentes ÔåÆ extrai com progresso
  3. Se bin├írios j├í est├úo presentes de sess├úo anterior ÔåÆ registra para limpeza
  4. Ao fechar ÔåÆ limpa bin├írios extra├¡dos, mant├®m ZIP
  5. atexit handler garante limpeza mesmo se closeEvent n├úo disparar
'''
import os
import sys
import shutil
import atexit
import logging
from typing import (Optional, List, Tuple)
from app.utils._app_cfg import REFS
logger = logging.getLogger('UnlockToolsManager')
_UNLOCK_ZIP_NAME = 'unlock_tools.zip'
_UNLOCK_ZIP_KEY = REFS.PK_Z
_BINARIOS_CHAVE = ['mtk.exe', 'emmcdl.exe', 'adb.exe', 'edl-ng.exe']
class UnlockToolsManager:
    '''Gerenciador de extra├º├úo/limpeza do ZIP de ferramentas union_unlock'''
    def __init__(self):
        self._tools_dir = self._resolver_tools_dir()
        self._zip_path = None
        self._arquivos_para_limpar = []
        self._deve_limpar = False
        self._atexit_registrado = False
    def _resolver_tools_dir(self) -> str:
        try:
            from app.utils.path_manager import PathManager
            pm_dir = PathManager.get_unlock_tools_dir()
            if pm_dir and os.path.isdir(pm_dir):
                return pm_dir
        except Exception:
            pass
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
            candidatos = [os.path.join(base, '_internal', 'app', 'views', 'union_unlock', 'tools'), os.path.join(base, 'app', 'views', 'union_unlock', 'tools')]
        else:
            utils_dir = os.path.dirname(os.path.abspath(__file__))
            app_dir = os.path.dirname(utils_dir)
            candidatos = [os.path.join(app_dir, 'views', 'union_unlock', 'tools')]
        for caminho in candidatos:
            if not os.path.isdir(caminho):
                continue
            return caminho
        return candidatos[0]
    def _localizar_zip(self) -> Optional[str]:
        zip_path = os.path.join(self._tools_dir, _UNLOCK_ZIP_NAME)
        if os.path.isfile(zip_path):
            self._zip_path = zip_path
            return zip_path
    def _registrar_atexit(self):
        if not self._atexit_registrado:
            atexit.register(self.limpar)
            self._atexit_registrado = True
    def _mapear_arquivos_do_zip(self) -> List[str]:
        '''Le o ZIP e retorna lista de caminhos absolutos dos membros'''
        try:
            import pyzipper
        except ImportError:
            return []
        zip_path = self._localizar_zip()
        if not zip_path:
            return []
        caminhos = []
        try:
            with pyzipper.AESZipFile(zip_path, 'r') as zf:
                zf.setpassword(_UNLOCK_ZIP_KEY)
                for membro in zf.namelist():
                    if membro.endswith('/'):
                        continue
                    nome = os.path.basename(membro)
                    if nome:
                        subdir = os.path.dirname(membro)
                        if subdir:
                            dest = os.path.join(self._tools_dir, subdir, nome)
                        else:
                            dest = os.path.join(self._tools_dir, nome)
                        caminhos.append(dest)
        except Exception as e:
            logger.debug(f'Erro ao mapear ZIP: {e}')
        return caminhos
    def zip_disponivel(self) -> bool:
        return self._localizar_zip() is not None
    def ja_extraido(self) -> bool:
        for nome in _BINARIOS_CHAVE:
            if os.path.isfile(os.path.join(self._tools_dir, nome)):
                continue
            return False
        return True
    def extrair(self, progress_callback=None) -> Tuple[bool, str]:
        try:
            import pyzipper
        except ImportError:
            logger.error('pyzipper n├úo dispon├¡vel')
            return (False, 'err_module')
        zip_path = self._localizar_zip()
        if not zip_path:
            return (False, 'err_resource')
        try:
            if progress_callback:
                progress_callback(5, 'Verificando recursos...')
            os.makedirs(self._tools_dir, exist_ok=True)
            if progress_callback:
                progress_callback(10, 'Conectando API de Ferramentas...')
            with pyzipper.AESZipFile(zip_path, 'r') as zf:
                zf.setpassword(_UNLOCK_ZIP_KEY)
                membros = zf.namelist()
                total = len(membros)
                if total == 0:
                    return (False, 'err_extract')
                if progress_callback:
                    progress_callback(15, 'Preparando m├│dulos de diagn├│stico...')
                for i, membro in enumerate(membros):
                    if membro.endswith('/'):
                        dir_dest = os.path.join(self._tools_dir, membro)
                        os.makedirs(dir_dest, exist_ok=True)
                        continue
                    nome_arquivo = os.path.basename(membro)
                    if not nome_arquivo:
                        continue
                    subdir = os.path.dirname(membro)
                    if subdir:
                        dir_dest = os.path.join(self._tools_dir, subdir)
                        os.makedirs(dir_dest, exist_ok=True)
                        dest_final = os.path.join(dir_dest, nome_arquivo)
                    else:
                        dest_final = os.path.join(self._tools_dir, nome_arquivo)
                    dados = zf.read(membro)
                    try:
                        try:
                            with open(dest_final, 'wb') as f:
                                f.write(dados)
                        except (PermissionError, OSError):
                            logger.debug('Recurso ocupado, continuando')
                    finally:
                        pass
                    self._arquivos_para_limpar.append(dest_final)
                    if not progress_callback:
                        continue
                    pct = 15 + int((i + 1) / total * 80)
                    progress_callback(pct, f'Carregando ferramentas... ({i + 1}/{total})')
                    continue
        except Exception as e:
            logger.error(f'Erro na extra├º├úo: {e}')
            if 'Bad password' in str(e) or isinstance(e, RuntimeError):
                return (False, 'err_decrypt')
            return (False, 'err_system')
        try:
            self._deve_limpar = True
            self._registrar_atexit()
            if progress_callback:
                progress_callback(100, 'Ferramentas prontas!')
            logger.info(f'Extra├º├úo conclu├¡da: {len(self._arquivos_para_limpar)} arquivos')
        except Exception as e:
            logger.error(f'Erro na extra├º├úo: {e}')
            if 'Bad password' in str(e) or isinstance(e, RuntimeError):
                return (False, 'err_decrypt')
            return (False, 'err_system')
        return (True, 'ok')
    def extrair_com_progresso(self, parent_widget=None) -> bool:
        if not self.zip_disponivel():
            logger.info('ZIP n├úo encontrado, assumindo bin├írios standalone (dev)')
            return True
        if self.ja_extraido():
            logger.info('Bin├írios j├í presentes ÔÇö registrando para limpeza ao fechar')
            self._arquivos_para_limpar = self._mapear_arquivos_do_zip()
            self._deve_limpar = True
            self._registrar_atexit()
            return True
        try:
            from PyQt5.QtWidgets import QProgressDialog, QApplication
            from PyQt5.QtCore import Qt
        except ImportError:
            sucesso, _ = self.extrair()
            return sucesso
        dialog = QProgressDialog(parent_widget)
        dialog.setWindowTitle('Tech Union Solutions')
        dialog.setLabelText('Conectando API de Ferramentas...')
        dialog.setCancelButton(None)
        dialog.setMinimum(0)
        dialog.setMaximum(100)
        dialog.setValue(0)
        dialog.setMinimumWidth(400)
        dialog.setWindowModality(Qt.WindowModal)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)
        dialog.setStyleSheet('\n            QProgressDialog {\n                background-color: #1a1a2e;\n                border: 2px solid #16213e;\n                border-radius: 10px;\n            }\n            QLabel {\n                color: #e94560;\n                font-size: 13px;\n                font-weight: bold;\n                padding: 10px;\n            }\n            QProgressBar {\n                border: 1px solid #16213e;\n                border-radius: 5px;\n                background-color: #0f3460;\n                text-align: center;\n                color: white;\n                font-weight: bold;\n                min-height: 22px;\n            }\n            QProgressBar::chunk {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n                    stop:0 #e94560, stop:1 #0f3460);\n                border-radius: 4px;\n            }\n        ')
        dialog.show()
        QApplication.processEvents()
        def atualizar_progresso(pct, msg):
            dialog.setValue(pct)
            dialog.setLabelText(msg)
            QApplication.processEvents()
        sucesso, resultado = self.extrair(progress_callback=atualizar_progresso)
        dialog.close()
        dialog.deleteLater()
        if not sucesso:
            logger.warning(f'Extra├º├úo falhou: {resultado}')
        return sucesso
    def _kill_adb_server(self):
        '''Encerra daemon para liberar locks.'''
        import subprocess
        try:
            _bin = os.path.join(self._tools_dir, 'adb.exe')
            if not os.path.isfile(_bin):
                _bin = shutil.which('adb')
            if _bin:
                subprocess.run([_bin, 'kill-server'], capture_output=True, timeout=3, creationflags=134217728)
                return
        except Exception:
            pass
    def limpar(self):
        if not self._deve_limpar:
            return
        self._kill_adb_server()
        removidos = 0
        for caminho in self._arquivos_para_limpar:
            try:
                if os.path.isfile(caminho):
                    os.remove(caminho)
                    removidos += 1
            except Exception:
                continue
        self._arquivos_para_limpar.clear()
        self._deve_limpar = False
        if removidos > 0:
            logger.info(f'Limpeza: {removidos} recursos liberados')
    def get_tools_dir(self) -> str:
        return self._tools_dir
_instance: Optional[UnlockToolsManager] = None
def get_unlock_tools_manager() -> UnlockToolsManager:
    global _instance
    if _instance is None:
        _instance = UnlockToolsManager()
    return _instance
def limpar_tools_unlock():
    if _instance is not None:
        _instance.limpar()
