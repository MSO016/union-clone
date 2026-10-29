from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QApplication, QLabel, QLineEdit, QPushButton, QMessageBox, QShortcut, QCheckBox, QHBoxLayout, QFrame, QTabWidget, QSizePolicy, QProgressDialog, QGraphicsOpacityEffect)
from PyQt5.QtCore import (Qt, QSettings, QTimer, QSize, QPropertyAnimation, QEasingCurve, QVariantAnimation, QAbstractAnimation)
from PyQt5.QtGui import (QIcon, QKeySequence, QPixmap, QColor)
import os
import platform
import requests
import json
import uuid
from datetime import datetime, timedelta
from machineid import id as get_machine_id
from app.utils.path_manager import PathManager
from app.utils.user_database import UserDatabaseManager
from app.utils.painel_administrativo import PainelAdministrativo
from app.utils.translation_manager import TranslationManager
import logging
import hashlib
import base64
from pathlib import Path
from cryptography.fernet import Fernet
import nacl.signing
import nacl.encoding
import pymysql
from app.utils._app_cfg import REFS, db_config
logger = logging.getLogger(__name__)
PRIMARY_DARK = '#0D47A1'
PRIMARY_LIGHT = '#2196F3'
ACCENT = '#00B0FF'
SUCCESS = '#00E676'
DANGER = '#FF1744'
BACKGROUND = '#ECEFF1'
TEXT_PRIMARY = '#263238'
TEXT_SECONDARY = '#607D8B'
BORDER_COLOR = '#CFD8DC'
VERSAO_LOCAL = '1.3.4.5'
MYSQL_CONFIG = db_config(ssl={'ca': None}, ssl_verify_cert=False)
def _standalone_volume_serial():
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        serial = ctypes.c_ulong(0)
        result = kernel32.GetVolumeInformationW('C:\\', ctypes.create_unicode_buffer(256), 256, ctypes.byref(serial), ctypes.byref(ctypes.c_ulong(0)), ctypes.byref(ctypes.c_ulong(0)), ctypes.create_unicode_buffer(256), 256)
        if result and serial.value != 0:
            return f'{serial.value:08X}'
    except Exception:
        pass
    return ''
class ValidationCache:
    def __init__(self, cache_dir=None):
        if cache_dir is None:
            appdata_path = os.path.join(os.getenv('LOCALAPPDATA'), 'TechniciansUnion', 'cache')
            cache_dir = appdata_path
        self.cache_dir = Path(cache_dir)
        try:
            if not self.cache_dir.exists():
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                if platform.system().lower() == 'windows':
                    import subprocess
                    si = subprocess.STARTUPINFO()
                    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    si.wShowWindow = subprocess.SW_HIDE
                    subprocess.run(['attrib', '+H', str(self.cache_dir)], check=False, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            logger.error(f'Erro ao criar diret├│rio de cache: {str(e)}')
            import tempfile
            self.cache_dir = Path(tempfile.gettempdir()) / 'TechniciansUnion' / 'cache'
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        machine_id = get_machine_id()
        self.encryption_key = self._generate_key(machine_id)
        self.fernet = Fernet(self.encryption_key)
    def _generate_key(self, seed):
        hardware_info = [seed, _standalone_volume_serial() or 'no-vol-serial', platform.machine(), platform.processor()]
        combined = ''.join(hardware_info).encode()
        key_hash = hashlib.sha256(combined).digest()
        return base64.urlsafe_b64encode(key_hash[:32])
    def _encrypt_data(self, data):
        json_data = json.dumps(data)
        return self.fernet.encrypt(json_data.encode())
    def _decrypt_data(self, encrypted_data):
        try:
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data)
        except:
            return
    def _get_cache_file(self, fingerprint):
        safe_name = hashlib.sha256(fingerprint.encode()).hexdigest()[:32]
        return self.cache_dir / f'validation_{safe_name}.enc'
    def _get_hardware_hash(self):
        hardware_info = [get_machine_id(), _standalone_volume_serial() or 'no-vol-serial', platform.machine(), platform.processor()]
        combined = ''.join(hardware_info).encode()
        return hashlib.sha256(combined).hexdigest()
    def save_validation(self, fingerprint, validation_data, ttl_days=1):
        try:
            cache_file = self._get_cache_file(fingerprint)
            try:
                if cache_file.exists():
                    cache_file.unlink()
            except Exception as e:
                logger.warning(f'N├úo foi poss├¡vel remover cache existente: {str(e)}')
                cache_file = self.cache_dir / f'validation_{fingerprint}_{uuid.uuid4().hex[:8]}.enc'
            else:
                cache_data = {'fingerprint': fingerprint, 'validation_data': validation_data, 'expires_at': (datetime.now() + timedelta(days=ttl_days)).isoformat(), 'created_at': datetime.now().isoformat(), 'hardware_hash': self._get_hardware_hash()}
                encrypted_data = self._encrypt_data(cache_data)
        except Exception as e:
            logger.error(f'Erro ao salvar cache: {str(e)}')
            try:
                self.clear_expired()
            except:
                pass
        with open(cache_file, 'xb') as f:
            f.write(encrypted_data)
        try:
            logger.info(f'Cache salvo com sucesso para fingerprint: {fingerprint}')
        except Exception as e:
            logger.error(f'Erro ao salvar cache: {str(e)}')
            try:
                self.clear_expired()
            except:
                pass
        return True
    def get_validation(self, fingerprint):
        try:
            cache_file = self._get_cache_file(fingerprint)
            if not cache_file.exists():
                return
            with open(cache_file, 'rb') as f:
                encrypted_data = f.read()
            cache_data = self._decrypt_data(encrypted_data)
            if not cache_data:
                logger.warning('Cache corrompido ou adulterado')
                return
            if cache_data.get('hardware_hash') != self._get_hardware_hash():
                logger.warning('Hardware diferente detectado')
                return
            expires_at = datetime.fromisoformat(cache_data['expires_at'])
            if datetime.now() > expires_at:
                logger.info(f'Cache expirado para fingerprint: {fingerprint}')
                cache_file.unlink(missing_ok=True)
                return
            if cache_data['fingerprint'] != fingerprint:
                logger.warning('Fingerprint n├úo corresponde')
                return
            logger.info(f'Cache v├ílido encontrado para fingerprint: {fingerprint}')
        except Exception as e:
            logger.error(f'Erro ao ler cache: {str(e)}')
        return cache_data['validation_data']
    def clear_expired(self):
        try:
            for cache_file in self.cache_dir.glob('validation_*.enc'):
                pass
            try:
                with open(cache_file, 'rb') as f:
                    encrypted_data = f.read()
                cache_data = self._decrypt_data(encrypted_data)
                if not cache_data:
                    cache_file.unlink()
            except:
                cache_file.unlink(missing_ok=True)
        except Exception as e:
            logger.error(f'Erro ao limpar caches expirados: {str(e)}')
            try:
                try:
                    for cache_file in self.cache_dir.glob('validation_*.enc'):
                        pass
                except:
                    cache_file.unlink(missing_ok=True)
            except Exception as e:
                logger.error(f'Erro ao limpar caches expirados: {str(e)}')
    def clear_all_cache_robust(self, silent=True):
        import time
        removed = 0
        try:
            if not self.cache_dir.exists():
                return 0
            for cache_file in list(self.cache_dir.glob('validation_*.enc')):
                ok = False
                for _ in range(3):
                    pass
            try:
                cache_file.unlink(missing_ok=True)
                if not cache_file.exists():
                    ok = True
            except (PermissionError, OSError):
                time.sleep(0.05)
            else:
                if ok:
                    removed += 1
                logger.warning('LIC-101')
                residual = list(self.cache_dir.glob('validation_*.enc'))
                for f in residual:
                    pass
        except Exception:
            logger.error('LIC-100')
        if residual:
            logger.warning(f'LIC-102:{len(residual)}')
        if not silent:
            logger.info(f'LIC-103:{removed}')
        return removed
