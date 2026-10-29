import os
import sys
import subprocess
import socket
import re
import time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QFrame, QMessageBox)
from PyQt5.QtCore import (QThread, pyqtSignal, Qt, QTimer, QVariantAnimation)
from PyQt5.QtGui import (QFont, QPixmap, QTransform)
from ..moto_e22_mods.brom_e22 import CoresUnion
try:
    from app.utils.adb_manager import ADBManager
    HAS_ADB_MANAGER = True
except ImportError:
    HAS_ADB_MANAGER = False
KARNEL_PAYLOADS = {'init': bytes.fromhex('0001009700000000000000020001'), 'factory': bytes.fromhex('00010108000000000000000c0100090007666163746f7279'), 'secure_off': bytes.fromhex('000201080000000000000024010015001f3120616e64726f6964626f6f742e7365637572655f68617264776172653d30'), 'enable': bytes.fromhex('0002010800000000000000050100150000'), 'reboot': bytes.fromhex('000300220000000000000000')}
FACTORY_MODE_IPS = ['192.168.137.2', '192.168.42.129', '192.168.42.1', '192.168.1.1']
class FrpOldWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, modelo: str):
        super().__init__()
        self.modelo = modelo
        self._cancelado = False
        self.device_ip = None
        self.phase1_done = False
        self.adb_manager = None
        self.adb_path = None
        if HAS_ADB_MANAGER:
            try:
                self.adb_manager = ADBManager()
                self.adb_path = self.adb_manager.adb_path
                if self.adb_path:
                    print(f'[FRP_OLD] ADBManager OK - ADB: {self.adb_path}')
                    return
                print('[FRP_OLD] ADBManager inicializado mas adb_path nao encontrado')
                self.adb_path = self.adb_manager.find_adb_path()
                if self.adb_path:
                    print(f'[FRP_OLD] ADB encontrado via find_adb_path: {self.adb_path}')
                    return
            except Exception as e:
                print(f'[FRP_OLD] Erro ao inicializar ADBManager: {e}')
                self.adb_manager = None
            return
        print('[FRP_OLD] ADBManager nao disponivel (import falhou)')
    def cancelar(self):
        self._cancelado = True
    def _log(self, msg: str):
        print(msg, flush=True)
        self.log_signal.emit(msg)
    def _run_adb(self, *args, timeout: int=30) -> tuple:
        if self.adb_manager:
            try:
                cmd_str = ' '.join(args)
                output = self.adb_manager.execute_adb_command(cmd_str, timeout=timeout)
                if output:
                    return output, 0
            except Exception as e:
                error_msg = str(e)
                self._log(f'   [ADB] Erro: {error_msg[:50]}...')
                return error_msg, -1
            return '', 0
        if not self.adb_path:
            return ('ADB nao disponivel', -1)
        cmd = [self.adb_path] + list(args)
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            adb_dir = os.path.dirname(self.adb_path)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=adb_dir, creationflags=creationflags)
        except subprocess.TimeoutExpired:
            return ('Timeout', -1)
        except Exception as e:
            return str(e), -1
        return result.stdout + result.stderr, result.returncode
    def _test_tcp_port(self, ip: str, port: int=11000, timeout: float=2) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    def _test_adb_port(self, ip: str, port: int=5555) -> bool:
        return self._test_tcp_port(ip, port, timeout=1)
    def _send_tcp_payload(self, ip: str, port: int, payload: bytes, name: str='') -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((ip, port))
            sock.sendall(payload)
            try:
                sock.settimeout(1)
                response = sock.recv(1024)
                if response and name:
                    self._log(f'   Resposta: {response.hex()[:30]}...')
            except:
                pass
            else:
                sock.close()
        except Exception as e:
            self._log(f'   Erro ao enviar {name}: {e}')
            return False
        return True
    def _find_factory_mode_device(self) -> str:
        possible_ips = FACTORY_MODE_IPS.copy()
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=5, creationflags=creationflags)
            for line in result.stdout.split('\n'):
                match = re.search('(192\\.168\\.137\\.\\d+)', line)
                if match:
                    ip = match.group(1)
                    if ip == '192.168.137.1':
                        continue
                    if ip not in possible_ips:
                        possible_ips.insert(0, ip)
        except:
            pass
        for ip in possible_ips:
            if not self._test_tcp_port(ip, 11000):
                continue
            return ip
    def _check_adb_device(self, output: str) -> tuple:
        if not output:
            return (False, None)
        for line in output.strip().split('\n'):
            line = line.strip()
            if not line or 'List of devices' in line:
                continue
            if 'daemon' in line.lower() or 'starting' in line.lower():
                continue
            if '\tdevice' in line:
                return (True, 'device')
            if '\tunauthorized' in line:
                return (True, 'unauthorized')
        return (False, None)
    def _wait_adb_authorization(self, timeout: int=60) -> bool:
        self._log('')
        self._log('­ƒô▒ ADB detectado! Aceite a autorizacao na tela do dispositivo...')
        self.status_signal.emit('adb_unauthorized')
        for i in range(timeout):
            if self._cancelado:
                return False
            output, code = self._run_adb('devices')
            if code == 0:
                connected, status = self._check_adb_device(output)
                if connected and status == 'device':
                    self._log('Ô£à ADB autorizado!')
                    return True
                if not connected:
                    self._log('ÔÜá´©Å Dispositivo desconectou')
                    return False
            self._log(f'   Aguardando autorizacao... ({i + 1}/{timeout})')
            self.msleep(1000)
        self._log('ÔÜá´©Å Timeout aguardando autorizacao ADB')
        return False
    def _execute_injection_karnel(self, ip: str) -> bool:
        port = 11000
        self._log('')
        self._log('==================================================')
        self._log('­ƒÆë INJECTION KARNEL')
        self._log('==================================================')
        self._log(f'Alvo: {ip}:{port} (TCP)')
        self.status_signal.emit('injecting')
        self.progress_signal.emit(20)
        if not self.phase1_done:
            self._log('')
            self._log('­ƒôñ FASE 1: Configuracao inicial...')
            for name in ('init', 'factory', 'secure_off', 'reboot'):
                if self._cancelado:
                    return False
                payload = KARNEL_PAYLOADS.get(name)
                if payload:
                    self._log(f'   Enviando {name.upper()}...')
                    success = self._send_tcp_payload(ip, port, payload, name.upper())
                    if success:
                        self._log(f'   Ô£ô {name.upper()} enviado')
                    self.msleep(500)
            self.phase1_done = True
            self.progress_signal.emit(30)
            self._log('')
            self._log('ÔÅ│ Aguardando reboot (5 segundos)...')
            self.msleep(5000)
        self._log('')
        self._log('­ƒôñ FASE 2: Ativando ADB...')
        self._log('   (Loop INIT/ENABLE ate ADB responder)')
        packets_sent = 0
        enable_sent = False
        max_attempts = 120
        for attempt in range(max_attempts):
            if self._cancelado:
                return False
            if packets_sent > 0 and packets_sent % 7 == 0:
                self._log('')
                self._log(f'­ƒöì Verificando ADB ({packets_sent} pacotes enviados)...')
                if self._test_adb_port(ip, 5555):
                    self._log('­ƒÄë Porta ADB 5555 aberta!')
                    return True
                output, code = self._run_adb('devices')
                if code == 0:
                    connected, status = self._check_adb_device(output)
                    if connected:
                        if status == 'unauthorized':
                            if self._wait_adb_authorization():
                                return True
                        else:
                            self._log('­ƒÄë ADB detectado (USB)!')
                            return True
                self._log('   ADB ainda nao disponivel...')
            if not self._test_tcp_port(ip, port, timeout=1):
                self._log(f'   Porta 11000 fechada (tentativa {attempt + 1})')
                if self._test_adb_port(ip, 5555):
                    self._log('­ƒÄë ADB ativou (TCP)!')
                    return True
                output, code = self._run_adb('devices')
                if code == 0:
                    connected, status = self._check_adb_device(output)
                    if connected:
                        if status == 'unauthorized':
                            if self._wait_adb_authorization():
                                return True
                        else:
                            self._log('­ƒÄë ADB ativou (USB)!')
                            return True
                self.msleep(1000)
                continue
            success = self._send_tcp_payload(ip, port, KARNEL_PAYLOADS['init'], f'INIT #{packets_sent + 1}')
            if not success:
                self.msleep(1000)
                if self._test_adb_port(ip, 5555):
                    self._log('­ƒÄë ADB ativou apos erro!')
                    return True
                output, code = self._run_adb('devices')
                if code == 0:
                    connected, status = self._check_adb_device(output)
                    if connected:
                        if status == 'unauthorized':
                            if self._wait_adb_authorization():
                                return True
                        else:
                            self._log('­ƒÄë ADB detectado!')
                            return True
            packets_sent += 1
            progress = 30 + min(30, packets_sent)
            self.progress_signal.emit(progress)
            if packets_sent >= 3:
                self.msleep(300)
                success = self._send_tcp_payload(ip, port, KARNEL_PAYLOADS['enable'], 'ENABLE')
                if success:
                    if not enable_sent:
                        self._log('   Ô£ô Primeiro ENABLE enviado!')
                        enable_sent = True
                    packets_sent += 1
                elif self._test_adb_port(ip, 5555):
                    self._log('­ƒÄë ADB ativou apos ENABLE!')
                    return True
            self.msleep(500)
            continue
        self._log('')
        self._log('ÔÜá´©Å Timeout - ADB nao ativou apos 2 minutos')
        return False
    def _execute_frp_bypass(self) -> bool:
        self._log('')
        self._log('==================================================')
        self._log('­ƒöô BYPASS FRP')
        self._log('==================================================')
        self.status_signal.emit('bypassing')
        self.progress_signal.emit(70)
        self._log('')
        self._log('­ƒô▒ Coletando informacoes do dispositivo...')
        props = [('model', 'ro.product.model'), ('android', 'ro.build.version.release')]
        for key, prop in props:
            output, code = self._run_adb('shell', f'getprop {prop}')
            if code == 0:
                self._log(f'   {key}: {output.strip()}')
        self.progress_signal.emit(75)
        self.msleep(1000)
        self._log('')
        self._log('­ƒôñ Executando bypass via content provider...')
        cmd1 = 'content insert --uri content://settings/secure --bind name:s:user_setup_complete --bind value:s:1'
        self._log(f'   $ adb shell {cmd1[:50]}...')
        output, code = self._run_adb('shell', cmd1)
        if code == 0:
            self._log('   Ô£ô Comando executado!')
        else:
            self._log(f'   ÔÜá´©Å Resposta: {output.strip()[:50]}')
        self.progress_signal.emit(80)
        self.msleep(1000)
        self._log('')
        self._log('­ƒôñ Configurando setup wizard...')
        cmd2 = 'settings put secure user_setup_complete 1'
        output, code = self._run_adb('shell', cmd2)
        if code == 0:
            self._log('   Ô£ô Setup wizard configurado!')
        self.progress_signal.emit(90)
        self.msleep(1000)
        self._log('')
        self._log('­ƒöä Reiniciando dispositivo...')
        output, code = self._run_adb('shell', 'reboot')
        self.progress_signal.emit(100)
        return True
    def run(self):
        try:
            self._log('')
            self._log('=======================================================')
            self._log('  TECH UNION SOLUTIONS - FRP OLD (Factory Mode)')
            self._log(f'  Modelo: {self.modelo}')
            self._log('=======================================================')
            if not self.adb_path:
                self._log('')
                self._log('ÔØî ERRO: ADB nao disponivel!')
                self._log('   Verifique se o ADB esta instalado no sistema.')
                self.finished_signal.emit(False, 'ADB nao disponivel!\n\nVerifique se o ADB esta instalado\nou se o Windows nao esta bloqueando.')
                self.status_signal.emit('error')
                return
            self._log(f'   ADB: {self.adb_path}')
            self._log('')
            self._log('­ƒöì Procurando dispositivo em Factory Mode...')
            self._log('   (Porta TCP 11000)')
            self.status_signal.emit('waiting')
            self.progress_signal.emit(5)
            factory_ip = None
            for i in range(30):
                if self._cancelado:
                    self.finished_signal.emit(False, 'Cancelado')
                    return
                factory_ip = self._find_factory_mode_device()
                if factory_ip:
                    break
                self._log(f'   Aguardando... ({i + 1}/30)')
                self.msleep(1000)
            if not factory_ip:
                self._log('')
                self._log('ÔØî Factory Mode nao detectado!')
                self._log('')
                self._log('­ƒôï Instrucoes:')
                self._log('   1. Desligue o aparelho')
                self._log('   2. Segure Volume - e Power')
                self._log("   3. Selecione 'Factory Mode' ou 'BP Tools'")
                self._log('   4. Conecte o cabo USB')
                self.finished_signal.emit(False, "Factory Mode nao detectado!\n\nInstrucoes:\n1. Desligue o aparelho\n2. Segure Vol- + Power\n3. Selecione 'Factory Mode' ou 'BP Tools'\n4. Conecte o cabo USB")
                self.status_signal.emit('error')
                return
            self.device_ip = factory_ip
            self._log('')
            self._log(f'­ƒÅ¡ Factory Mode detectado: {factory_ip}')
            self.status_signal.emit('factory_detected')
            self.progress_signal.emit(15)
            adb_ok = self._execute_injection_karnel(factory_ip)
            if not adb_ok:
                if self._cancelado:
                    self.finished_signal.emit(False, 'Cancelado')
                    return
                self._log('')
                self._log('ÔØî Falha ao ativar ADB')
                self._log('   Tente novamente ou use outro metodo')
                self.finished_signal.emit(False, 'ADB nao ativou!\n\nTente novamente ou verifique:\n- Dispositivo compativel\n- Factory Mode ativo\n- Cabo USB funcionando')
                self.status_signal.emit('error')
                return
            self._log('')
            self._log('Ô£à ADB ativado com sucesso!')
            self.status_signal.emit('adb_detected')
            self.progress_signal.emit(65)
            if self.device_ip:
                target = f'{self.device_ip}:5555'
                self._log(f'   Conectando ADB em {target}...')
                self._run_adb('disconnect')
                self.msleep(500)
                output, code = self._run_adb('connect', target)
                if 'connected' in output.lower():
                    self._log('   Ô£ô Conectado via TCP/IP')
            bypass_ok = self._execute_frp_bypass()
            if bypass_ok:
                self._log('')
                self._log('=======================================================')
                self._log('  FRP BYPASS CONCLUIDO COM SUCESSO!')
                self._log('=======================================================')
                self._log('')
                self._log('O dispositivo esta reiniciando...')
                self._log('')
                self._log('PROXIMO PASSO:')
                self._log('  1. Apos reiniciar, va em Configuracoes')
                self._log('  2. Restaure de fabrica novamente')
                self._log('  3. Configure o aparelho normalmente')
                self._log('')
                self._log('=======================================================')
                self._log('  TECH UNION SOLUTIONS - Valeu, tecnico!')
                self._log('=======================================================')
                self.status_signal.emit('success')
                self.finished_signal.emit(True, 'FRP removido com sucesso!\n\nO dispositivo esta reiniciando.\n\nPROXIMO PASSO:\n1. Apos reiniciar, va em Configuracoes\n2. Restaure de fabrica novamente\n3. Configure o aparelho normalmente')
                return
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Falha no bypass FRP')
            return
        except Exception as e:
            self._log('')
            self._log(f'ÔØî ERRO: {str(e)}')
            import traceback
            traceback.print_exc()
            self.status_signal.emit('error')
            self.finished_signal.emit(False, str(e))
