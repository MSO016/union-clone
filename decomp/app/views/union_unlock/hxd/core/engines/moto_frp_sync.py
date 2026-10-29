'''
Sync de LKs FRP Motorola: MySQL ÔåÆ SQLite local criptografado.
Padrao identico ao EdlSync (app/database/edl_sync.py).
TECH UNION SOLUTIONS ÔÇö Julho 2026
'''
import base64
import hashlib
import json
import logging
import os
import platform
import sqlite3
import threading
import uuid
import zlib
from datetime import datetime, timedelta
from pathlib import Path
from app.utils._app_cfg import db_config
_logger = logging.getLogger(__name__)
try:
    import pymysql
    _MYSQL_OK = True
except ImportError:
    _MYSQL_OK = False
def _resolve_mfk_db():
    try:
        from app.utils.path_manager import PathManager
        tools = PathManager.get_unlock_tools_dir()
        if tools:
            p = os.path.normpath(os.path.join(os.path.dirname(tools), 'hxd', 'core', '_mfk_cache.db'))
            if os.path.isfile(p):
                return Path(p)
    except Exception:
        pass
    return Path(__file__).parent.parent / '_mfk_cache.db'
_DB_PATH = _resolve_mfk_db()
def _machine_key() -> bytes:
    info = f'{platform.node()}-{uuid.getnode()}-UNION2026'
    return hashlib.sha256(info.encode()).digest()