class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_db = UserDatabaseManager()
        self.translation_manager = TranslationManager.get_instance()
        self.validation_cache = ValidationCache()
        migration_file = Path(os.getenv('LOCALAPPDATA')) / 'TechniciansUnion' / '.fp_migration_v2'
        if not migration_file.exists():
            self.force_cache_cleanup()
        migration_v3 = Path(os.getenv('LOCALAPPDATA')) / 'TechniciansUnion' / '.fp_migration_v3'
        if not migration_v3.exists():
            self._migrate_fingerprint_v3()
        migration_v4 = Path(os.getenv('LOCALAPPDATA')) / 'TechniciansUnion' / '.fp_migration_v4'
        if not migration_v4.exists():
            self._migrate_fingerprint_v4()
        migration_v5 = Path(os.getenv('LOCALAPPDATA')) / 'TechniciansUnion' / '.fp_migration_v5'
        if not migration_v5.exists():
            self._migrate_cache_v5()
        self.api_url = REFS.VK_URL
        self.account_id = REFS.VK_ACC
        self.product_id = REFS.VK_PRD
        self.product_token = REFS.VK_TKN
        self.translation_manager.language_changed.connect(self.refresh_interface)
        icon = QIcon(PathManager.get_resource_path('icon.png'))
        self.setWindowIcon(icon)
        self.setup_ui()
        self._fade_in_done = False
        try:
            self.setWindowOpacity(0.0)
        except Exception:
            self._fade_in_done = True
        self.load_saved_license()
    def showEvent(self, event):
        super().showEvent(event)
        if self._fade_in_done:
            return
        self._fade_in_done = True
        try:
            self._fade_anim = QPropertyAnimation(self, b'windowOpacity')
            self._fade_anim.setDuration(400)
            self._fade_anim.setStartValue(0.0)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
            self._fade_anim.start()
            return
        except Exception:
            self.setWindowOpacity(1.0)
    def eventFilter(self, obj, event):
        if getattr(self, '_btn_anim_active', False) and obj is self.activate_btn:
            from PyQt5.QtCore import QEvent
            if event.type() == QEvent.Enter:
                if getattr(self, '_pulse_active', False):
                    self._pulse_anim.stop()
                    self._pulse_effect.setOpacity(1.0)
                self._btn_anim.setDirection(QAbstractAnimation.Forward)
                self._btn_anim.start()
            elif event.type() == QEvent.Leave:
                self._btn_anim.setDirection(QAbstractAnimation.Backward)
                self._btn_anim.start()
        return super().eventFilter(obj, event)
    def conectar_mysql(self):
        try:
            return pymysql.connect(**MYSQL_CONFIG, **{'cursorclass': pymysql.cursors.DictCursor, 'autocommit': False})
        except Exception as e:
            logger.error(f'Erro ao conectar ao MySQL: {str(e)}')
    def verificar_usuario_mysql(self, email):
        try:
            conn = self.conectar_mysql()
            if not conn:
                logger.error('Nao foi possivel conectar ao MySQL para verificar usuario')
                return
            cursor = conn.cursor()
            cursor.execute('SELECT id_usuario, licenca, nome_usuario, status FROM usuarios WHERE email = %s', (email,))
            usuario = cursor.fetchone()
            cursor.close()
            conn.close()
            return usuario
        except Exception as e:
            logger.error(f'Erro ao verificar usuario no MySQL: {str(e)}')
    def verificar_perfil_completo(self, user_id):
        try:
            conn = self.conectar_mysql()
            if not conn:
                logger.warning('N├úo foi poss├¡vel verificar perfil - assumindo incompleto')
                return False
            cursor = conn.cursor()
            cursor.execute('SELECT nome FROM perfil WHERE id_usuario = %s LIMIT 1', (user_id,))
            perfil = cursor.fetchone()
            cursor.close()
            conn.close()
            if perfil and perfil.get('nome') and len(perfil['nome'].strip()) >= 3:
                logger.info(f'Ô£à Perfil completo detectado para user_id={user_id}')
                return True
            logger.info(f'ÔÜá´©Å Perfil incompleto para user_id={user_id} - wizard ser├í exibido')
            return False
        except Exception as e:
            logger.error(f'Erro ao verificar perfil: {str(e)} - assumindo incompleto')
            return False
    def criar_usuario_mysql(self, email):
        conn = None
        cursor = None
        try:
            conn = self.conectar_mysql()
            if not conn:
                logger.error('N├úo foi poss├¡vel conectar ao MySQL para criar usu├írio')
                return (False, 'Erro de conexao com o servidor. Tente novamente.')
            cursor = conn.cursor()
            cursor.execute('SELECT id_usuario FROM usuarios WHERE email = %s', (email,))
            usuario_existente = cursor.fetchone()
            if usuario_existente:
                logger.info(f'Usuario {email} ja existe (ID: {usuario_existente[0]}) - usando registro existente')
                cursor.close()
                conn.close()
                return True, usuario_existente[0]
            import time
            licenca_unica = f'UNION-{int(time.time())}-{str(uuid.uuid4())[:8].upper()}'
            nome_inicial = email.split('@')[0]
            cursor.execute("\n                INSERT INTO usuarios (email, licenca, nome_usuario, data_registro, ultimo_login, status)\n                VALUES (%s, %s, %s, NOW(), NOW(), 'ativo')\n            ", (email, licenca_unica, nome_inicial))
            user_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f'Usu├írio criado no MySQL - ID: {user_id}, Email: {email}, Licen├ºa: {licenca_unica}')
        except Exception as e:
            error_str = str(e)
            logger.error(f'Erro ao criar usu├írio no MySQL: {error_str}')
            try:
                if cursor:
                    cursor.close()
                if conn:
                    conn.rollback()
                    conn.close()
            except:
                pass
            if '1062' in error_str or 'Duplicate' in error_str:
                pass
        return True, user_id
    def atualizar_ultimo_login(self, email):
        try:
            conn = self.conectar_mysql()
            if not conn:
                return False
            cursor = conn.cursor()
            cursor.execute('UPDATE usuarios SET ultimo_login = NOW() WHERE email = %s', (email,))
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f'├Ültimo login atualizado para: {email}')
            return True
        except Exception as e:
            logger.error(f'Erro ao atualizar ├║ltimo login: {str(e)}')
            return False
    def verificar_versao_sistema(self):
        try:
            logger.info(f'­ƒöì Verificando vers├úo do sistema... VERSAO_LOCAL = {VERSAO_LOCAL}')
            conn = pymysql.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM configuracoes LIMIT 1')
            config = cursor.fetchone()
            cursor.close()
            conn.close()
            if not config:
                self.show_version_error('Erro de Configura├º├úo', 'N├úo foi poss├¡vel verificar a vers├úo do sistema.\nTente novamente mais tarde.')
                return False
            versao_atual = config[1]
            link_download = config[2]
            mensagem_aviso = config[3]
            manutencao_ativa = bool(config[4])
            mensagem_manutencao = config[5]
            logger.info(f'­ƒôè Configura├º├úo obtida: versao_atual={versao_atual}, manutencao_ativa={manutencao_ativa}')
            if manutencao_ativa:
                logger.info('­ƒöº Sistema em manuten├º├úo - BLOQUEANDO todos os usu├írios')
                self.show_maintenance_window(mensagem_manutencao)
                return False
            if VERSAO_LOCAL != versao_atual:
                logger.info(f'ÔØî Vers├úo desatualizada: {VERSAO_LOCAL} != {versao_atual}')
                self.show_update_window(mensagem_aviso, link_download, versao_atual)
                return False
            logger.info(f'Ô£à Vers├úo autorizada: {VERSAO_LOCAL}')
            return True
        except Exception as e:
            logger.error(f'ÔØî Erro ao verificar vers├úo: {e}')
            self.show_version_error('Erro de Conex├úo', 'N├úo foi poss├¡vel verificar a vers├úo do sistema.\n\nPoss├¡veis causas:\nÔÇó Sem conex├úo com a internet\nÔÇó Firewall bloqueando a conex├úo\nÔÇó Servi├ºos temporariamente indispon├¡veis\n\nTente novamente em alguns minutos.')
            return False
    def _get_volume_serial(self):
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            serial_number = ctypes.c_ulong(0)
            result = kernel32.GetVolumeInformationW('C:\\', ctypes.create_unicode_buffer(256), 256, ctypes.byref(serial_number), ctypes.byref(ctypes.c_ulong(0)), ctypes.byref(ctypes.c_ulong(0)), ctypes.create_unicode_buffer(256), 256)
            if result and serial_number.value != 0:
                return f'{serial_number.value:08X}'
        except Exception:
            pass
        return ''
    def _is_running_in_vm(self):
        try:
            from app.utils._cfg_probe import detect_virtual_machine
            detections = detect_virtual_machine()
            for d in detections or []:
                if d.get('k') == 'vm':
                    return True
        except Exception:
            return False
        try:
            return False
        except Exception:
            return False
    def get_machine_fingerprint(self):
        try:
            logger.info('Iniciando gera├º├úo de fingerprint...')
            machine_id = get_machine_id()
            if not machine_id:
                raise ValueError('MachineGuid indispon├¡vel')
            vol_serial = self._get_volume_serial()
            if vol_serial:
                seed = f'{machine_id}:{vol_serial}'
            else:
                logger.warning('VolumeSerial indispon├¡vel, usando apenas MachineGuid')
                seed = machine_id
            hash_object = hashlib.sha256(seed.encode())
            hex_dig = hash_object.hexdigest()
            fingerprint = ':'.join((hex_dig[i:i + 2] for i in range(0, 64, 2)))
            logger.info(f'Fingerprint gerado com sucesso: {fingerprint}')
        except Exception as e:
            logger.error(f'Erro ao gerar fingerprint v4: {str(e)}', exc_info=True)
            try:
                machine_id_fallback = get_machine_id()
                if machine_id_fallback:
                    h = hashlib.sha256(machine_id_fallback.encode()).hexdigest()
                    fallback_fp = ':'.join((h[i:i + 2] for i in range(0, 64, 2)))
                    logger.warning('Usando fingerprint fallback (MachineGuid puro)')
                    return fallback_fp
            except Exception:
                pass
        return fingerprint
    def get_headers(self):
        return {'Content-Type': 'application/vnd.api+json', 'Accept': 'application/vnd.api+json', 'Authorization': f'Bearer {self.product_token}'}
    def get_existing_machine(self, machine_fingerprint, license_id=None):
        if not machine_fingerprint:
            return
        headers = self.get_headers()
        if license_id:
            try:
                url = f'{self.api_url}/accounts/{self.account_id}/licenses/{license_id}/machines'
                logger.info(f'Buscando m├íquina na licen├ºa: {license_id}')
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    machines_data = response.json().get('data', [])
                    logger.info(f'M├íquinas na licen├ºa: {len(machines_data)}')
                    for machine in machines_data:
                        if machine.get('attributes', {}).get('fingerprint') == machine_fingerprint:
                            machine_id = machine.get('id')
                            logger.info(f'M├íquina encontrada (por licen├ºa): {machine_id}')
                            return machine_id
                    logger.info('Fingerprint n├úo encontrado nesta licen├ºa')
                    return
            except requests.exceptions.RequestException as e:
                logger.warning(f'Falha na busca por licen├ºa, tentando fallback: {str(e)}')
        try:
            url = f'{self.api_url}/accounts/{self.account_id}/machines'
            params = {'fingerprint': machine_fingerprint, 'limit': 10}
            logger.info('Fallback: busca global com valida├º├úo de licen├ºa')
            response = requests.get(url, headers=headers, params=params, timeout=15)
            if response.status_code == 200:
                machines_data = response.json().get('data', [])
                for machine in machines_data:
                    if machine.get('attributes', {}).get('fingerprint') == machine_fingerprint:
                        machine_license_id = machine.get('relationships', {}).get('license', {}).get('data', {}).get('id')
                        if license_id and machine_license_id != license_id:
                            logger.warning('M├íquina encontrada mas pertence a outra licen├ºa - ignorando')
                            return
                        machine_id = machine.get('id')
                        logger.info(f'M├íquina encontrada (fallback global): {machine_id}')
                        return machine_id
            logger.info('Nenhuma m├íquina encontrada')
        except Exception as e:
            logger.error(f'Exce├º├úo ao buscar m├íquina: {str(e)}')
    def get_license_id(self, license_key):
        try:
            url = f'{self.api_url}/accounts/{self.account_id}/licenses/actions/validate-key'
            headers = self.get_headers()
            data = {'meta': {'key': license_key}}
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                license_data = response.json().get('data', {})
                return license_data.get('id')
        except Exception as e:
            print(f'Erro ao obter ID da licen├ºa: {str(e)}')
    def register_machine(self, email, license_key):
        try:
            machine_fingerprint = self.get_machine_fingerprint()
            if not machine_fingerprint:
                logger.error('Fingerprint indispon├¡vel - imposs├¡vel registrar m├íquina')
                return (None, 'Erro de identifica├º├úo do computador. Por favor, reinicie e tente novamente.')
            logger.info(f'Tentando registrar/recuperar m├íquina para fingerprint: {machine_fingerprint}')
            license_id = self.get_license_id(license_key)
            if not license_id:
                logger.error('Falha ao obter ID da licen├ºa')
                return (None, 'N├úo foi poss├¡vel obter o ID da licen├ºa. Por favor, verifique se a chave est├í correta.')
            existing_machine_id = self.get_existing_machine(machine_fingerprint, license_id)
            if existing_machine_id:
                logger.info(f'M├íquina existente encontrada: {existing_machine_id}')
                return existing_machine_id, None
            logger.info(f'Registrando nova m├íquina para licen├ºa ID: {license_id}')
            url = f'{self.api_url}/accounts/{self.account_id}/machines'
            headers = self.get_headers()
            data = {'data': {'type': 'machines', 'attributes': {'fingerprint': machine_fingerprint, 'name': f'{platform.node()} ({email})', 'platform': platform.system().lower(), 'hostname': platform.node(), 'cores': os.cpu_count(), 'metadata': {'user_email': email, 'registration_date': datetime.now().isoformat()}}, 'relationships': {'license': {'data': {'type': 'licenses', 'id': license_id}}}}}
            response = requests.post(url, headers=headers, json=data)
            response_data = response.json()
            if response.status_code == 201:
                machine_data = response_data.get('data', {})
                machine_id = machine_data.get('id')
                logger.info(f'Nova m├íquina registrada com sucesso: {machine_id}')
                return machine_id, None
            errors = response_data.get('errors', [])
            for error in errors:
                code = error.get('code')
                detail = error.get('detail', '')
                logger.error(f'Erro ao registrar m├íquina: {code} - {detail}')
                if code == 'FINGERPRINT_TAKEN':
                    logger.info('Fingerprint j├í existe, tentando recuperar m├íquina')
                    existing_machine_id = self.get_existing_machine(machine_fingerprint, license_id)
                    if existing_machine_id:
                        return existing_machine_id, None
                    return (None, "ÔÜá´©Å Este computador j├í est├í vinculado a outra licen├ºa.\n\nIsso pode acontecer quando:\n1. Voc├¬ j├í utilizou outra licen├ºa neste computador\n2. Houve uma troca de plano ou migra├º├úo de licen├ºa\n\nPara resolver, entre em contato com o suporte informando seu email e o nome do computador.\n\nWhatsApp Suporte oficial: <a href='https://wa.me/558594129977'>+55 85 9412-9977</a>\nWhatsApp (atendimento): <a href='https://wa.me/5585997507465'>+55 85 99750-7465</a>")
                if code == 'MACHINE_LIMIT_EXCEEDED':
                    return (None, "ÔÜá´©Å Esta licen├ºa j├í est├í ativa em outro computador.\n\nCada licen├ºa permite uso em apenas 1 m├íquina por vez.\nPara usar neste computador, entre em contato com o suporte para desativar a m├íquina anterior.\n\nWhatsApp Suporte oficial: <a href='https://wa.me/558594129977'>+55 85 9412-9977</a>\nWhatsApp (atendimento): <a href='https://wa.me/5585997507465'>+55 85 99750-7465</a>")
        except Exception as e:
            logger.error(f'Exce├º├úo ao registrar m├íquina: {str(e)}')
            return (None, 'Erro ao registrar m├íquina. Por favor, tente novamente.')
        try:
            logger.error(f'Erro final ao registrar m├íquina: {errors}')
            return (None, "ÔÜá´©Å N├úo foi poss├¡vel ativar este computador.\n\nPor favor, tente novamente. Se o problema persistir, entre em contato com o suporte.\n\nWhatsApp Suporte oficial: <a href='https://wa.me/558594129977'>+55 85 9412-9977</a>\nWhatsApp (atendimento): <a href='https://wa.me/5585997507465'>+55 85 99750-7465</a>")
        except Exception as e:
            logger.error(f'Exce├º├úo ao registrar m├íquina: {str(e)}')
            return (None, 'Erro ao registrar m├íquina. Por favor, tente novamente.')
    def get_error_message(self, code, detail):
        base_contact = "\n\nPara suporte, acesse:\nSite: <a href='https://restorecellsolucoes.com'>https://restorecellsolucoes.com</a>\nWhatsApp Suporte oficial: <a href='https://wa.me/558594129977'>+55 85 9412-9977</a>\nWhatsApp (atendimento): <a href='https://wa.me/5585997507465'>+55 85 99750-7465</a>\n\nSuporte oficial no Instagram:\n<a href='https://instagram.com/restorecell10'>@restorecell10</a>"
        messages = {'EXPIRED': f'ÔÜá´©Å Sua licen├ºa expirou!\nPor favor, entre em contato com nosso suporte para renovar.{base_contact}', 'SUSPENDED': f'ÔÜá´©Å Sua licen├ºa foi suspensa!\nPor favor, entre em contato com o suporte para mais informa├º├Áes.{base_contact}', 'INVALID': f'ÔÜá´©Å Licen├ºa inv├ílida!\nVerifique se digitou corretamente ou adquira uma nova licen├ºa com nosso suporte.{base_contact}', 'NOT_FOUND': f'ÔÜá´©Å Licen├ºa n├úo encontrada!\nVerifique se digitou corretamente ou adquira uma licen├ºa com nosso suporte.{base_contact}', 'MACHINE_LIMIT_EXCEEDED': f'ÔÜá´©Å Licen├ºa em uso em outra m├íquina!\nEsta licen├ºa j├í est├í sendo utilizada em outro computador. Para usar nesta m├íquina, voc├¬ precisa primeiro desativar a licen├ºa no outro computador ou entrar em contato com o suporte.{base_contact}', 'PRODUCT_SCOPE_MISMATCH': f'ÔÜá´©Å Esta licen├ºa n├úo ├® v├ílida para a vers├úo 1.3 do UNION TECHNICAL!\nPor favor, adquira uma licen├ºa compat├¡vel com a vers├úo 1.3 atrav├®s de nosso suporte.{base_contact}', 'PRODUCT_MISMATCH': f'ÔÜá´©Å Esta licen├ºa n├úo ├® v├ílida para a vers├úo 1.3 do TECH UNION SOLUTIONS!\nPor favor, adquira uma licen├ºa compat├¡vel com a vers├úo 1.3 atrav├®s de nosso suporte.{base_contact}', 'USER_SCOPE_MISMATCH': f'ÔÜá´©Å Email incorreto!\nO email informado n├úo corresponde ao email registrado na licen├ºa. Por favor, use o mesmo email utilizado na compra da licen├ºa.{base_contact}', 'NO_MACHINE': f'ÔÜá´©Å Erro de ativa├º├úo - M├íquina n├úo est├í ativada!\n\nEste erro ocorre geralmente quando:\n1. ├ë a primeira vez que voc├¬ tenta ativar neste computador\n2. Houve uma altera├º├úo de hardware no seu computador\n3. Houve um erro na comunica├º├úo com o servidor de licen├ºas\n\nPor favor, tente novamente. Se o erro persistir, entre em contato com o suporte t├®cnico atrav├®s do WhatsApp: +55 85 9412-9977 ou +55 85 99750-7465{base_contact}'}
        if 'machine is not activated' in str(detail).lower() or 'has no associated machines' in str(detail).lower():
            return messages['NO_MACHINE']
        if 'user scope does not match' in str(detail).lower():
            return messages['USER_SCOPE_MISMATCH']
        if 'machine scope does not match' in str(detail).lower() or 'machine limit exceeded' in str(detail).lower():
            return messages['MACHINE_LIMIT_EXCEEDED']
        return messages.get(code, f'ÔÜá´©Å {detail}{base_contact}')
    def show_error_message(self, title, message):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setTextFormat(Qt.RichText)
        msg.exec_()
    def validate_license(self, email, license_key):
        try:
            self.user_domain = email.split('@')[-1].lower() if '@' in email else ''
            fingerprint = f'{email}:{license_key}'
            progress = QProgressDialog('Validando licen├ºa...', None, 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setAutoClose(True)
            progress.setValue(0)
            url = f'{self.api_url}/accounts/{self.account_id}/licenses/actions/validate-key'
            headers = self.get_headers()
            data = {'meta': {'key': license_key}}
            license_data = {}
            try:
                response = requests.post(url, headers=headers, json=data)
                if response.status_code != 200:
                    error_msg = "ÔÜá´©Å Licen├ºa inv├ílida!\n\nA chave de licen├ºa informada n├úo ├® v├ílida. Por favor:\n1. Verifique se digitou a chave corretamente\n2. Certifique-se de que est├í usando uma licen├ºa oficial\n3. Se voc├¬ ainda n├úo tem uma licen├ºa, adquira atrav├®s de nosso site oficial\n\nPara suporte ou aquisi├º├úo, acesse:\nSite: <a href='https://restorecellsolucoes.com'>https://restorecellsolucoes.com</a>\nWhatsApp Suporte oficial: <a href='https://wa.me/558594129977'>+55 85 9412-9977</a>\nWhatsApp (atendimento): <a href='https://wa.me/5585997507465'>+55 85 99750-7465</a>"
                    return False, error_msg, {}
                response_data = response.json()
                license_raw_data = response_data.get('data', {})
                if not license_raw_data:
                    raise ValueError('Dados da licen├ºa n├úo encontrados')
                license_attributes = license_raw_data.get('attributes', {})
                license_data = {'id': license_raw_data.get('id'), 'key': license_attributes.get('key'), 'name': license_attributes.get('name'), 'expiry': license_attributes.get('expiry'), 'created': license_attributes.get('created'), 'status': license_attributes.get('status'), 'uses': license_attributes.get('uses', 0), 'maxUses': license_attributes.get('maxUses'), 'suspended': license_attributes.get('suspended', False)}
                license_product = license_raw_data.get('relationships', {}).get('product', {}).get('data', {}).get('id')
                if license_product != self.product_id:
                    error_msg = "ÔÜá´©Å Licen├ºa incompat├¡vel!\n\nEsta licen├ºa n├úo ├® v├ílida para a vers├úo 1.3 do TECH UNION SOLUTIONS.\nPor favor, certifique-se de que est├í usando a licen├ºa correta para esta vers├úo.\n\nPara adquirir uma licen├ºa compat├¡vel, acesse:\nSite: <a href='https://restorecellsolucoes.com'>https://restorecellsolucoes.com</a>\nWhatsApp Suporte oficial: <a href='https://wa.me/558594129977'>+55 85 9412-9977</a>\nWhatsApp (atendimento): <a href='https://wa.me/5585997507465'>+55 85 99750-7465</a>"
                    self.validation_cache.save_validation(fingerprint, {'valid': False, 'error_msg': error_msg, 'error_type': 'PRODUCT_MISMATCH', 'license_data': license_data}, ttl_days=REFS.LIC_CACHE_NEGATIVE_TTL_DAYS)
            except requests.exceptions.RequestException as e:
                error_msg = "ÔÜá´©Å Erro de conex├úo!\n\nN├úo foi poss├¡vel validar sua licen├ºa devido a um problema de conex├úo.\nPor favor:\n1. Verifique sua conex├úo com a internet\n2. Certifique-se de que n├úo h├í bloqueios de firewall\n3. Tente novamente em alguns minutos\n\nSe o problema persistir, entre em contato com o suporte:\nWhatsApp Suporte oficial: <a href='https://wa.me/558594129977'>+55 85 9412-9977</a>\nWhatsApp (atendimento): <a href='https://wa.me/5585997507465'>+55 85 99750-7465</a>"
                try:
                    return False, error_msg, {}
                except Exception as e:
                    logger.error(f'Exce├º├úo na valida├º├úo: {str(e)}')
                    return False, 'Erro de conex├úo ao validar licen├ºa. Verifique sua internet e tente novamente.', {}
            else:
                return
        except Exception as e:
            logger.error(f'Exce├º├úo na valida├º├úo: {str(e)}')
            return False, 'Erro de conex├úo ao validar licen├ºa. Verifique sua internet e tente novamente.', {}
        return False, self.get_error_message('INVALID', error_msg), license_data
    def clear_license_cache(self, email=None, license_key=None):
        try:
            if email and license_key:
                fingerprint = f'{email}:{license_key}'
                cache_file = self.validation_cache._get_cache_file(fingerprint)
                if cache_file.exists():
                    cache_file.unlink()
                    logger.info(f'Cache removido para {email}')
                    return True
                return
            self.validation_cache.clear_expired()
            logger.info('Todo o cache de licen├ºas foi limpo')
            return True
        except Exception as e:
            logger.error(f'Erro ao limpar cache: {str(e)}')
            return False
    def handle_license_activation(self):
        email = self.license_email.text().strip()
        license_key = self.license_key.text().strip()
        if not email or not license_key:
            self.show_error_message('Aviso', 'Preencha todos os campos!')
            return
        try:
            try:
                if self._is_running_in_vm():
                    self.show_error_message('Ambiente n├úo suportado', "Este sistema n├úo pode ser executado neste ambiente.\n\nPara utilizar o sistema, instale em um computador compat├¡vel.\n\nSe acredita que isso ├® um erro, entre em contato com o suporte:\nWhatsApp: <a href='https://wa.me/558594129977'>+55 85 9412-9977</a>")
                    return
            except Exception:
                pass
        except Exception as e:
            logger.error(f'Erro inesperado no handle_license_activation: {str(e)}')
            self.show_error_message('Erro', "Erro inesperado ao validar licen├ºa.\n\nPara suporte, acesse:\nSite: <a href='https://restorecellsolucoes.com'>https://restorecellsolucoes.com</a>\nWhatsApp Suporte oficial: <a href='https://wa.me/558594129977'>+55 85 9412-9977</a>\nWhatsApp (atendimento): <a href='https://wa.me/5585997507465'>+55 85 99750-7465</a>\nSuporte oficial no Instagram:\n<a href='https://instagram.com/restorecell10'>@restorecell10</a>")
        try:
            logger.info('­ƒöì Iniciando verifica├º├úo de vers├úo do sistema...')
            if not self.verificar_versao_sistema():
                logger.info('ÔØî Verifica├º├úo de vers├úo bloqueou o acesso')
                return
            logger.info('Ô£à Verifica├º├úo de vers├úo OK - prosseguindo com autentica├º├úo')
            is_valid, error_msg, license_data = self.validate_license(email, license_key)
            if not is_valid:
                if error_msg:
                    if any((err in error_msg.lower() for err in ('hardware', 'm├íquina', 'device', 'fingerprint'))):
                        logger.info('Tentando valida├º├úo ap├│s limpar cache...')
                        self.clear_license_cache(email, license_key)
                        is_valid, error_msg, license_data = self.validate_license(email, license_key)
            if is_valid:
                logger.info('­ƒöì Verificando usu├írio na tabela usuarios do MySQL...')
                usuario_mysql = self.verificar_usuario_mysql(email)
                if usuario_mysql and usuario_mysql.get('status') not in (None, 'ativo'):
                    _st = usuario_mysql.get('status', '')
                    logger.info(f'LOGIN-BLOCK: usuario {email} status={_st}')
                    self.show_error_message('Acesso Indisponivel', "Seu acesso esta temporariamente indisponivel.\n\nEntre em contato com o suporte para regularizar.\n\nWhatsApp Suporte oficial: <a href='https://wa.me/558594129977'>+55 85 9412-9977</a>\nWhatsApp (atendimento): <a href='https://wa.me/5585997507465'>+55 85 99750-7465</a>")
                    return
                primeira_vez = False
                if not usuario_mysql:
                    logger.info(f'­ƒæñ Usu├írio {email} n├úo existe no MySQL - criando registro b├ísico...')
                    sucesso, resultado = self.criar_usuario_mysql(email)
                    if not sucesso:
                        self.show_error_message('Erro', f'Erro ao registrar usu├írio no sistema:\n{resultado}\n\nTente novamente. Se o problema persistir, contate o suporte.')
                        return
                    primeira_vez = True
                    logger.info(f'Ô£à Usu├írio criado com sucesso no MySQL (ID: {resultado})')
                else:
                    self.atualizar_ultimo_login(email)
                    logger.info(f'Ô£à Usu├írio {email} j├í existe no MySQL - login atualizado')
                is_net_user = self.user_domain and self.user_domain.endswith('.net')
                self.save_license_data(email, license_key)
                self.hide()
                if primeira_vez:
                    usuario_mysql_atual = self.verificar_usuario_mysql(email)
                    user_id = usuario_mysql_atual['id_usuario'] if usuario_mysql_atual else None
                else:
                    user_id = usuario_mysql['id_usuario']
                perfil_completo = False
                if user_id:
                    perfil_completo = self.verificar_perfil_completo(user_id)
                if primeira_vez or not perfil_completo:
                    if primeira_vez:
                        logger.info('­ƒÄ» Primeira vez detectada - abrindo wizard de boas-vindas...')
                    else:
                        logger.info('ÔÜá´©Å Perfil incompleto detectado - abrindo wizard de boas-vindas...')
                    from app.views.welcome_wizard import WelcomeWizard
                    self.perfil_window = WelcomeWizard(email, self)
                    def on_perfil_finished():
                        from app.views.main_window import MainWindow
                        self.main_window = MainWindow(user_id, is_admin=False, user_domain=self.user_domain, user_email=email, fullscreen=True, license_data=license_data, validation_cache=self.validation_cache, license_key=license_key)
                        self.main_window.show()
                    self.perfil_window.finished.connect(on_perfil_finished)
                    self.perfil_window.exec_()
                    return
                logger.info('Ô£à Perfil completo - abrindo sistema principal...')
                from app.views.main_window import MainWindow
                self.main_window = MainWindow(user_id, is_admin=False, user_domain=self.user_domain, user_email=email, fullscreen=True, license_data=license_data, validation_cache=self.validation_cache, license_key=license_key)
                self.main_window.show()
                return
            self.show_error_message('Erro', error_msg)
        except Exception as e:
            logger.error(f'Erro inesperado no handle_license_activation: {str(e)}')
            self.show_error_message('Erro', "Erro inesperado ao validar licen├ºa.\n\nPara suporte, acesse:\nSite: <a href='https://restorecellsolucoes.com'>https://restorecellsolucoes.com</a>\nWhatsApp Suporte oficial: <a href='https://wa.me/558594129977'>+55 85 9412-9977</a>\nWhatsApp (atendimento): <a href='https://wa.me/5585997507465'>+55 85 99750-7465</a>\nSuporte oficial no Instagram:\n<a href='https://instagram.com/restorecell10'>@restorecell10</a>")
    def _apply_svg_icon(self, button, svg_name, icon_size=16):
        try:
            icons_dir = PathManager.get_resource_path('icons_svg')
            svg_path = os.path.join(icons_dir, svg_name)
            if os.path.exists(svg_path):
                button.setIcon(QIcon(svg_path))
                button.setIconSize(QSize(icon_size, icon_size))
                return True
        except Exception:
            logger.debug('SVG nao aplicado no login: %s', svg_name)
        return False
    def setup_ui(self):
        self.setWindowTitle(f'TECH UNION SOLUTIONS v{VERSAO_LOCAL} - Professional Solutions')
        try:
            _avail = QApplication.primaryScreen().availableGeometry()
            _sw, _sh = _avail.width(), _avail.height()
        except Exception:
            _sw, _sh = 1366, 768
        if _sw <= 1280:
            bucket = 'xs'
        elif _sw <= 1366:
            bucket = 'sm'
        elif _sw <= 1600:
            bucket = 'md'
        elif _sw <= 1920:
            bucket = 'lg'
        else:
            bucket = 'xl'
        rs = {'xs': dict(win=(360, 460, 370, 520, 540, 660), logo=76, title=17, sub=12, field_pad_v=8, field_pad_h=12, field_fs=12, field_min_h=36, btn_pad_v=8, btn_pad_h=16, btn_fs=12, btn_min_h=34, chk_fs=11, ver_fs=11, spacing=4, margin=10, tab_pad_v=8, tab_pad_h=16, tab_min_w=72), 'sm': dict(win=(380, 500, 405, 580, 580, 700), logo=88, title=19, sub=13, field_pad_v=10, field_pad_h=12, field_fs=13, field_min_h=40, btn_pad_v=9, btn_pad_h=18, btn_fs=13, btn_min_h=38, chk_fs=11, ver_fs=12, spacing=8, margin=14, tab_pad_v=9, tab_pad_h=20, tab_min_w=80), 'md': dict(win=(410, 540, 460, 640, 660, 760), logo=110, title=21, sub=14, field_pad_v=11, field_pad_h=14, field_fs=14, field_min_h=44, btn_pad_v=10, btn_pad_h=20, btn_fs=13, btn_min_h=40, chk_fs=12, ver_fs=13, spacing=10, margin=16, tab_pad_v=10, tab_pad_h=24, tab_min_w=84), 'lg': dict(win=(430, 580, 475, 680, 720, 820), logo=130, title=22, sub=16, field_pad_v=12, field_pad_h=16, field_fs=14, field_min_h=46, btn_pad_v=10, btn_pad_h=20, btn_fs=13, btn_min_h=42, chk_fs=12, ver_fs=14, spacing=12, margin=18, tab_pad_v=11, tab_pad_h=28, tab_min_w=88), 'xl': dict(win=(450, 600, 510, 720, 760, 880), logo=160, title=24, sub=17, field_pad_v=14, field_pad_h=16, field_fs=15, field_min_h=50, btn_pad_v=11, btn_pad_h=22, btn_fs=14, btn_min_h=44, chk_fs=13, ver_fs=14, spacing=14, margin=20, tab_pad_v=12, tab_pad_h=30, tab_min_w=96)}[bucket]
        _mn_w, _mn_h, _w, _h, _mx_w, _mx_h = rs['win']
        self.setMinimumSize(min(_mn_w, _sw - 20), min(_mn_h, _sh - 30))
        self.resize(min(_w, int(_sw * 0.45)), min(_h, int(_sh * 0.82)))
        self.setMaximumSize(min(_mx_w, _sw), min(_mx_h, _sh - 40))
        try:
            _cg = QApplication.primaryScreen().availableGeometry()
            _frame = self.frameGeometry()
            _frame.moveCenter(_cg.center())
            self.move(_frame.topLeft())
        except Exception:
            pass
        central = QWidget()
        central.setObjectName('loginCentralBg')
        central.setAutoFillBackground(True)
        self.setCentralWidget(central)
        central.setStyleSheet('\n            QWidget#loginCentralBg {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #ffffff, stop:1 #f8f9fa);\n            }\n        ')
        layout = QVBoxLayout(central)
        layout.setContentsMargins(rs['margin'], rs['margin'], rs['margin'], rs['margin'])
        layout.setSpacing(rs['spacing'])
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'login.png')
        logo_pixmap = QPixmap(logo_path)
        if not logo_pixmap.isNull():
            _logo_sz = rs['logo']
            if _sh < 720:
                _logo_sz = int(_logo_sz * 0.6)
            logo_pixmap = logo_pixmap.scaled(_logo_sz, _logo_sz, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            _gif_ok = False
            try:
                from PyQt5.QtGui import QMovie
                _gif_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'login.gif')
                if os.path.isfile(_gif_path):
                    self._logo_movie = QMovie(_gif_path)
                    if self._logo_movie.isValid():
                        self._logo_movie.setScaledSize(QSize(_logo_sz, _logo_sz))
                        self._logo_static_pix = logo_pixmap
                        logo_label.setMovie(self._logo_movie)
                        _switched = [False]
                        def _gif_to_static():
                            if _switched[0]:
                                return
                            _switched[0] = True
                            try:
                                self._logo_movie.stop()
                                logo_label.setPixmap(self._logo_static_pix)
                                return
                            except Exception:
                                return
                        _fc = self._logo_movie.frameCount()
                        if _fc > 1:
                            def _on_frame(fn):
                                if fn >= _fc - 1:
                                    QTimer.singleShot(50, _gif_to_static)
                            self._logo_movie.frameChanged.connect(_on_frame)
                        QTimer.singleShot(6000, _gif_to_static)
                        self._logo_movie.start()
                        _gif_ok = True
            except Exception:
                pass
            if not _gif_ok:
                logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label)
        main_title = QLabel('TECH UNION SOLUTIONS')
        main_title.setAlignment(Qt.AlignCenter)
        main_title.setStyleSheet(f'\n            font-size: {rs['title']}px;\n            font-weight: 800;\n            color: {PRIMARY_DARK};\n            letter-spacing: 1.5px;\n            margin-top: -2px;\n        ')
        layout.addWidget(main_title)
        subtitle = QLabel('POWERED BY BRAZILIAN TECH')
        subtitle.setAlignment(Qt.AlignCenter)
        _sub_letter = 3 if bucket in ('md', 'lg', 'xl') else 2
        subtitle.setStyleSheet(f"\n            font-family: 'Consolas', 'Courier New', monospace;\n            font-size: {rs['sub']}px;\n            font-weight: 700;\n            color: {PRIMARY_DARK};\n            letter-spacing: {_sub_letter}px;\n        ")
        if _sh >= 720:
            layout.addWidget(subtitle)
        tab_widget = QTabWidget()
        tab_widget.setTabBarAutoHide(True)
        tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tab_widget.setStyleSheet(f'\n            QTabWidget {{\n                background: transparent;\n            }}\n            QTabWidget::pane {{\n                border: 1px solid {PRIMARY_DARK};\n                border-radius: 14px;\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #ffffff,\n                    stop:0.7 #FAFCFE,\n                    stop:1 {BACKGROUND});\n            }}\n            QTabBar::tab {{\n                padding: {rs['tab_pad_v']}px {rs['tab_pad_h']}px;\n                margin: 0px 3px;\n                border: 1px solid {PRIMARY_DARK};\n                border-bottom: none;\n                border-top-left-radius: 14px;\n                border-top-right-radius: 14px;\n                background: {BACKGROUND};\n                font-size: {rs['chk_fs']}px;\n                font-weight: 600;\n                letter-spacing: 1px;\n                color: {PRIMARY_DARK};\n                min-width: {rs['tab_min_w']}px;\n                text-align: center;\n            }}\n            QTabBar::tab:selected {{\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #4FC3F7,\n                    stop:0.5 {PRIMARY_LIGHT},\n                    stop:1 {PRIMARY_DARK});\n                border-bottom: 1px solid {PRIMARY_DARK};\n                color: white;\n                font-weight: 800;\n                letter-spacing: 1.2px;\n            }}\n            QTabBar::tab:!selected:hover {{\n                background: #DCE7F2;\n                color: {PRIMARY_DARK};\n            }}\n        ')
        _field_qss = f'\n            QLineEdit {{\n                padding: {rs['field_pad_v']}px {rs['field_pad_h']}px;\n                border: 2px solid {BORDER_COLOR};\n                border-radius: 10px;\n                font-size: {rs['field_fs']}px;\n                background: white;\n                color: {TEXT_PRIMARY};\n                selection-background-color: {PRIMARY_LIGHT};\n                selection-color: white;\n            }}\n            QLineEdit:hover {{\n                border-color: {PRIMARY_LIGHT};\n            }}\n            QLineEdit:focus {{\n                border-color: {ACCENT};\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #ffffff,\n                    stop:0.5 #F5F9FF,\n                    stop:1 #ffffff);\n            }}\n        '
        _checkbox_qss = f'\n            QCheckBox {{\n                color: {PRIMARY_DARK};\n                font-size: {rs['chk_fs']}px;\n                font-weight: 600;\n                letter-spacing: 1px;\n                padding: 4px;\n            }}\n            QCheckBox::indicator {{\n                width: 18px;\n                height: 18px;\n            }}\n            QCheckBox::indicator:unchecked {{\n                border: 2px solid {PRIMARY_DARK};\n                background: white;\n                border-radius: 5px;\n            }}\n            QCheckBox::indicator:checked {{\n                border: 2px solid {ACCENT};\n                background: {ACCENT};\n                border-radius: 5px;\n            }}\n        '
        def _apply_field_height(le):
            from PyQt5.QtGui import QFont
            f = QFont(le.font())
            f.setPixelSize(rs['field_fs'])
            le.setFont(f)
            fm = le.fontMetrics()
            le.setMinimumHeight(max(rs['field_min_h'], fm.height() + 2 * rs['field_pad_v'] + 4))
            le.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        license_tab = QWidget()
        license_layout = QVBoxLayout(license_tab)
        license_layout.setContentsMargins(rs['margin'], rs['margin'], rs['margin'], rs['margin'])
        license_layout.setSpacing(max(8, rs['spacing'] - 2))
        self.license_email = QLineEdit()
        self.license_email.setPlaceholderText('Email')
        self.license_email.setStyleSheet(_field_qss)
        _apply_field_height(self.license_email)
        license_layout.addWidget(self.license_email)
        self.license_key = QLineEdit()
        self.license_key.setPlaceholderText('Chave de licenca')
        self.license_key.setStyleSheet(_field_qss)
        _apply_field_height(self.license_key)
        license_layout.addWidget(self.license_key)
        self.save_license = QCheckBox('LEMBRAR LICENCA')
        self.save_license.setStyleSheet(_checkbox_qss)
        license_layout.addWidget(self.save_license)
        self.activate_btn = QPushButton('ENTRAR')
        self.activate_btn.setCursor(Qt.PointingHandCursor)
        self.activate_btn.setMinimumHeight(rs['btn_min_h'])
        self.activate_btn.setStyleSheet(f'\n            QPushButton {{\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #5FCEFA,\n                    stop:0.45 {PRIMARY_LIGHT},\n                    stop:1 {PRIMARY_DARK});\n                color: white;\n                border: 1px solid rgba(13, 71, 161, 0.55);\n                border-top: 1px solid rgba(255, 255, 255, 0.35);\n                padding: {rs['btn_pad_v']}px {rs['btn_pad_h']}px;\n                border-radius: 10px;\n                font-size: {rs['btn_fs']}px;\n                font-weight: 800;\n                letter-spacing: 2px;\n                min-width: 120px;\n            }}\n            QPushButton:hover {{\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #6FD4FB,\n                    stop:0.45 #29B6F6,\n                    stop:1 #1976D2);\n                border-color: rgba(13, 71, 161, 0.75);\n                border-top-color: rgba(255, 255, 255, 0.45);\n            }}\n            QPushButton:pressed {{\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 {PRIMARY_DARK},\n                    stop:1 #1565C0);\n                border-color: rgba(13, 71, 161, 0.95);\n                border-top-color: rgba(255, 255, 255, 0.20);\n                padding-top: {rs['btn_pad_v'] + 1}px;\n            }}\n            QPushButton:focus {{\n                outline: none;\n                border: 1px solid #4FC3F7;\n                border-top: 1px solid rgba(255, 255, 255, 0.45);\n            }}\n        ')
        self.activate_btn.clicked.connect(self.handle_license_activation)
        license_layout.addWidget(self.activate_btn)
        try:
            self._btn_anim = QVariantAnimation(self, startValue=0.0001, endValue=0.9999, duration=280)
            self._btn_anim.setEasingCurve(QEasingCurve.InOutQuad)
            _btn_base_qss = f'color: white; border: 1px solid rgba(13,71,161,0.55);border-top: 1px solid rgba(255,255,255,0.35);padding: {rs['btn_pad_v']}px {rs['btn_pad_h']}px;border-radius: 10px; font-size: {rs['btn_fs']}px;font-weight: 800; letter-spacing: 2px; min-width: 120px;'
            _c1 = QColor('#5FCEFA')
            _c2 = QColor('#1976D2')
            def _on_btn_anim_value(val):
                grad = f'background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 {_c1.name()}, stop:{val:.4f} {_c2.name()}, stop:1.0 {_c1.name()});'
                self.activate_btn.setStyleSheet(f'QPushButton {{ {_btn_base_qss} {grad} }}')
            self._btn_anim.valueChanged.connect(_on_btn_anim_value)
            self.activate_btn.installEventFilter(self)
            self._btn_anim_active = True
        except Exception:
            self._btn_anim_active = False
        try:
            self._pulse_effect = QGraphicsOpacityEffect(self.activate_btn)
            self._pulse_effect.setOpacity(1.0)
            self.activate_btn.setGraphicsEffect(self._pulse_effect)
            self._pulse_anim = QPropertyAnimation(self._pulse_effect, b'opacity')
            self._pulse_anim.setDuration(900)
            self._pulse_anim.setStartValue(1.0)
            self._pulse_anim.setEndValue(0.55)
            self._pulse_anim.setEasingCurve(QEasingCurve.InOutQuad)
            self._pulse_anim.setLoopCount(-1)
            self._pulse_timer = QTimer(self)
            self._pulse_timer.setSingleShot(True)
            self._pulse_timer.setInterval(5000)
            self._pulse_timer.timeout.connect(self._pulse_anim.start)
            self._pulse_timer.start()
            self._pulse_active = True
        except Exception:
            self._pulse_active = False
        license_layout.addStretch(1)
        admin_tab = QWidget()
        admin_layout = QVBoxLayout(admin_tab)
        admin_layout.setContentsMargins(rs['margin'], rs['margin'], rs['margin'], rs['margin'])
        admin_layout.setSpacing(max(8, rs['spacing'] - 2))
        self.username = QLineEdit()
        self.username.setPlaceholderText('Usuario')
        self.username.setStyleSheet(_field_qss)
        _apply_field_height(self.username)
        admin_layout.addWidget(self.username)
        self.password = QLineEdit()
        self.password.setPlaceholderText('Senha')
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setStyleSheet(_field_qss)
        _apply_field_height(self.password)
        admin_layout.addWidget(self.password)
        self.show_password = QCheckBox('MOSTRAR SENHA')
        self.show_password.setStyleSheet(_checkbox_qss)
        self.show_password.stateChanged.connect(self.toggle_password_visibility)
        admin_layout.addWidget(self.show_password)
        self.login_btn = QPushButton('LOGIN ADMIN')
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setMinimumHeight(rs['btn_min_h'])
        self.login_btn.setStyleSheet(f'\n            QPushButton {{\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #4FC3F7,\n                    stop:0.5 {ACCENT},\n                    stop:1 #1565C0);\n                color: white;\n                border: 1px solid rgba(13, 71, 161, 0.45);\n                padding: {rs['btn_pad_v']}px {rs['btn_pad_h']}px;\n                border-radius: 10px;\n                font-size: {rs['btn_fs']}px;\n                font-weight: 800;\n                letter-spacing: 1.8px;\n                min-width: 120px;\n            }}\n            QPushButton:hover {{\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #80D8FF,\n                    stop:0.5 #4FC3F7,\n                    stop:1 {PRIMARY_LIGHT});\n                border-color: rgba(13, 71, 161, 0.65);\n            }}\n            QPushButton:pressed {{\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 {PRIMARY_DARK},\n                    stop:1 #1565C0);\n                border-color: rgba(13, 71, 161, 0.85);\n            }}\n            QPushButton:focus {{\n                outline: none;\n                border: 1px solid #4FC3F7;\n            }}\n        ')
        self.login_btn.clicked.connect(self.handle_admin_login)
        admin_layout.addWidget(self.login_btn)
        self.clear_cache_btn = QPushButton('LIMPAR CACHE')
        self.clear_cache_btn.setCursor(Qt.PointingHandCursor)
        self.clear_cache_btn.setMinimumHeight(rs['btn_min_h'])
        self.clear_cache_btn.setStyleSheet(f'\n            QPushButton {{\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #FF5252,\n                    stop:0.5 #F44336,\n                    stop:1 #C62828);\n                color: white;\n                border: 1px solid rgba(183, 28, 28, 0.45);\n                padding: {rs['btn_pad_v']}px {rs['btn_pad_h']}px;\n                border-radius: 10px;\n                font-size: {rs['btn_fs']}px;\n                font-weight: 800;\n                letter-spacing: 1.8px;\n                min-width: 120px;\n            }}\n            QPushButton:hover {{\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #FF7676,\n                    stop:0.5 #FF5252,\n                    stop:1 #D32F2F);\n                border-color: rgba(183, 28, 28, 0.65);\n            }}\n            QPushButton:pressed {{\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #B71C1C,\n                    stop:1 #D32F2F);\n                border-color: rgba(183, 28, 28, 0.85);\n            }}\n            QPushButton:focus {{\n                outline: none;\n                border: 1px solid #FF7676;\n            }}\n        ')
        self._apply_svg_icon(self.clear_cache_btn, 'trash.svg', 16)
        self.clear_cache_btn.clicked.connect(self.clear_all_cache)
        admin_layout.addWidget(self.clear_cache_btn)
        admin_layout.addStretch(1)
        tab_widget.addTab(license_tab, 'LICEN├çA')
        layout.addStretch(1)
        layout.addWidget(tab_widget)
        layout.addStretch(3)
        self._tab_widget = tab_widget
        self._admin_tab_widget = admin_tab
        self._admin_tab_visible = False
        version = QLabel(f'v{VERSAO_LOCAL}')
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet(f'\n            color: rgba(13, 71, 161, 140);\n            font-size: {max(10, rs['ver_fs'] - 1)}px;\n            font-weight: 500;\n            margin-top: 6px;\n            letter-spacing: 0.8px;\n        ')
        layout.addWidget(version)
        footer_row = QHBoxLayout()
        footer_row.setContentsMargins(0, 4, 0, 0)
        footer_row.setSpacing(6)
        _link_btn_qss = f'\n            QPushButton {{\n                background: transparent;\n                color: {TEXT_SECONDARY};\n                border: 1px solid {BORDER_COLOR};\n                border-radius: 8px;\n                font-size: 10px;\n                font-weight: 600;\n                letter-spacing: 1px;\n                padding: 3px 9px;\n            }}\n            QPushButton:hover {{\n                color: {PRIMARY_DARK};\n                border-color: {PRIMARY_DARK};\n                background: rgba(13, 71, 161, 0.04);\n            }}\n            QPushButton:pressed {{\n                background: rgba(13, 71, 161, 0.10);\n                color: {PRIMARY_DARK};\n            }}\n        '
        self.footer_clear_btn = QPushButton()
        self.footer_clear_btn.setCursor(Qt.PointingHandCursor)
        self.footer_clear_btn.setToolTip('Limpar cache local')
        self.footer_clear_btn.setFixedSize(32, 22)
        self.footer_clear_btn.setStyleSheet(_link_btn_qss)
        if not self._apply_svg_icon(self.footer_clear_btn, 'trash.svg', 14):
            self.footer_clear_btn.setText('CACHE')
            self.footer_clear_btn.setFixedSize(56, 22)
        self.footer_clear_btn.clicked.connect(self.clear_all_cache)
        footer_row.addWidget(self.footer_clear_btn)
        footer_row.addStretch(1)
        self.footer_vpn_btn = QPushButton('VPN')
        self.footer_vpn_btn.setCursor(Qt.PointingHandCursor)
        self.footer_vpn_btn.setToolTip('Abrir teste de VPN da Cloudflare (one.one.one.one) no navegador')
        self.footer_vpn_btn.setFixedSize(56, 22)
        self.footer_vpn_btn.setStyleSheet(_link_btn_qss)
        self.footer_vpn_btn.clicked.connect(self._open_vpn_link)
        footer_row.addWidget(self.footer_vpn_btn)
        layout.addLayout(footer_row)
        shortcut = QShortcut(QKeySequence('Return'), self)
        shortcut.activated.connect(self.handle_current_tab)
        self._admin_shortcut_primary = QShortcut(QKeySequence('Ctrl+Shift+3'), self)
        self._admin_shortcut_primary.activated.connect(self._reveal_admin_tab)
        self._admin_shortcut_reserve = QShortcut(QKeySequence('Ctrl+Alt+Shift+A'), self)
        self._admin_shortcut_reserve.activated.connect(self._reveal_admin_tab)
        self._admin_shortcut_legacy = QShortcut(QKeySequence('Ctrl+Shift+F3'), self)
        self._admin_shortcut_legacy.activated.connect(self._reveal_admin_tab)
    def handle_current_tab(self):
        tab_widget = getattr(self, '_tab_widget', None) or self.findChild(QTabWidget)
        if tab_widget is None:
            return
        current_widget = tab_widget.currentWidget()
        admin_widget = getattr(self, '_admin_tab_widget', None)
        if admin_widget is not None and current_widget is admin_widget:
            self.handle_admin_login()
            return
        self.handle_license_activation()
    def _reveal_admin_tab(self):
        admin_widget = getattr(self, '_admin_tab_widget', None)
        tab_widget = getattr(self, '_tab_widget', None)
        if admin_widget is None or tab_widget is None:
            return
        if not getattr(self, '_admin_tab_visible', False):
            idx = tab_widget.addTab(admin_widget, 'ADMIN')
            self._admin_tab_visible = True
        else:
            idx = tab_widget.indexOf(admin_widget)
        if idx >= 0:
            tab_widget.setCurrentIndex(idx)
            if hasattr(self, 'username'):
                if self.username is not None:
                    self.username.setFocus()
    def _open_vpn_link(self):
        try:
            from PyQt5.QtGui import QDesktopServices
            from PyQt5.QtCore import QUrl
            QDesktopServices.openUrl(QUrl('https://one.one.one.one'))
            return
        except Exception as exc:
            logger.error('Falha ao abrir VPN link: %s', type(exc).__name__)
            QMessageBox.information(self, 'VPN', 'Acesse: https://one.one.one.one no seu navegador.')
    def load_saved_license(self):
        settings = QSettings('UNION TECHNICAL', 'License')
        saved_email = settings.value('email', '')
        saved_license = settings.value('license', '')
        if saved_email:
            if saved_license:
                self.license_email.setText(saved_email)
                self.license_key.setText(saved_license)
                self.save_license.setChecked(True)
    def save_license_data(self, email, license_key):
        settings = QSettings('UNION TECHNICAL', 'License')
        if self.save_license.isChecked():
            settings.setValue('email', email)
            settings.setValue('license', license_key)
            return
        settings.remove('email')
        settings.remove('license')
    def handle_admin_login(self):
        username = self.username.text()
        password = self.password.text()
        if not username or not password:
            QMessageBox.warning(self, 'Aviso', 'Preencha todos os campos!')
            return
        try:
            logger.info('­ƒöì [ADMIN] Iniciando verifica├º├úo de vers├úo do sistema...')
            if not self.verificar_versao_sistema():
                logger.info('ÔØî [ADMIN] Verifica├º├úo de vers├úo bloqueou o acesso')
                return
            logger.info('Ô£à [ADMIN] Verifica├º├úo de vers├úo OK - prosseguindo com login admin')
            success, user_type = self.user_db.verify_login(username, password)
            if success and user_type == 'admin':
                self.hide()
                user_id = self.user_db.get_user_id(username)
                from app.views.main_window import MainWindow
                self.main_window = MainWindow(user_id, is_admin=True, fullscreen=True)
                self.main_window.show()
                self.admin_panel = PainelAdministrativo()
                self.admin_panel.show()
                return
            QMessageBox.warning(self, 'Erro', 'Acesso negado! Apenas administradores podem fazer login nesta aba.')
            return
        except Exception as e:
            logger.error(f'Erro no login admin: {str(e)}')
            QMessageBox.critical(self, 'Erro', 'Erro interno no sistema. Tente novamente.')
    def toggle_password_visibility(self, state):
        if state:
            self.password.setEchoMode(QLineEdit.Normal)
            return
        self.password.setEchoMode(QLineEdit.Password)
    def refresh_interface(self):
        self.setWindowTitle(f'TECH UNION SOLUTIONS v{VERSAO_LOCAL} - Professional Solutions')
        self.license_email.setPlaceholderText('Email / E-mail / Correo electronico TECH UNION SOLUTIONS')
        self.license_key.setPlaceholderText('License Key / Chave de Licenca / Clave de Licencia')
        self.username.setPlaceholderText('Username / Usuario / Usuario')
        self.password.setPlaceholderText('Password / Senha / Contrasena')
        self.save_license.setText('LEMBRAR LICENCA')
        self.show_password.setText('MOSTRAR SENHA')
        self.activate_btn.setText('ENTRAR')
        self.login_btn.setText('LOGIN ADMIN')
    def load_saved_username(self):
        settings = QSettings('TECHNICIANS UNION', 'Login')
        saved_username = settings.value('username', '')
        if saved_username:
            self.username.setText(saved_username)
            self.remember_me.setChecked(True)
        saved_password = settings.value('password', '')
        if saved_password:
            self.password.setText(saved_password)
            self.save_password.setChecked(True)
    def save_credentials(self, username, password):
        settings = QSettings('TECHNICIANS UNION', 'Login')
        if self.remember_me.isChecked():
            settings.setValue('username', username)
        else:
            settings.remove('username')
        if self.save_password.isChecked():
            settings.setValue('password', password)
            return
        settings.remove('password')
    def handle_login(self):
        username = self.username.text()
        password = self.password.text()
        if not username or not password:
            QMessageBox.warning(self, 'Aviso', 'Preencha todos os campos!')
            return
        try:
            success, user_type = self.user_db.verify_login(username, password)
            if success:
                self.save_credentials(username, password)
                self.hide()
                user_id = self.user_db.get_user_id(username)
                if user_type == 'admin':
                    from app.views.main_window import MainWindow
                    self.main_window = MainWindow(user_id, is_admin=True, fullscreen=True)
                    self.main_window.show()
                    self.admin_panel = PainelAdministrativo()
                    self.admin_panel.show()
                    return
                from app.views.main_window import MainWindow
                self.main_window = MainWindow(user_id, is_admin=False, fullscreen=True)
                self.main_window.show()
                return
            QMessageBox.warning(self, 'Erro', 'Usu├írio ou senha inv├ílidos!')
            return
        except Exception as e:
            logger.error(f'Erro no login: {str(e)}')
            QMessageBox.critical(self, 'Erro', 'Erro interno no sistema. Tente novamente.')
    def clear_all_cache(self):
        try:
            cache = ValidationCache()
            cache_dir = cache.cache_dir
            if cache_dir.exists():
                for file in cache_dir.glob('validation_*.enc'):
                    pass
            try:
                file.unlink()
            except Exception as e:
                logger.error(f'Erro ao remover arquivo de cache {file}: {str(e)}')
            else:
                QMessageBox.information(self, 'Sucesso', 'Cache limpo com sucesso!')
                return
        except Exception as e:
            logger.error(f'Erro ao limpar cache: {str(e)}')
            QMessageBox.warning(self, 'Erro', 'Erro ao limpar cache. Tente novamente.')
    def force_cache_cleanup(self):
        try:
            logger.info('Iniciando limpeza for├ºada do cache devido ├á mudan├ºa no formato do fingerprint')
            self.clear_all_cache()
            migration_file = Path(os.getenv('LOCALAPPDATA')) / 'TechniciansUnion' / '.fp_migration_v2'
            migration_file.parent.mkdir(parents=True, exist_ok=True)
            migration_file.touch()
            logger.info('Limpeza de cache conclu├¡da com sucesso')
            return
        except Exception as e:
            logger.error(f'Erro ao limpar cache durante migra├º├úo: {str(e)}')
    def _migrate_fingerprint_v3(self):
        try:
            logger.info('Migra├º├úo v3: fingerprint estabilizado (somente MachineGuid)')
            self.validation_cache.clear_all_cache_robust(silent=True)
            migration_file = Path(os.getenv('LOCALAPPDATA')) / 'TechniciansUnion' / '.fp_migration_v3'
            migration_file.parent.mkdir(parents=True, exist_ok=True)
            migration_file.touch()
            logger.info('Migra├º├úo v3 conclu├¡da com sucesso')
            return
        except Exception as e:
            logger.error(f'Erro na migra├º├úo v3: {str(e)}')
    def _migrate_fingerprint_v4(self):
        try:
            logger.info('Migra├º├úo v4: fingerprint anti-colis├úo (MachineGuid + VolumeSerial)')
            self.validation_cache.clear_all_cache_robust(silent=True)
            migration_file = Path(os.getenv('LOCALAPPDATA')) / 'TechniciansUnion' / '.fp_migration_v4'
            migration_file.parent.mkdir(parents=True, exist_ok=True)
            migration_file.touch()
            logger.info('Migra├º├úo v4 conclu├¡da com sucesso')
            return
        except Exception as e:
            logger.error(f'Erro na migra├º├úo v4: {str(e)}')
    def _migrate_cache_v5(self):
        try:
            self.validation_cache.clear_all_cache_robust(silent=True)
            migration_file = Path(os.getenv('LOCALAPPDATA')) / 'TechniciansUnion' / '.fp_migration_v5'
            migration_file.parent.mkdir(parents=True, exist_ok=True)
            migration_file.touch()
            return
        except Exception:
            return
    def show_maintenance_window(self, mensagem_manutencao):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle('­ƒöº Sistema em Manuten├º├úo')
        html_content = f'\n        <div style="text-align: center; font-family: Arial;">\n            <h2 style="color: #e67e22; margin-bottom: 20px;">\n                ­ƒöº Sistema Temporariamente Indispon├¡vel\n            </h2>\n            \n            <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin: 10px 0;">\n                <p style="font-size: 14px; color: #856404; margin: 5px 0;">\n                    <strong>O que est├í acontecendo?</strong><br>\n                    Estamos realizando manuten├º├Áes para melhorar sua experi├¬ncia.\n                </p>\n            </div>\n            \n            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">\n                <p style="font-size: 14px; color: #495057;">\n                    <strong>­ƒôó Mensagem do Sistema:</strong><br>\n                    <em>"{mensagem_manutencao}"</em>\n                </p>\n            </div>\n            \n            <div style="background-color: #d1ecf1; padding: 15px; border-radius: 8px; margin: 10px 0;">\n                <p style="font-size: 13px; color: #0c5460;">\n                    <strong>­ƒÆí O que fazer agora?</strong><br>\n                    ÔÇó Aguarde alguns minutos e tente novamente<br>\n                    ÔÇó As manuten├º├Áes geralmente s├úo r├ípidas<br>\n                    ÔÇó Seus dados est├úo seguros e n├úo ser├úo perdidos\n                </p>\n            </div>\n            \n            <p style="font-size: 12px; color: #6c757d; margin-top: 20px;">\n                <strong>­ƒòÆ Tempo estimado:</strong> Geralmente entre 5 a 30 minutos<br>\n                <strong>­ƒô× Suporte:</strong> WhatsApp +55 85 9412-9977 ou +55 85 99750-7465\n            </p>\n        </div>\n        '
        msg.setText(html_content)
        msg.setTextFormat(Qt.RichText)
        retry_btn = msg.addButton('­ƒöä Tentar Novamente', QMessageBox.ActionRole)
        close_btn = msg.addButton('ÔØî Fechar', QMessageBox.RejectRole)
        msg.exec_()
        clicked_button = msg.clickedButton()
        if clicked_button == retry_btn:
            QTimer.singleShot(1000, self.verificar_versao_sistema)
            return
        self.close()
    def show_update_window(self, mensagem_aviso, link_download, versao_atual):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle('Atualiza├º├úo Necess├íria')
        bloco_mensagem = ''
        if mensagem_aviso:
            bloco_mensagem = f'\n                <tr><td colspan="2" style="padding-top:10px;">\n                    <div style="background-color:#FFF8E1; padding:12px;">\n                        <span style="color:#8D6E00; font-size:13px;">{mensagem_aviso}</span>\n                    </div>\n                </td></tr>'
        html_content = f'\n        <div style="font-family:\'Segoe UI\', Arial, sans-serif; min-width:360px;">\n            <h2 style="color:#0D47A1; margin:0 0 4px 0; font-size:19px;">\n                Atualiza├º├úo dispon├¡vel\n            </h2>\n            <p style="color:#607D8B; font-size:13px; margin:0 0 16px 0;">\n                Uma nova vers├úo do UNION est├í pronta para instala├º├úo.\n            </p>\n\n            <table width="100%" cellpadding="10" cellspacing="0">\n                <tr>\n                    <td style="background-color:#ECEFF1; color:#607D8B; font-size:13px;">Sua vers├úo</td>\n                    <td align="right" style="background-color:#ECEFF1; color:#455A64; font-size:13px;"><b>{VERSAO_LOCAL}</b></td>\n                </tr>\n                <tr>\n                    <td style="background-color:#E3F2FD; color:#0D47A1; font-size:13px;">Nova vers├úo</td>\n                    <td align="right" style="background-color:#E3F2FD; color:#0D47A1; font-size:13px;"><b>{versao_atual}</b></td>\n                </tr>\n                {bloco_mensagem}\n            </table>\n\n            <p style="color:#90A4AE; font-size:12px; margin:16px 0 0 0;">\n                Suporte: WhatsApp +55 85 9412-9977 ou +55 85 99750-7465\n            </p>\n        </div>\n        '
        msg.setText(html_content)
        msg.setTextFormat(Qt.RichText)
        auto_btn = msg.addButton('Atualizar Automaticamente', QMessageBox.AcceptRole)
        download_btn = None
        if link_download:
            download_btn = msg.addButton('Baixar pelo Navegador', QMessageBox.ActionRole)
        retry_btn = msg.addButton('Verificar Novamente', QMessageBox.ActionRole)
        close_btn = msg.addButton('Fechar', QMessageBox.RejectRole)
        msg.exec_()
        clicked_button = msg.clickedButton()
        if clicked_button == auto_btn:
            self._iniciar_auto_update(link_download)
            return
        if download_btn is not None and clicked_button == download_btn:
            self._abrir_download_manual(link_download)
            return
        if clicked_button == retry_btn:
            QTimer.singleShot(1000, self.verificar_versao_sistema)
            return
        self.close()
    def _iniciar_auto_update(self, link_download):
        try:
            from app.views.components._upd_dialog import _UpdDialog, lancar
            dlg = _UpdDialog(self)
            self._upd_dlg = dlg
            dlg.exec_()
            if dlg.sucesso and dlg.caminho_instalador:
                if lancar(dlg.caminho_instalador):
                    logger.info('upd: instalador iniciado, encerrando app')
                    self.close()
                    QApplication.quit()
                    return
                logger.warning('upd: falha ao iniciar instalador ÔÇö fallback')
            else:
                logger.info('upd: aquisi├º├úo/valida├º├úo falhou ÔÇö fallback')
            self._abrir_download_manual(link_download)
            return
        except Exception as e:
            logger.error('upd: erro inesperado, acionando fallback (%s)', type(e).__name__)
            self._abrir_download_manual(link_download)
    def _abrir_download_manual(self, link_download):
        if link_download:
            import webbrowser
            try:
                webbrowser.open(link_download)
                QMessageBox.information(self, 'Download Iniciado', 'O download foi iniciado em seu navegador.\n\nPr├│ximos passos:\n1. Aguarde o download terminar\n2. Execute o arquivo baixado\n3. Siga as instru├º├Áes de instala├º├úo\n4. Reinicie o UNION\n\nAp├│s a instala├º├úo, o programa abrir├í com a nova vers├úo.')
            except Exception:
                QMessageBox.warning(self, 'Atualiza├º├úo', 'N├úo foi poss├¡vel iniciar o download automaticamente.\n\nEntre em contato com o suporte para obter a nova vers├úo.')
        else:
            QMessageBox.warning(self, 'Atualiza├º├úo', 'N├úo foi poss├¡vel concluir a atualiza├º├úo autom├ítica.\n\nEntre em contato com o suporte para obter a nova vers├úo.')
        self.close()
    def show_version_error(self, title, message):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setTextFormat(Qt.RichText)
        retry_btn = msg.addButton('­ƒöä Tentar Novamente', QMessageBox.ActionRole)
        close_btn = msg.addButton('ÔØî Fechar', QMessageBox.RejectRole)
        msg.exec_()
        clicked_button = msg.clickedButton()
        if clicked_button == retry_btn:
            QTimer.singleShot(1000, self.verificar_versao_sistema)
            return
        self.close()
# WARNING: Decompyle incomplete