class FrpOldWidget(QWidget):
    MODELO = 'FRP OLD'
    VARIANTE = 'G5 / G6 / G7 (Factory Mode)'
    ANDROID = 'Android 7 - 10'
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.em_execucao = False
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.setup_ui()
        self._init_animation()
    def _get_img_path(self, filename: str) -> str:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base, 'img', filename)
    def _get_tools_path(self) -> str:
        try:
            from app.utils.path_manager import PathManager
            d = PathManager.get_unlock_tools_dir()
            if d and os.path.isdir(d):
                return d
        except Exception:
            pass
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base, 'tools')
    def setup_ui(self):
        self.setStyleSheet(f'background-color: {CoresUnion.BACKGROUND};')
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(50)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.setAlignment(Qt.AlignTop)
        self.label_teste = QLabel('ATIVO')
        self.label_teste.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self.label_teste.setStyleSheet(f'\n            background-color: {CoresUnion.SUCCESS};\n            color: white;\n            padding: 4px 12px;\n            border-radius: 10px;\n        ')
        self.label_teste.setFixedWidth(90)
        self.label_teste.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.label_teste)
        left_layout.addSpacing(10)
        self.label_modelo = QLabel(f'Motorola {self.MODELO}')
        self.label_modelo.setFont(QFont('Segoe UI', 24, QFont.Bold))
        self.label_modelo.setStyleSheet(f'color: {CoresUnion.TEXT};')
        left_layout.addWidget(self.label_modelo)
        self.label_variante = QLabel(self.VARIANTE)
        self.label_variante.setFont(QFont('Segoe UI', 14))
        self.label_variante.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        left_layout.addWidget(self.label_variante)
        left_layout.addSpacing(20)
        self.label_version = QLabel(f'Suporte: {self.ANDROID}')
        self.label_version.setFont(QFont('Segoe UI', 13))
        self.label_version.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        left_layout.addWidget(self.label_version)
        left_layout.addSpacing(20)
        self.btn_frp = QPushButton('Remover FRP')
        self.btn_frp.setFixedSize(160, 40)
        self.btn_frp.setCursor(Qt.PointingHandCursor)
        self.btn_frp.setFont(QFont('Segoe UI', 12, QFont.Bold))
        self.btn_frp.setStyleSheet(f'\n            QPushButton {{ background-color: {CoresUnion.PRIMARY}; color: {CoresUnion.TEXT_WHITE}; border: none; border-radius: 20px; }}\n            QPushButton:hover {{ background-color: {CoresUnion.PRIMARY_HOVER}; }}\n            QPushButton:disabled {{ background-color: {CoresUnion.BORDER}; }}\n        ')
        self.btn_frp.clicked.connect(self.executar_frp)
        left_layout.addWidget(self.btn_frp)
        left_layout.addSpacing(10)
        self.btn_parar = QPushButton('Parar')
        self.btn_parar.setFixedSize(100, 35)
        self.btn_parar.setCursor(Qt.PointingHandCursor)
        self.btn_parar.setFont(QFont('Segoe UI', 11))
        self.btn_parar.setStyleSheet(f'\n            QPushButton {{ background-color: {CoresUnion.BACKGROUND_DARK}; color: {CoresUnion.TEXT}; border: 1px solid {CoresUnion.BORDER}; border-radius: 17px; }}\n            QPushButton:hover {{ background-color: {CoresUnion.BORDER}; }}\n        ')
        self.btn_parar.clicked.connect(self.parar)
        left_layout.addWidget(self.btn_parar)
        self.barra_progresso = QProgressBar()
        self.barra_progresso.setFixedSize(250, 18)
        self.barra_progresso.setValue(0)
        self.barra_progresso.setTextVisible(False)
        self.barra_progresso.setStyleSheet(f'\n            QProgressBar {{ border: 1px solid {CoresUnion.BORDER}; border-radius: 9px; background-color: {CoresUnion.BACKGROUND_WHITE}; }}\n            QProgressBar::chunk {{ background-color: {CoresUnion.PRIMARY}; border-radius: 8px; }}\n        ')
        left_layout.addWidget(self.barra_progresso)
        left_layout.addStretch()
        self.label_instrucoes = QLabel("Instrucoes:\n1. Instale o driver USB Motorola\n2. Desligue o aparelho\n3. Segure Vol- + Power\n4. Selecione 'Factory Mode' ou 'BP Tools'\n5. Conecte o cabo USB\n6. Clique em 'Remover FRP'\n\nIMPORTANTE: Funciona APENAS em aparelhos\nque habilitam Factory Mode. Alguns modelos\nmesmo listados podem nao ser compativeis.\nRequer driver USB Motorola instalado.")
        self.label_instrucoes.setFont(QFont('Segoe UI', 9))
        self.label_instrucoes.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED}; padding: 5px;')
        self.label_instrucoes.setWordWrap(True)
        left_layout.addWidget(self.label_instrucoes)
        left_layout.addSpacing(10)
        self.label_status = QLabel('Pronto para iniciar')
        self.label_status.setFont(QFont('Segoe UI', 12))
        self.label_status.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        left_layout.addWidget(self.label_status)
        main_layout.addWidget(left_widget, stretch=1)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setAlignment(Qt.AlignCenter)
        self.phone_container = QFrame()
        self.phone_container.setFixedSize(250, 250)
        self.phone_container.setStyleSheet(f'\n            background-color: {CoresUnion.BACKGROUND_DARK};\n            border-radius: 125px;\n            border: 2px solid {CoresUnion.BORDER};\n        ')
        phone_layout = QVBoxLayout(self.phone_container)
        phone_layout.setAlignment(Qt.AlignCenter)
        self.phone_image = QLabel()
        self.phone_image.setFixedSize(140, 140)
        self.phone_image.setAlignment(Qt.AlignCenter)
        phone_layout.addWidget(self.phone_image)
        right_layout.addWidget(self.phone_container)
        self.label_phone_status = QLabel('')
        self.label_phone_status.setAlignment(Qt.AlignCenter)
        self.label_phone_status.setFont(QFont('Segoe UI', 11))
        self.label_phone_status.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED}; margin-top: 15px;')
        right_layout.addWidget(self.label_phone_status)
        main_layout.addWidget(right_widget, stretch=1)
        self._set_phone_image('notfound')
    def _init_animation(self):
        self.spinner_anim = QVariantAnimation()
        self.spinner_anim.setDuration(3000)
        self.spinner_anim.setStartValue(0)
        self.spinner_anim.setEndValue(360)
        self.spinner_anim.setLoopCount(-1)
        self.spinner_anim.valueChanged.connect(self._rotate_phone)
        self.original_pixmap = None
    def _set_phone_image(self, status: str):
        images = {'notfound': 'phone_notfound.png', 'loading': 'phone_loading.png', 'connected': 'phone_connected.png', 'success': 'phone_success.png', 'error': 'phone_error.png'}
        styles = {'notfound': f'background-color: {CoresUnion.BACKGROUND_DARK}; border-radius: 125px; border: 2px solid {CoresUnion.BORDER};', 'loading': f'background-color: {CoresUnion.BACKGROUND_DARK}; border-radius: 125px; border: 2px solid {CoresUnion.PRIMARY};', 'connected': f'background-color: {CoresUnion.BACKGROUND_DARK}; border-radius: 125px; border: 2px solid {CoresUnion.PRIMARY};', 'success': f'background-color: {CoresUnion.SUCCESS}; border-radius: 125px; border: 2px solid {CoresUnion.SUCCESS};', 'error': f'background-color: {CoresUnion.ERROR}; border-radius: 125px; border: 2px solid {CoresUnion.ERROR};'}
        self.phone_container.setStyleSheet(styles.get(status, styles['notfound']))
        img_path = self._get_img_path(images.get(status, 'phone_notfound.png'))
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.phone_image.setPixmap(pixmap)
            if status == 'loading':
                self.original_pixmap = pixmap
    def _rotate_phone(self, angle: int):
        if self.original_pixmap:
            rotated = self.original_pixmap.transformed(QTransform().rotate(angle), Qt.SmoothTransformation)
            xoffset = (rotated.width() - self.original_pixmap.width()) // 2
            yoffset = (rotated.height() - self.original_pixmap.height()) // 2
            self.phone_image.setPixmap(rotated.copy(xoffset, yoffset, self.original_pixmap.width(), self.original_pixmap.height()))
    def _start_spinner(self):
        self._set_phone_image('loading')
        self.spinner_anim.start()
    def _stop_spinner(self):
        self.spinner_anim.stop()
    def executar_frp(self):
        if self.em_execucao:
            return
        reply = QMessageBox.question(self, 'Confirmar - FRP OLD', "Este metodo funciona em Motorolas ANTIGOS:\n- Moto G5 / G5 Plus / G5S\n- Moto G6 / G6 Plus / G6 Play\n- Alguns Moto G7\n\nIMPORTANTE: Funciona APENAS em aparelhos\nque habilitam Factory Mode. Alguns modelos\nmesmo listados podem NAO ser compativeis.\n\nO dispositivo deve estar em FACTORY MODE:\n1. Desligue o aparelho\n2. Segure Vol- + Power\n3. Selecione 'Factory Mode' ou 'BP Tools'\n4. Conecte o cabo USB\n\nDeseja continuar?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.em_execucao = True
        self.label_status.setText('Procurando Factory Mode...')
        self.label_status.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        self.label_phone_status.setText('Conecte em Factory Mode')
        self._start_spinner()
        self.barra_progresso.setValue(5)
        self.worker = FrpOldWorker(self.MODELO)
        self.worker.progress_signal.connect(self.barra_progresso.setValue)
        self.worker.status_signal.connect(self._on_status)
        self.worker.log_signal.connect(self._on_log)
        self.worker.finished_signal.connect(self._on_finished)
        self.btn_frp.setEnabled(False)
        self.worker.start()
    def _on_log(self, msg: str):
        pass
    def _on_status(self, status: str):
        status_map = {'waiting': ('Aguardando Factory Mode...', CoresUnion.TEXT_MUTED, 'loading', 'Entre em Factory Mode'), 'factory_detected': ('Factory Mode detectado!', CoresUnion.PRIMARY, 'connected', 'Injetando Karnel...'), 'injecting': ('Ativando ADB - Verifique a tela!', CoresUnion.WARNING, 'loading', 'Verifique a tela do dispositivo'), 'adb_detected': ('ADB ativado!', CoresUnion.PRIMARY, 'connected', 'Executando bypass...'), 'adb_unauthorized': ('Aceite na tela do dispositivo!', CoresUnion.WARNING, 'connected', "Toque em 'Permitir' na tela"), 'bypassing': ('Executando bypass FRP...', CoresUnion.PRIMARY, 'loading', 'Quase la...'), 'success': ('FRP removido com sucesso!', CoresUnion.SUCCESS, 'success', 'Restaure de fabrica'), 'error': ('Falha no processo', CoresUnion.ERROR, 'error', 'Verifique e tente novamente')}
        if status in status_map:
            text, color, image, phone_text = status_map[status]
            self.label_status.setText(text)
            self.label_status.setStyleSheet(f'color: {color};')
            self.label_phone_status.setText(phone_text)
            if status in ('success', 'error'):
                self._stop_spinner()
                self._set_phone_image(image)
                return
            if status in ('factory_detected', 'adb_detected', 'adb_unauthorized'):
                self._stop_spinner()
                self._set_phone_image('connected')
    def _on_finished(self, sucesso: bool, msg: str):
        self.em_execucao = False
        self.btn_frp.setEnabled(True)
        self._stop_spinner()
        if sucesso:
            self._set_phone_image('success')
            self.barra_progresso.setValue(100)
            QMessageBox.information(self, 'Sucesso', msg)
            return
        self._set_phone_image('error')
        QMessageBox.warning(self, 'Aviso', msg)
    def parar(self):
        if self.em_execucao:
            if self.worker:
                self.worker.cancelar()
            self.em_execucao = False
            self.btn_frp.setEnabled(True)
            self._stop_spinner()
            self._set_phone_image('notfound')
            self.label_status.setText('Processo interrompido')
            self.label_status.setStyleSheet(f'color: {CoresUnion.WARNING};')
            self.label_phone_status.setText('')
            self.barra_progresso.setValue(0)
