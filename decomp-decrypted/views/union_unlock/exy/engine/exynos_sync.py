import base64
import hashlib
import json
import os
import platform
import sqlite3
import threading
import uuid
import zlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import (Dict, List, Optional)
try:
    import pymysql
    _CONEXAO_DISPONIVEL = True
except ImportError:
    _CONEXAO_DISPONIVEL = False
from app.utils._app_cfg import db_config as _get_db_config
_CONFIG_CONEXAO = _get_db_config(connect_timeout=10, read_timeout=30)
try:
    from app.utils._cfg_probe import _is_dev_env as _probe_is_dev
    _DEV_MODE = bool(_probe_is_dev())
except Exception:
    _DEV_MODE = False
def _status_filter():
    if _DEV_MODE:
        return ('ativo', 'desenvolvimento')
    return ('ativo',)
def _status_placeholders(values):
    return ', '.join(['%s'] * len(values))
def _log(msg: str):
    print(f'[EXYNOS_SYNC] {msg}', flush=True)
def _resolve_db_path() -> Path:
    try:
        from app.utils.path_manager import PathManager
        exy_dir = PathManager.get_exy_dir()
        if exy_dir:
            p = os.path.join(exy_dir, 'exy.db')
            parent = os.path.dirname(p)
            if not os.path.isdir(parent):
                os.makedirs(parent, exist_ok=True)
            return Path(p)
    except Exception:
        pass
    return Path(__file__).parent / 'exy.db'
_DB_PATH = _resolve_db_path()
def _get_machine_key() -> bytes:
    machine_info = f'{platform.node()}-{uuid.getnode()}-UNION2026'
    return hashlib.sha256(machine_info.encode()).digest()