def _xor(data: bytes, key: bytes) -> bytes:
    kc = (key * (len(data) // len(key) + 1))[:len(data)]
    return bytes((a ^ b for a, b in zip(data, kc)))
def _enc(data: bytes) -> bytes:
    try:
        return base64.b64encode(_xor(zlib.compress(data, 9), _machine_key()))
    except Exception:
        return data
def _dec(data: bytes) -> bytes:
    try:
        return zlib.decompress(_xor(base64.b64decode(data), _machine_key()))
    except Exception:
        return data
class MotoFrpSync:
    SYNC_HORAS = 24
    DEBOUNCE_MIN = 30
    def __init__(self, db_path: Path=None):
        self.db_path = str(db_path or _DB_PATH)
        self._lock = threading.RLock()
        self._init_db()
    _SCHEMA_V = 4
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        precisa_recriar = False
        try:
            info = c.execute('PRAGMA table_info(modelos)').fetchall()
        except Exception:
            pass
        try:
            cols = {r[1] for r in info}
            if cols and 'android_version' not in cols:
                precisa_recriar = True
            elif cols:
                pk_cols = [r[1] for r in info if r[5] > 0]
                if pk_cols == ['codename']:
                    precisa_recriar = True
                elif 'srv_id' in pk_cols:
                    precisa_recriar = True
        except Exception:
            pass
        if precisa_recriar:
            c.execute('DROP TABLE IF EXISTS modelos')
        c.execute("\n            CREATE TABLE IF NOT EXISTS modelos (\n                codename TEXT NOT NULL,\n                srv_id INTEGER NOT NULL,\n                marca TEXT NOT NULL,\n                modelo TEXT NOT NULL,\n                serial_len INTEGER DEFAULT 10,\n                status TEXT DEFAULT 'em_teste',\n                observacoes TEXT,\n                lote_cn TEXT DEFAULT '',\n                android_version INTEGER DEFAULT NULL,\n                sync_em TEXT,\n                PRIMARY KEY (codename, modelo)\n            )\n        ")
        c.execute('\n            CREATE TABLE IF NOT EXISTS _cache (\n                ref_id INTEGER NOT NULL, ref_tipo TEXT NOT NULL,\n                dados BLOB NOT NULL, chk TEXT NOT NULL,\n                ts_dl TEXT, ts_uso TEXT, n_uso INTEGER DEFAULT 0,\n                PRIMARY KEY (ref_id, ref_tipo)\n            )\n        ')
        c.execute('\n            CREATE TABLE IF NOT EXISTS info_sync (\n                id INTEGER PRIMARY KEY DEFAULT 1,\n                ultima_atualizacao TEXT, ultima_tentativa TEXT,\n                total_modelos INTEGER DEFAULT 0\n            )\n        ')
        conn.commit()
        conn.close()
    def _conn(self):
        c = sqlite3.connect(self.db_path)
        c.row_factory = sqlite3.Row
        return c
    def pode_sincronizar(self) -> bool:
        conn = self._conn()
        n = conn.execute('SELECT COUNT(*) as c FROM modelos').fetchone()['c']
        if n == 0:
            conn.close()
            return True
        info = conn.execute('SELECT * FROM info_sync WHERE id=1').fetchone()
        conn.close()
        if not info or not info['ultima_atualizacao']:
            return True
        try:
            d = datetime.now() - datetime.fromisoformat(info['ultima_atualizacao'])
            if d < timedelta(hours=self.SYNC_HORAS):
                return False
        except (TypeError, ValueError):
            return True
        if not info['ultima_tentativa']:
            return True
        try:
            dt = datetime.now() - datetime.fromisoformat(info['ultima_tentativa'])
        except (TypeError, ValueError):
            return True
        return dt >= timedelta(minutes=self.DEBOUNCE_MIN)
    def sincronizar(self, force: bool=False) -> tuple:
        if not _MYSQL_OK:
            return (False, 'Modulo de conexao indisponivel')
        if not force and not self.pode_sincronizar():
            return (False, 'OK')
        conn_m = None
        try:
            cfg = db_config(connect_timeout=10, read_timeout=30, cursorclass=pymysql.cursors.DictCursor)
            conn_m = pymysql.connect(**cfg)
            cur = conn_m.cursor()
            cur.execute("\n                SELECT id, marca, modelo, codename, serial_len, status,\n                       observacoes, modelos_compativeis, android_version\n                FROM moto_frp_lks WHERE status IN ('ativo', 'teste')\n                ORDER BY marca\n            ")
            rows = cur.fetchall()
            conn_m.close()
            conn_m = None
            with self._lock:
                conn = self._conn()
                conn.execute('INSERT OR IGNORE INTO info_sync (id) VALUES (1)')
                conn.execute('UPDATE info_sync SET ultima_tentativa=? WHERE id=1', (datetime.now().isoformat(),))
                ids_srv = set()
                total_modelos = 0
                agora = datetime.now().isoformat()
                for r in rows:
                    ids_srv.add(r['id'])
                    sl = r.get('serial_len') or 10
                    marca = r['marca']
                    lote_cn = r.get('codename') or ''
                    av = r.get('android_version')
                    mc_raw = r.get('modelos_compativeis')
                    if mc_raw:
                        modelos_j = json.loads(mc_raw) if isinstance(mc_raw, str) else mc_raw
                        for m in modelos_j:
                            m_av = m.get('android_version') or av
                            conn.execute('\n                                INSERT OR REPLACE INTO modelos\n                                    (codename, srv_id, marca, modelo, serial_len, status,\n                                     observacoes, lote_cn, android_version, sync_em)\n                                VALUES (?,?,?,?,?,?,?,?,?,?)\n                            ', (m['codename'], r['id'], marca, m['modelo'], sl, m.get('status', 'em_teste'), '', lote_cn, m_av, agora))
                            total_modelos += 1
                        continue
                    if not r.get('codename'):
                        continue
                    conn.execute('\n                            INSERT OR REPLACE INTO modelos\n                                (codename, srv_id, marca, modelo, serial_len, status,\n                                 observacoes, lote_cn, android_version, sync_em)\n                            VALUES (?,?,?,?,?,?,?,?,?,?)\n                        ', (r['codename'], r['id'], marca, r.get('modelo') or r['codename'], sl, r['status'], r.get('observacoes') or '', lote_cn, av, agora))
                    total_modelos += 1
                    continue
        except Exception:
            if conn_m:
                try:
                    conn_m.close()
                    return (False, 'Falha na conexao')
                except Exception:
                    return (False, 'Falha na conexao')
            return (False, 'Falha na conexao')
        atuais = {(x['codename'], x['modelo']) for x in conn.execute('SELECT codename, modelo FROM modelos WHERE sync_em=?', (agora,)).fetchall()}
        todos = {(x['codename'], x['modelo']) for x in conn.execute('SELECT codename, modelo FROM modelos').fetchall()}
        orfaos = todos - atuais
        if orfaos:
            sids_orfaos = set()
            for cn, mod in orfaos:
                row = conn.execute('SELECT srv_id FROM modelos WHERE codename=? AND modelo=?', (cn, mod)).fetchone()
                if row:
                    sids_orfaos.add(row['srv_id'])
                conn.execute('DELETE FROM modelos WHERE codename=? AND modelo=?', (cn, mod))
            sids_ativos = {x['srv_id'] for x in conn.execute('SELECT DISTINCT srv_id FROM modelos').fetchall()}
            for sid_orfao in sids_orfaos - sids_ativos:
                conn.execute('DELETE FROM _cache WHERE ref_id=?', (sid_orfao,))
        conn.execute('UPDATE info_sync SET ultima_atualizacao=?, total_modelos=? WHERE id=1', (agora, total_modelos))
        conn.commit()
        conn.close()
        try:
            pass
        except Exception:
            if conn_m:
                try:
                    conn_m.close()
                    return (False, 'Falha na conexao')
                except Exception:
                    return (False, 'Falha na conexao')
            return (False, 'Falha na conexao')
        if conn_m:
            try:
                conn_m.close()
            except Exception:
                return
            return True, f'{total_modelos} modelo(s) sincronizado(s)'
    def listar_marcas(self) -> list:
        conn = self._conn()
        rows = conn.execute("SELECT DISTINCT marca FROM modelos WHERE status IN ('ativo','em_teste') ORDER BY marca").fetchall()
        conn.close()
        return [r['marca'] for r in rows]
    def listar_modelos(self, marca: str) -> list:
        conn = self._conn()
        rows = conn.execute("SELECT srv_id, marca, modelo, codename, serial_len, status, android_version FROM modelos WHERE marca=? AND status IN ('ativo','em_teste') ORDER BY status, modelo", (marca,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    def get_android_version(self, codename: str, modelo: str='') -> int:
        '''Retorna android_version para o codename/modelo (ou 0 se nao definida).
        Se modelo fornecido, busca entrada exata; senao, prioriza srv_id maior.'''
        conn = self._conn()
        if modelo:
            row = conn.execute('SELECT android_version FROM modelos WHERE codename=? AND modelo=? LIMIT 1', (codename, modelo)).fetchone()
        else:
            row = conn.execute('SELECT android_version FROM modelos WHERE codename=? ORDER BY srv_id DESC LIMIT 1', (codename,)).fetchone()
        conn.close()
        if row and row['android_version']:
            return row['android_version']
        return 0
    def get_srv_id(self, codename: str) -> int:
        '''Retorna srv_id (classe do lote) para o codename.'''
        conn = self._conn()
        row = conn.execute('SELECT srv_id FROM modelos WHERE codename=? LIMIT 1', (codename,)).fetchone()
        conn.close()
        if row:
            return row['srv_id']
        return 1
    def get_lote_codename(self, codename: str) -> str:
        '''Retorna codename primario do lote.'''
        conn = self._conn()
        row = conn.execute('SELECT lote_cn FROM modelos WHERE codename=? LIMIT 1', (codename,)).fetchone()
        conn.close()
        if row and row['lote_cn']:
            return row['lote_cn']
        return codename
    _TIPO_MAP = {'lk_mod': 'a', 'lk_clean': 'b'}
    def download_lk(self, codename: str, tipo: str):
        if tipo not in ('lk_mod', 'lk_clean'):
            return (None, 'Tipo invalido')
        tipo_c = self._TIPO_MAP[tipo]
        conn = self._conn()
        m = conn.execute('SELECT srv_id FROM modelos WHERE codename=? LIMIT 1', (codename,)).fetchone()
        conn.close()
        if not m:
            return (None, 'Modelo nao encontrado')
        sid = m['srv_id']
        cached = self._cache_get(sid, tipo_c)
        if cached:
            return cached, 'OK'
        if not _MYSQL_OK:
            return (None, 'Modulo indisponivel')
        col = 'lk_mod_blob' if tipo == 'lk_mod' else 'lk_clean_blob'
        conn_m = None
        try:
            cfg = db_config(connect_timeout=15, read_timeout=90, cursorclass=pymysql.cursors.DictCursor)
            conn_m = pymysql.connect(**cfg)
            cur = conn_m.cursor()
            cur.execute(f"SELECT {col} FROM moto_frp_lks WHERE id=%s AND status IN ('ativo','teste')", (sid,))
            row = cur.fetchone()
            conn_m.close()
            conn_m = None
            if not row or not row[col]:
                if conn_m:
                    try:
                        conn_m.close()
                    except Exception:
                        pass
                    return (None, 'Dados indisponiveis no servidor')
                return (None, 'Dados indisponiveis no servidor')
        except Exception as exc:
            _logger.debug('download_lk falhou sid=%s tipo=%s: %s', sid, tipo, exc)
        try:
            dados = row[col]
            hv = hashlib.sha256(dados).hexdigest()
            with self._lock:
                conn = self._conn()
                conn.execute('\n                    INSERT OR REPLACE INTO _cache\n                        (ref_id, ref_tipo, dados, chk, ts_dl, ts_uso, n_uso)\n                    VALUES (?,?,?,?,?,?,1)\n                ', (sid, tipo_c, _enc(dados), hv, datetime.now().isoformat(), datetime.now().isoformat()))
                conn.commit()
                conn.close()
        except Exception as exc:
            _logger.debug('download_lk falhou sid=%s tipo=%s: %s', sid, tipo, exc)
        if conn_m:
            try:
                conn_m.close()
            except Exception:
                return
            return dados, 'OK'
    def _cache_get(self, sid: int, tipo: str):
        conn = self._conn()
        row = conn.execute('SELECT dados, chk FROM _cache WHERE ref_id=? AND ref_tipo=?', (sid, tipo)).fetchone()
        conn.close()
        if not row or not row['dados']:
            return
        try:
            dados = _dec(bytes(row['dados']))
            if hashlib.sha256(dados).hexdigest() != row['chk']:
                return
            with self._lock:
                c = self._conn()
                c.execute('UPDATE _cache SET ts_uso=?, n_uso=n_uso+1 WHERE ref_id=? AND ref_tipo=?', (datetime.now().isoformat(), sid, tipo))
                c.commit()
                c.close()
        except Exception:
            return
        return dados
# WARNING: Decompyle incomplete
