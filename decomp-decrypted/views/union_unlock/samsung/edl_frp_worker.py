import os
import sys
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal
class EdlFrpWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, frp_edl_path: str, loader_path: str, modelo: str):
        super().__init__()
        self.frp_edl_path = frp_edl_path
        self.loader_path = loader_path
        self.modelo = modelo
        self._cancelado = False
    def _log(self, msg: str):
        print(msg, flush=True)
        self.log_signal.emit(msg)
    def run(self):
        try:
            if not (os.path.exists(self.frp_edl_path) and os.path.exists(self.loader_path)):
                self.finished_signal.emit(False, 'Componente n├úo encontrado!\n\nReinstale o programa ou entre\nem contato com o suporte.')
                self.status_signal.emit('error')
                return
            self._log('=======================================================')
            self._log('  TECH UNION SOLUTIONS - FRP SAMSUNG EDL')
            self._log(f'  Modelo: {self.modelo}')
            self._log('  M├®todo: Qualcomm EDL + FRP_EDL')
            self._log('=======================================================')
            self._log('')
            self._log('Ô£à FRP_EDL.exe .: Encontrado')
            self._log(f'Ô£à Loader .....: {os.path.basename(self.loader_path)}')
            self._log('')
            self._log('­ƒô▒ Aguardando dispositivo em modo EDL...')
            self._log('   MODO EDL REQUER TEST POINT:')
            self._log('   1. Abra o aparelho')
            self._log('   2. Localize o ponto EDL na placa')
            self._log('   3. Faca curto no Test Point + conecte USB')
            self._log('')
            self._log('-------------------------------------------------------')
            self.status_signal.emit('waiting')
            self.progress_signal.emit(10)
            comando_edl = [self.frp_edl_path, '-m', 'ufs', '-l', self.loader_path, 'resetfrp']
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            processo = subprocess.Popen(comando_edl, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.path.dirname(self.frp_edl_path), creationflags=creationflags)
            device_connected = False
            frp_done = False
            erro_detectado = None
            while True:
                if self._cancelado:
                    processo.terminate()
                    self._log('')
                    self._log('Ôøö Processo cancelado pelo usu├írio')
                    self.finished_signal.emit(False, 'Cancelado')
                    self.status_signal.emit('error')
                    return
                linha = processo.stdout.readline()
                if not linha and processo.poll() is not None:
                    break
                if linha:
                    linha_limpa = linha.rstrip()
                    self._log(linha_limpa)
                    linha_lower = linha_limpa.lower()
                    if 'automatic port detection failed' in linha_lower:
                        erro_detectado = 'no_device'
                    elif 'failed to send loader' in linha_lower:
                        erro_detectado = 'loader_failed'
                    if 'loader sent' in linha_lower and erro_detectado == 'loader_failed':
                        erro_detectado = None
                    if not device_connected:
                        frases_conexao = ['auto-detected port', 'device detected', 'loader sent']
                        if any((frase in linha_lower for frase in frases_conexao)):
                            device_connected = True
                            self.status_signal.emit('connected')
                            self.progress_signal.emit(40)
                            self._log('')
                            self._log('Ô£à Dispositivo detectado e conectado!')
                            self._log('')
                    if 'reading partition' in linha_lower:
                        self.progress_signal.emit(50)
                    elif 'persist' in linha_lower and 'done' in linha_lower:
                        self.progress_signal.emit(60)
                    elif 'frp' in linha_lower and 'done' in linha_lower:
                        frp_done = True
                        self.progress_signal.emit(80)
                    elif 'persistent' in linha_lower and 'done' in linha_lower:
                        self.progress_signal.emit(85)
                    elif 'rebooting' in linha_lower:
                        frp_done = True
                        self.progress_signal.emit(95)
            retcode = processo.wait()
            if frp_done:
                erro_detectado = None
            if erro_detectado == 'no_device':
                self.status_signal.emit('error')
                self._log('')
                self._log('Nenhum dispositivo detectado!')
                self.finished_signal.emit(False, 'Dispositivo n├úo detectado!\n\nConecte em modo EDL (Qualcomm 9008)')
                return
            if erro_detectado == 'loader_failed' and not device_connected:
                self.status_signal.emit('error')
                self._log('')
                self._log('N├úo foi poss├¡vel conectar ao dispositivo.')
                self.finished_signal.emit(False, 'N├úo foi poss├¡vel conectar.\nReconecte o dispositivo em modo EDL.')
                return
            if not device_connected:
                self.status_signal.emit('error')
                self._log('')
                self._log('Dispositivo n├úo conectado!')
                self.finished_signal.emit(False, 'Dispositivo n├úo conectado!\n\nEntre em modo EDL antes de iniciar.')
                return
            if not frp_done:
                if retcode != 0:
                    self.status_signal.emit('error')
                    self._log('')
                    self.finished_signal.emit(False, 'Erro no processo.\nReconecte e tente novamente.')
                    return
            self.progress_signal.emit(100)
            self.status_signal.emit('success')
            self._log('')
            self._log('=======================================================')
            self._log('  Ô£à PROCESSO FINALIZADO COM SUCESSO!')
            self._log('=======================================================')
            self._log('')
            self._log('­ƒô▒ FRP removido com sucesso!')
            self._log('ÔÅ│ O dispositivo vai reiniciar automaticamente')
            self._log('­ƒÆí Configure normalmente ap├│s reiniciar!')
            self._log('')
            self._log('=======================================================')
            self._log('  TECH UNION SOLUTIONS - Valeu, t├®cnico! ­ƒÆ¬­ƒçº­ƒçÀ')
            self._log('=======================================================')
            self.finished_signal.emit(True, 'FRP removido com sucesso!')
            return
        except OSError as e:
            self.status_signal.emit('error')
            if hasattr(e, 'winerror') and e.winerror == 740:
                self.finished_signal.emit(False, "Execute como Administrador!\n\nClique com bot├úo direito no programa\ne selecione 'Executar como administrador'.")
        except Exception:
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado.\n\nReinstale o programa ou entre\nem contato com o suporte.')