def _xor_encrypt(data: bytes, key: bytes) -> bytes:
    key_cycle = (key * (len(data) // len(key) + 1))[:len(data)]
    return bytes((a ^ b for a, b in zip(data, key_cycle)))
def _encrypt_data(data: bytes) -> bytes:
    try:
        compressed = zlib.compress(data, level=9)
        encrypted = _xor_encrypt(compressed, _get_machine_key())
        return base64.b64encode(encrypted)
    except Exception:
        return data
def _decrypt_data(data: bytes) -> bytes:
    try:
        decoded = base64.b64decode(data)
        decrypted = _xor_encrypt(decoded, _get_machine_key())
        return zlib.decompress(decrypted)
    except Exception:
        return data
class ExynosSync:
    SYNC_HORAS = 24
    DEBOUNCE_MIN = 30
    def __init__(self, db_path: Path=None):
        self.db_path = str(db_path or _DB_PATH)
        self._lock = threading.RLock()
        self._init_db()
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("\n            CREATE TABLE IF NOT EXISTS presets (\n                srv_id         INTEGER PRIMARY KEY,\n                chipset_key    TEXT NOT NULL UNIQUE,\n                chipset_nome   TEXT,\n                dispositivos   TEXT,\n                modelos_sm     TEXT,\n                metodo         TEXT DEFAULT 'extract',\n                preset_enc     BLOB,\n                ramdisk_tipo   TEXT DEFAULT 'padrao',\n                tem_overlay    INTEGER DEFAULT 0,\n                observacoes    TEXT,\n                status         TEXT DEFAULT 'ativo',\n                sync_em        TEXT\n            )\n        ")
        c.execute('\n            CREATE TABLE IF NOT EXISTS info_sistema (\n                id                     INTEGER PRIMARY KEY,\n                ultima_atualizacao     TEXT,\n                ultima_tentativa_sync  TEXT,\n                total_presets          INTEGER DEFAULT 0\n            )\n        ')
        c.execute('CREATE INDEX IF NOT EXISTS idx_exy_chipset ON presets(chipset_key)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_exy_metodo ON presets(metodo)')
        conn.commit()
        conn.close()
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    def _get_info(self) -> Dict:
        conn = self._get_conn()
        try:
            row = conn.execute('SELECT * FROM info_sistema WHERE id=1').fetchone()
            conn.close()
            if row:
                return dict(row)
            return {}
        except sqlite3.OperationalError:
            conn.close()
            self._init_db()
            return {}
    def _tem_presets_locais(self) -> bool:
        conn = self._get_conn()
        try:
            row = conn.execute('SELECT COUNT(*) as c FROM presets').fetchone()
            conn.close()
            return row['c'] > 0
        except sqlite3.OperationalError:
            conn.close()
            self._init_db()
            return False
    def pode_sincronizar(self) -> bool:
        if not self._tem_presets_locais():
            return True
        info = self._get_info()
        ult_sync = info.get('ultima_atualizacao')
        if not ult_sync:
            return True
        try:
            delta_sync = datetime.now() - datetime.fromisoformat(ult_sync)
            if delta_sync < timedelta(hours=self.SYNC_HORAS):
                return False
        except (TypeError, ValueError):
            return True
        ult_tentativa = info.get('ultima_tentativa_sync')
        if not ult_tentativa:
            return True
        try:
            delta_tent = datetime.now() - datetime.fromisoformat(ult_tentativa)
        except (TypeError, ValueError):
            return True
        return delta_tent >= timedelta(minutes=self.DEBOUNCE_MIN)
    def _registrar_tentativa(self):
        conn = self._get_conn()
        try:
            conn.execute('INSERT OR IGNORE INTO info_sistema (id, ultima_atualizacao, total_presets) VALUES (1, NULL, 0)')
            conn.execute('UPDATE info_sistema SET ultima_tentativa_sync = ? WHERE id = 1', (datetime.now().isoformat(),))
            conn.commit()
        except sqlite3.OperationalError:
            conn.close()
            self._init_db()
            conn = self._get_conn()
            conn.execute('INSERT OR IGNORE INTO info_sistema (id, ultima_atualizacao, total_presets) VALUES (1, NULL, 0)')
            conn.execute('UPDATE info_sistema SET ultima_tentativa_sync = ? WHERE id = 1', (datetime.now().isoformat(),))
            conn.commit()
        conn.close()
    def sincronizar(self) -> bool:
        if not _CONEXAO_DISPONIVEL:
            _log('Driver de conexao indisponivel ÔÇö sync cancelado')
            return False
        self._registrar_tentativa()
        _log('Conectando ao servidor...')
        conn_mysql = None
        try:
            conn_mysql = pymysql.connect(**_CONFIG_CONEXAO, **{'cursorclass': pymysql.cursors.DictCursor})
            cursor_mysql = conn_mysql.cursor()
            _sf = _status_filter()
            _ph = _status_placeholders(_sf)
            cursor_mysql.execute(f"\n                SELECT id, chipset_key, chipset_nome, dispositivos,\n                       modelos_sm, metodo, preset_json, ramdisk_tipo,\n                       tem_overlay, observacoes, status\n                FROM exynos_presets\n                WHERE status IN ({_ph})\n                  AND (engine_type = 'eng1' OR engine_type IS NULL)\n                ORDER BY chipset_key\n            ", _sf)
            rows = cursor_mysql.fetchall()
            conn_mysql.close()
            conn_mysql = None
            _log(f'Servidor retornou {len(rows)} presets')
            with self._lock:
                conn = self._get_conn()
                ids_servidor = set()
                for row in rows:
                    ids_servidor.add(row['id'])
                    preset_raw = row.get('preset_json') or '{}'
                    if isinstance(preset_raw, dict):
                        preset_raw = json.dumps(preset_raw, ensure_ascii=False)
                    preset_enc = _encrypt_data(preset_raw.encode('utf-8')) if preset_raw else None
                    conn.execute('\n                        INSERT OR REPLACE INTO presets\n                            (srv_id, chipset_key, chipset_nome, dispositivos,\n                             modelos_sm, metodo, preset_enc, ramdisk_tipo,\n                             tem_overlay, observacoes, status, sync_em)\n                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)\n                    ', (row['id'], row['chipset_key'], row.get('chipset_nome') or '', row.get('dispositivos') or '', row.get('modelos_sm') or '', row.get('metodo') or 'extract', preset_enc, row.get('ramdisk_tipo') or 'padrao', 1 if row.get('tem_overlay') else 0, row.get('observacoes') or '', row.get('status') or 'ativo', datetime.now().isoformat()))
                    continue
                ids_locais = {r['srv_id'] for r in conn.execute('SELECT srv_id FROM presets').fetchall()}
                ids_orfaos = ids_locais - ids_servidor
                if ids_orfaos:
                    ph = ','.join(('?' for _ in ids_orfaos))
                    conn.execute(f'DELETE FROM presets WHERE srv_id IN ({ph})', list(ids_orfaos))
                    _log(f'Removidos {len(ids_orfaos)} preset(s) orfao(s)')
                conn.execute('INSERT OR IGNORE INTO info_sistema (id, ultima_atualizacao, total_presets) VALUES (1, NULL, 0)')
                conn.execute('UPDATE info_sistema SET ultima_atualizacao = ?, total_presets = ? WHERE id = 1', (datetime.now().isoformat(), len(rows)))
                conn.commit()
                conn.close()
            _log(f'Sincronizacao concluida ÔÇö {len(rows)} presets no cache')
        except Exception as exc:
            _log(f'ERRO na sincronizacao ÔÇö {exc}')
        if conn_mysql is not None:
            try:
                conn_mysql.close()
            except Exception:
                pass
            return True
        return True
    def listar_chipsets(self) -> List[Dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute("\n                SELECT srv_id, chipset_key, chipset_nome, dispositivos,\n                       modelos_sm, metodo, ramdisk_tipo, tem_overlay, status\n                FROM presets\n                WHERE status = 'ativo'\n                ORDER BY chipset_key\n            ").fetchall()
        except Exception:
            conn.close()
            return []
        conn.close()
        return [dict(r) for r in rows]
    def obter_preset_json(self, chipset_key: str) -> Optional[Dict]:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT preset_enc FROM presets WHERE chipset_key = ? AND status = 'ativo'", (chipset_key,)).fetchone()
        except Exception:
            pass
        conn.close()
        if not row or not row['preset_enc']:
            return
        try:
            raw = _decrypt_data(bytes(row['preset_enc'])).decode('utf-8')
        except Exception as exc:
            _log(f'Erro ao descriptografar preset {chipset_key}: {exc}')
        return json.loads(raw)
    def obter_preset_completo(self, chipset_key: str) -> Optional[Dict]:
        conn = self._get_conn()
        try:
            row = conn.execute('\n                SELECT srv_id, chipset_key, chipset_nome, dispositivos,\n                       modelos_sm, metodo, preset_enc, ramdisk_tipo,\n                       tem_overlay, observacoes, status\n                FROM presets WHERE chipset_key = ?\n            ', (chipset_key,)).fetchone()
        except Exception:
            pass
        conn.close()
        if not row:
            return
        result = dict(row)
        if row['preset_enc']:
            try:
                raw = _decrypt_data(bytes(row['preset_enc'])).decode('utf-8')
                result['preset_json'] = json.loads(raw)
            except Exception:
                result['preset_json'] = {}
        else:
            result['preset_json'] = {}
        del result['preset_enc']
        return result
    def total_presets(self) -> int:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT COUNT(*) as c FROM presets WHERE status='ativo'").fetchone()
        except Exception:
            conn.close()
            return 0
        conn.close()
        if row:
            return row['c']
        return 0
    def forcar_sync(self) -> bool:
        conn = self._get_conn()
        conn.execute('UPDATE info_sistema SET ultima_atualizacao = NULL, ultima_tentativa_sync = NULL WHERE id = 1')
        conn.commit()
        conn.close()
        return self.sincronizar()
_instancia: Optional[ExynosSync] = None
_instancia_lock = threading.Lock()
def get_sync() -> ExynosSync:
    global _instancia
    if _instancia is None:
        with _instancia_lock:
            if _instancia is None:
                _instancia = ExynosSync()
        return _instancia
    return _instancia
