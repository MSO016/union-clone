import os
import sys
import subprocess
import time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QFrame, QMessageBox, QGridLayout, QTextEdit)
from PyQt5.QtCore import (Qt, QThread, pyqtSignal)
from PyQt5.QtGui import QFont
from ..galaxy_a04_all_mods.brom_a04_all import CoresUnion
def log(msg: str):
    print(f'[ANDROID16] {msg}', flush=True)
def _resolve_samsung_subdir(script_dir: str, *subpath) -> str:
    try:
        from app.utils.path_manager import PathManager
        tools = PathManager.get_unlock_tools_dir()
        if tools and os.path.isdir(tools):
            samsung = os.path.normpath(os.path.join(os.path.dirname(tools), 'samsung', *subpath))
            if os.path.exists(samsung):
                return samsung
    except Exception:
        pass
    return os.path.normpath(os.path.join(script_dir, '..', *subpath))
def _resolve_adb(script_dir: str) -> str:
    data_dir = _resolve_samsung_subdir(script_dir, 'data', 'nsec_and_16')
    local_adb = os.path.join(data_dir, 'adb.exe')
    if os.path.isfile(local_adb):
        return local_adb
    try:
        from app.utils.adb_manager import ADBManager
        mgr = ADBManager()
        found = mgr.find_adb_path()
        if found and os.path.isfile(found):
            return found
    except Exception:
        pass
    return 'adb'
