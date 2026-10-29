import os
import sys
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal
class EdlXiaomiWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, edl_path: str, loader_path: str, modelo: str, partition: str='frp'):
        super().__init__()
        self.edl_path = edl_path
        self.loader_path = loader_path
        self.modelo = modelo
        self.partition = partition
        self._cancelado = False
    def _log(self, msg: str):
        print(msg, flush=True)
        self.log_signal.emit(msg)
    def run(self):
        try:
            if not os.path.exists(self.edl_path):
                self._log('ÔØî ERRO: edl.exe n├úo encontrado!')
                self._log(f'   Caminho: {self.edl_path}')
                self.finished_signal.emit(False, 'edl.exe n├úo encontrado')
                self.status_signal.emit('error')
                return
            if not os.path.exists(self.loader_path):
                self._log('ÔØî ERRO: Loader n├úo encontrado!')
                self._log(f'   Caminho: {self.loader_path}')
                self.finished_signal.emit(False, 'Loader n├úo encontrado')
                self.status_signal.emit('error')
                return
            self._log('=======================================================')
            self._log('  TECH UNION SOLUTIONS - FRP XIAOMI EDL')
            self._log(f'  Modelo: {self.modelo}')
            self._log('  M├®todo: Qualcomm EDL + Firehose Loader')
            self._log('=======================================================')
            self._log('')
            self._log('Ô£à edl.exe ......: Encontrado')
            self._log(f'Ô£à Loader .......: {os.path.basename(self.loader_path)}')
            self._log(f'Ô£à Parti├º├úo .....: {self.partition}')
            self._log('')
            self._log('­ƒô▒ Aguardando dispositivo em modo EDL...')
            self._log('   Conecte o celular em modo EDL:')
            self._log('   1. Desligue o aparelho completamente')
            self._log('   2. Segure Volume - (menos)')
            self._log('   3. Conecte o cabo USB mantendo pressionado')
            self._log('   4. Solte ap├│s 5 segundos')
            self._log('')
            self._log('-------------------------------------------------------')
            self.status_signal.emit('waiting')
            self.progress_signal.emit(10)
            comando_edl = [self.edl_path, 'e', self.partition, '--loader', self.loader_path, '--memory=emmc']
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            processo = subprocess.Popen(comando_edl, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=False, cwd=os.path.dirname(self.edl_path), creationflags=creationflags)
            device_connected = False
            erasing_started = False
            erase_completed = False
            if self._cancelado:
                processo.terminate()
                self._log('')
                self._log('Ôøö Processo cancelado pelo usu├írio')
                self.finished_signal.emit(False, 'Cancelado')
                self.status_signal.emit('error')
                return
            linha_bytes = processo.stdout.readline()
            if not linha_bytes and processo.poll() is not None:
                pass
            elif linha_bytes:
                pass
            try:
                linha = linha_bytes.decode('utf-8', errors='replace').rstrip()
            except:
                linha = linha_bytes.decode('latin-1', errors='replace').rstrip()
            else:
                linha_limpa = linha
                self._log(linha_limpa)
                linha_lower = linha_limpa.lower()
                if not device_connected:
                    frases_conexao = ['device detected :)', 'uploading loader', 'loader successfully', 'firehose mode detected']
                    if any((frase in linha_lower for frase in frases_conexao)):
                        device_connected = True
                        self.status_signal.emit('connected')
                        self.progress_signal.emit(50)
                        self._log('')
                        self._log('Ô£à Dispositivo detectado e conectado!')
                        self._log('')
                if 'erasing' in linha_lower:
                    erasing_started = True
                    self.progress_signal.emit(70)
                if 'erased' in linha_lower or 'reset frp' in linha_lower:
                    erase_completed = True
                    self.progress_signal.emit(90)
                retcode = processo.wait()
                if retcode == 0 or erase_completed:
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
                self.status_signal.emit('error')
                self._log('')
                self._log(f'ÔØî Falha na formata├º├úo (c├│digo: {retcode})')
                self.finished_signal.emit(False, 'Erro na formata├º├úo EDL')
        except Exception as e:
            self.status_signal.emit('error')
            self._log(f'ÔØî Exce├º├úo: {str(e)}')
            self.finished_signal.emit(False, str(e))
    def cancelar(self):
        self._cancelado = True
        if sys.platform == 'win32':
            try:
                subprocess.run(['taskkill', '/F', '/IM', 'edl.exe'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                return
            except:
                pass