class MtpWorker(QThread):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, script_dir: str, step: str):
        super().__init__()
        self.script_dir = script_dir
        self.step = step
        self._cancelado = False
        self._adb = _resolve_adb(script_dir)
    def cancelar(self):
        self._cancelado = True
    def run(self):
        try:
            if self.step == 'adb':
                self._execute_adb_enable()
                return
            if self.step == 'frp':
                self._execute_frp_remove()
                return
            if self.step == 'patch':
                self._execute_patch()
                return
        except Exception as e:
            log(f'ÔØî ERRO: {str(e)}')
            self.finished_signal.emit(False, str(e))
    def _execute_adb_enable(self):
        log('==================================================')
        log('ETAPA 1: HABILITAR ADB')
        log('==================================================')
        self.status_signal.emit('adb_starting')
        self.progress_signal.emit(10)
        at_console = os.path.join(_resolve_samsung_subdir(self.script_dir, 'data', 'nsec_and_16'), 'ATCommandConsole.exe')
        log(f'­ƒôé Ferramenta: {at_console}')
        if not os.path.exists(at_console):
            log('ÔØî ATCommandConsole.exe n├úo encontrado!')
            self.finished_signal.emit(False, 'Ferramenta n├úo encontrada!')
            return
        log('Ô£à Ferramenta encontrada')
        log('ÔÅ│ Iniciando AT Command Console...')
        self.progress_signal.emit(20)
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            process = subprocess.Popen([at_console], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
            success = False
            for line in process.stdout:
                if self._cancelado:
                    log('ÔÜá´©Å Processo cancelado pelo usu├írio')
                    process.terminate()
                    return
                line = line.strip()
                if not line:
                    continue
                log(f'   {line}')
                if 'No AT device detected' in line:
                    log('ÔØî Nenhuma porta COM detectada!')
                    log('   Tente novamente.')
                    log('   - Se o problema persistir, reinicie o dispositivo.')
                    process.terminate()
                    self.finished_signal.emit(False, 'Nenhuma porta COM detectada.\nTente novamente.\n\n- Se o problema persistir, reinicie o dispositivo.')
                    return
                if 'Connected to COM' in line:
                    log('Ô£à Porta COM conectada!')
                    self.progress_signal.emit(50)
                    self.status_signal.emit('connected')
                    continue
                if '[SUCCESS] ADB Device Connected' in line:
                    log('Ô£à ADB conectado com sucesso!')
                    self.progress_signal.emit(100)
                    success = True
                    continue
                if 'Script execution finished' in line or 'Press Enter to exit' in line:
                    log('Ô£à Processo do ATCommandConsole finalizado')
                    process.terminate()
                    break
                if 'Done' not in line:
                    continue
                success = True
                continue
            if process.poll() is None:
                process.terminate()
            if success:
                log('Ô£à ETAPA 1 CONCLU├ìDA!')
                log('--------------------------------------------------')
                self.finished_signal.emit(True, "ADB habilitado!\nAgora execute 'Remover FRP'.")
                return
            log('ÔÜá´©Å Processo finalizado - verifique o dispositivo')
            self.finished_signal.emit(False, 'Verifique o dispositivo e tente novamente.')
            return
        except Exception as e:
            log(f'ÔØî Erro: {str(e)}')
            self.finished_signal.emit(False, str(e))
    def _adb_cmd(self, args, **kwargs):
        if isinstance(args, str):
            full = f'"{self._adb}" {args}'
            return subprocess.run(full, shell=True, **kwargs)
        return subprocess.run([self._adb] + list(args), **kwargs)
    def _adb_popen(self, args, **kwargs):
        if isinstance(args, str):
            full = f'"{self._adb}" {args}'
            return subprocess.Popen(full, shell=True, **kwargs)
        return subprocess.Popen([self._adb] + list(args), **kwargs)
    def _execute_frp_remove(self):
        log('==================================================')
        log('ETAPA 2: REMOVER FRP')
        log('==================================================')
        self.status_signal.emit('frp_starting')
        self.progress_signal.emit(10)
        data_dir = _resolve_samsung_subdir(self.script_dir, 'data', 'nsec_and_16')
        log(f'Diretorio: {data_dir}')
        log(f'ADB: {self._adb}')
        log('Limpando processos anteriores...')
        self._adb_cmd("shell pkill -f 'nc -lp 8080'", capture_output=True)
        self._adb_cmd("shell pkill -f 'nc -lp 1234'", capture_output=True)
        push_files = [('base.apk', '/data/log/', 'Enviando base.apk...'), ('classes.dex', '/data/log/', 'Enviando classes.dex...')]
        progress = 20
        for fname, dest, msg in push_files:
            if self._cancelado:
                return
            self._adb_cmd("shell pkill -f 'nc -lp 8080'", capture_output=True)
            self._adb_cmd("shell pkill -f 'nc -lp 1234'", capture_output=True)
            log(msg)
            self.progress_signal.emit(progress)
            result = self._adb_cmd(f'push {fname} {dest}', capture_output=True, text=True, cwd=data_dir)
            if result.stdout:
                log(f'   {result.stdout.strip()}')
            if 'error: no devices' in (result.stderr or '').lower():
                log('Dispositivo nao conectado!')
                self.finished_signal.emit(False, 'Dispositivo nao conectado via ADB!')
                return
            if 'file pushed' in (result.stdout or '').lower():
                log('   Arquivo enviado!')
            progress += 20
            continue
        if self._cancelado:
            return
        self._adb_cmd("shell pkill -f 'nc -lp 8080'", capture_output=True)
        self._adb_cmd("shell pkill -f 'nc -lp 1234'", capture_output=True)
        log('Executando comandos...')
        log('   Aguardando resposta (max 20s)...')
        self.progress_signal.emit(70)
        nc_cmd = 'shell "echo \'app_process -Djava.class.path=/data/log/classes.dex /system/bin --nice-name=Exploit Exploit && sleep 2 && am restart\' | nc -lp 1234"'
        try:
            process = self._adb_popen(nc_cmd, cwd=data_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except Exception as e:
            log(f'   Erro: {str(e)}')
        else:
            try:
                try:
                    out, err = process.communicate(timeout=20)
                    output = (out or '') + (err or '')
                    if out:
                        log(f'   {out.strip()}')
                    if 'not found' in output.lower() or 'no service started' in output.lower():
                        log('Servico nao encontrado!')
                        self.finished_signal.emit(False, "Servico nao encontrado.\nExecute 'Habilitar ADB' novamente.")
                        return
                except subprocess.TimeoutExpired:
                    process.terminate()
                    log('   Timeout - continuando...')
            except Exception as e:
                log(f'   Erro: {str(e)}')
        self.progress_signal.emit(100)
        log('ETAPA 2 CONCLUIDA!')
        log('--------------------------------------------------')
        self.finished_signal.emit(True, "FRP removido!\nAgora clique em 'Concluir' para finalizar.")
    def _dd_via_service(self, partition: str, timeout: int=25) -> str:
        self._adb_cmd("shell pkill -f 'nc -lp 8080'", capture_output=True)
        time.sleep(0.5)
        nc_cmd = f'shell "am startservice com.shell/.Server > /dev/null & sleep 3 & echo \'dd if=/dev/zero of=/dev/block/by-name/{partition}\' | /system/bin/nc -lp 8080"'
        try:
            proc = self._adb_popen(nc_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except Exception as e:
            return str(e)
        try:
            try:
                out, err = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.terminate()
                return ''
            return (out or '') + (err or '')
        except Exception as e:
            return str(e)
    def _dd_direto(self, partition: str) -> str:
        result = self._adb_cmd(f'shell "dd if=/dev/zero of=/dev/block/by-name/{partition} 2>&1"', capture_output=True, text=True)
        return (result.stdout or '') + (result.stderr or '')
    def _limpar_particao(self, partition: str) -> bool:
        log(f'Limpando {partition}...')
        output = self._dd_via_service(partition)
        out_l = output.lower()
        if 'records' in out_l or 'copied' in out_l or 'no space left' in out_l:
            log(f'   {partition} limpa com sucesso!')
            return True
        if "can't find service" in out_l or 'not found' in out_l or 'no service started' in out_l or not output.strip():
            log('   Servico indisponivel, tentando acesso direto...')
            output = self._dd_direto(partition)
            out_l = output.lower()
            if 'records' in out_l or 'copied' in out_l or 'no space left' in out_l:
                log(f'   {partition} limpa com sucesso (direto)!')
                return True
        if output.strip():
            log(f'   {output.strip()[:120]}')
        return False
    def _execute_patch(self):
        log('==================================================')
        log('ETAPA 3: CONCLUIR PROCESSO')
        log('==================================================')
        self.status_signal.emit('patch_starting')
        self.progress_signal.emit(10)
        log(f'ADB: {self._adb}')
        log('Iniciando servidor ADB...')
        self._adb_cmd('start-server', capture_output=True)
        log('Aguardando dispositivo reconectar...')
        self.progress_signal.emit(15)
        adb_found = False
        for tentativa in range(1, 13):
            if self._cancelado:
                self.finished_signal.emit(False, 'Cancelado')
                return
            devices = self._adb_cmd('devices', capture_output=True, text=True)
            output = devices.stdout.strip()
            if 'device' in output.lower() and output.count('device') >= 2:
                log(f'Dispositivo reconectado! (tentativa {tentativa})')
                adb_found = True
                break
            log(f'   Tentativa {tentativa}/12 ÔÇö aguardando 5s...')
            pct = 15 + int(tentativa * 2)
            self.progress_signal.emit(min(pct, 40))
            time.sleep(5)
        if not adb_found:
            log('Dispositivo nao reconectou via ADB')
            log('Verifique a conexao USB e tente novamente')
            self.finished_signal.emit(False, 'Dispositivo nao reconectou via ADB.\n\nVerifique a conexao USB e tente novamente.')
            return
        self.progress_signal.emit(40)
        try:
            frp_ok = self._limpar_particao('frp')
            self.progress_signal.emit(60)
            persistent_ok = self._limpar_particao('persistent')
            self.progress_signal.emit(80)
            if frp_ok or persistent_ok:
                log('Protecao removida!')
                log('Reiniciando dispositivo...')
                time.sleep(2)
                self._adb_cmd('reboot', capture_output=True)
                self.progress_signal.emit(100)
                log('==================================================')
                log('PROCESSO FINALIZADO COM SUCESSO!')
                log('==================================================')
                self.finished_signal.emit(True, 'FRP removido com sucesso!\nDispositivo reiniciando...\n\nConfigure normalmente apos reiniciar.')
                return
            log('Nenhuma particao confirmada ÔÇö reiniciando mesmo assim')
            time.sleep(2)
            self._adb_cmd('reboot', capture_output=True)
            self.progress_signal.emit(100)
            log('==================================================')
            log('PROCESSO FINALIZADO!')
            log('==================================================')
            self.finished_signal.emit(True, 'Processo finalizado!\nDispositivo reiniciando...\n\nVerifique se o FRP foi removido.')
            return
        except Exception as e:
            log(f'Erro: {str(e)}')
            self.finished_signal.emit(False, str(e))
class MtpAllAndroid16Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.em_execucao = False
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.setup_ui()
    def setup_ui(self):
        self.setStyleSheet(f'background-color: {CoresUnion.BACKGROUND};')
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 25, 30, 25)
        main_layout.setSpacing(20)
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)
        title = QLabel('Samsung Galaxy | Android 16')
        title.setFont(QFont('Segoe UI', 22, QFont.Bold))
        title.setStyleSheet(f'color: {CoresUnion.TEXT};')
        header_layout.addWidget(title)
        subtitle = QLabel('Todos os modelos')
        subtitle.setFont(QFont('Segoe UI', 12))
        subtitle.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        header_layout.addWidget(subtitle)
        main_layout.addWidget(header_widget)
        stepper_container = QWidget()
        stepper_layout = QHBoxLayout(stepper_container)
        stepper_layout.setContentsMargins(0, 15, 0, 15)
        stepper_layout.setSpacing(15)
        step1_widget = self._create_step_indicator('1', 'Habilitar ADB', True)
        stepper_layout.addWidget(step1_widget)
        connector1 = QLabel('ÔåÆ')
        connector1.setFont(QFont('Segoe UI', 18))
        connector1.setStyleSheet(f'color: {CoresUnion.BORDER};')
        stepper_layout.addWidget(connector1)
        step2_widget = self._create_step_indicator('2', 'Eliminar FRP', False)
        stepper_layout.addWidget(step2_widget)
        connector2 = QLabel('ÔåÆ')
        connector2.setFont(QFont('Segoe UI', 18))
        connector2.setStyleSheet(f'color: {CoresUnion.BORDER};')
        stepper_layout.addWidget(connector2)
        step3_widget = self._create_step_indicator('3', 'Concluir', False)
        stepper_layout.addWidget(step3_widget)
        stepper_layout.addStretch()
        main_layout.addWidget(stepper_container)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        actions_panel = QWidget()
        actions_layout = QVBoxLayout(actions_panel)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(15)
        self.btn_adb = QPushButton('ÔûÂ  Habilitar ADB')
        self.btn_adb.setFixedHeight(50)
        self.btn_adb.setCursor(Qt.PointingHandCursor)
        self.btn_adb.setFont(QFont('Segoe UI', 12, QFont.Bold))
        self.btn_adb.setStyleSheet(f'\n            QPushButton {{\n                background-color: {CoresUnion.PRIMARY};\n                color: white;\n                border: none;\n                border-radius: 10px;\n                padding: 0 20px;\n                text-align: left;\n            }}\n            QPushButton:hover {{ background-color: {CoresUnion.PRIMARY_HOVER}; }}\n            QPushButton:disabled {{ background-color: {CoresUnion.BORDER}; color: #999; }}\n        ')
        self.btn_adb.clicked.connect((lambda: self.execute_step('adb')))
        actions_layout.addWidget(self.btn_adb)
        self.btn_frp = QPushButton('ÔûÂ  Eliminar FRP')
        self.btn_frp.setFixedHeight(50)
        self.btn_frp.setCursor(Qt.PointingHandCursor)
        self.btn_frp.setFont(QFont('Segoe UI', 12, QFont.Bold))
        self.btn_frp.setStyleSheet(f'\n            QPushButton {{\n                background-color: #00897B;\n                color: white;\n                border: none;\n                border-radius: 10px;\n                padding: 0 20px;\n                text-align: left;\n            }}\n            QPushButton:hover {{ background-color: #00796B; }}\n            QPushButton:disabled {{ background-color: {CoresUnion.BORDER}; color: #999; }}\n        ')
        self.btn_frp.clicked.connect((lambda: self.execute_step('frp')))
        actions_layout.addWidget(self.btn_frp)
        self.btn_patch = QPushButton('ÔûÂ  Concluir Processo')
        self.btn_patch.setFixedHeight(50)
        self.btn_patch.setCursor(Qt.PointingHandCursor)
        self.btn_patch.setFont(QFont('Segoe UI', 12, QFont.Bold))
        self.btn_patch.setStyleSheet(f'\n            QPushButton {{\n                background-color: #FF6D00;\n                color: white;\n                border: none;\n                border-radius: 10px;\n                padding: 0 20px;\n                text-align: left;\n            }}\n            QPushButton:hover {{ background-color: #E65100; }}\n            QPushButton:disabled {{ background-color: {CoresUnion.BORDER}; color: #999; }}\n        ')
        self.btn_patch.clicked.connect((lambda: self.execute_step('patch')))
        actions_layout.addWidget(self.btn_patch)
        actions_layout.addStretch()
        content_layout.addWidget(actions_panel, stretch=1)
        log_panel = QWidget()
        log_layout = QVBoxLayout(log_panel)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(10)
        log_title = QLabel(' Log de Execu├º├úo')
        log_title.setFont(QFont('Segoe UI', 13, QFont.Bold))
        log_title.setStyleSheet(f'color: {CoresUnion.TEXT};')
        log_layout.addWidget(log_title)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont('Segoe UI', 10))
        self.log_text.setStyleSheet(f'\n            QTextEdit {{\n                background-color: {CoresUnion.BACKGROUND_WHITE};\n                color: {CoresUnion.TEXT};\n                border: 2px solid {CoresUnion.BORDER};\n                border-radius: 10px;\n                padding: 15px;\n                line-height: 1.5;\n            }}\n        ')
        info_inicial = "­ƒô▒ <b>Samsung Galaxy Android 16 - Unlock FRP</b><br><br>ÔÜá´©Å <b style='color: #FF6D00;'>IMPORTANTE:</b> Este m├®todo funciona para patches de seguran├ºa<br>de <b>Outubro a Dezembro de 2025</b><br><br>­ƒôï <b>Requisitos:</b><br>ÔÇó Dispositivo ligado e conectado via USB<br>ÔÇó Drivers ADB instalados<br>ÔÇó .NET Framework 8.0 ou superior<br><br>­ƒöä <b>Processo:</b><br>1. Habilitar ADB no dispositivo<br>2. Remover bloqueio FRP<br>3. Aplicar patch e reiniciar<br><br><span style='color: #00897B;'>Ô£ô Pronto para iniciar</span><br><hr style='border: 1px solid #E0E0E0;'>"
        self.log_text.setHtml(info_inicial)
        log_layout.addWidget(self.log_text)
        content_layout.addWidget(log_panel, stretch=2)
        main_layout.addLayout(content_layout)
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(8)
        self.label_status = QLabel(' Pronto para iniciar')
        self.label_status.setFont(QFont('Segoe UI', 11, QFont.Bold))
        self.label_status.setStyleSheet(f'color: {CoresUnion.TEXT};')
        footer_layout.addWidget(self.label_status)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(15)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f'\n            QProgressBar {{\n                border: 2px solid {CoresUnion.BORDER};\n                border-radius: 7px;\n                background-color: {CoresUnion.BACKGROUND_WHITE};\n            }}\n            QProgressBar::chunk {{\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n                    stop:0 {CoresUnion.PRIMARY}, stop:1 #00BFA5);\n                border-radius: 5px;\n            }}\n        ')
        footer_layout.addWidget(self.progress_bar)
        main_layout.addLayout(footer_layout)
    def _create_step_indicator(self, number, text, active=False):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignCenter)
        circle = QLabel(number)
        circle.setFixedSize(40, 40)
        circle.setAlignment(Qt.AlignCenter)
        circle.setFont(QFont('Segoe UI', 14, QFont.Bold))
        if active:
            circle.setStyleSheet(f'\n                background-color: {CoresUnion.PRIMARY};\n                color: white;\n                border-radius: 20px;\n                border: 3px solid {CoresUnion.PRIMARY};\n            ')
        else:
            circle.setStyleSheet(f'\n                background-color: {CoresUnion.BACKGROUND_WHITE};\n                color: {CoresUnion.TEXT_MUTED};\n                border-radius: 20px;\n                border: 2px solid {CoresUnion.BORDER};\n            ')
        layout.addWidget(circle, alignment=Qt.AlignCenter)
        label = QLabel(text)
        label.setFont(QFont('Segoe UI', 10))
        label.setStyleSheet(f'color: {CoresUnion.TEXT if active else CoresUnion.TEXT_MUTED};')
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        return container
    def execute_step(self, step: str):
        if self.em_execucao:
            QMessageBox.warning(self, 'Aviso', 'Um processo j├í est├í em execu├º├úo.')
            return
        self.em_execucao = True
        self.progress_bar.setValue(0)
        step_names = {'adb': 'Habilitando ADB...', 'frp': 'Removendo FRP...', 'patch': 'Concluindo...'}
        self.label_status.setText(step_names.get(step, 'Processando...'))
        self.label_status.setStyleSheet(f'color: {CoresUnion.PRIMARY};')
        self.btn_adb.setEnabled(False)
        self.btn_frp.setEnabled(False)
        self.btn_patch.setEnabled(False)
        log(f'Iniciando: {step}')
        self.worker = MtpWorker(self.script_dir, step)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.status_signal.connect(self._on_status)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()
    def _on_status(self, status: str):
        if status == 'connected':
            self.label_status.setText('Dispositivo conectado!')
            self.label_status.setStyleSheet(f'color: {CoresUnion.PRIMARY};')
    def _on_finished(self, sucesso: bool, msg: str):
        self.em_execucao = False
        self.btn_adb.setEnabled(True)
        self.btn_frp.setEnabled(True)
        self.btn_patch.setEnabled(True)
        if sucesso:
            self.label_status.setText('Ô£à Conclu├¡do!')
            self.label_status.setStyleSheet(f'color: {CoresUnion.SUCCESS};')
            QMessageBox.information(self, 'Sucesso', msg)
            return
        self.label_status.setText('ÔØî Erro')
        self.label_status.setStyleSheet(f'color: {CoresUnion.ERROR};')
        self.progress_bar.setValue(0)
        QMessageBox.critical(self, 'Erro', msg)
