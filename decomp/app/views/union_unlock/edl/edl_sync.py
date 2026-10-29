'''
Cache local de modelos EDL ÔÇö sincronizacao com servidor remoto.
TECH UNION SOLUTIONS ÔÇö Modulo QCOM EDL (isolado do edl_sync de producao)
Totalmente independente do app/database/edl_sync.py:
- Banco SQLite proprio: edl_qcom.db (N├âO compartilha com edl_modelos.db)
- Funcionalidades exclusivas: loaders_auto, busca 7 niveis, auth
- O edl_sync de producao (database/) continua intocado
Padrao identico ao LoaderCache (QCOM9008):
- sync baixa apenas metadados (rapido, <2s)
- loader blob baixado sob demanda quando usuario seleciona modelo
- criptografia XOR + zlib para dados em disco
'''
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
from typing import (Dict, List, Optional, Tuple)
try:
    import pymysql
    _CONEXAO_DISPONIVEL = True
except ImportError:
    _CONEXAO_DISPONIVEL = False
from app.utils._app_cfg import db_config
try:
    from app.utils._cfg_probe import _is_dev_env as _probe_is_dev
    _DEV_MODE = bool(_probe_is_dev())
except Exception:
    _DEV_MODE = False
def _status_loaders():
    if _DEV_MODE:
        return ('ativo', 'desenvolvimento')
    return ('ativo',)
def _status_in_clause(values):
    return ', '.join(['%s'] * len(values))
def _log(msg: str):
    print(f'[EDL_QCOM_SYNC] {msg}', flush=True)
def _resolve_edl_db():
    try:
        from app.utils.path_manager import PathManager
        tools = PathManager.get_unlock_tools_dir()
        if tools:
            p = os.path.normpath(os.path.join(os.path.dirname(tools), 'edl', 'edl_qcom.db'))
            if os.path.isfile(p):
                return Path(p)
    except Exception:
        pass
    return Path(__file__).parent / 'edl_qcom.db'
_DB_PATH = _resolve_edl_db()
_CONFIG_CONEXAO = db_config(connect_timeout=10, read_timeout=30, ssl={'ca': None}, ssl_verify_cert=False)
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
class EdlSync:
    '''
    Cache local (SQLite) de modelos EDL cadastrados no servidor.
    Padrao identico ao LoaderCache QCOM:
    - SYNC_HORAS: Intervalo entre sincronizacoes (24h)
    - DEBOUNCE_MIN: Minimo entre tentativas quando ja tem dados (30 min)
    - sync baixa APENAS metadados (rapido)
    - loader blob baixado sob demanda (download_loader)
    '''
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
        c.execute("\n            CREATE TABLE IF NOT EXISTS modelos (\n                srv_id    INTEGER PRIMARY KEY,\n                marca     TEXT NOT NULL,\n                modelo    TEXT NOT NULL,\n                descricao TEXT,\n                memoria   TEXT DEFAULT 'emmc',\n                ops_enc   BLOB,\n                tamanho   INTEGER DEFAULT 0,\n                tem_testpoint INTEGER DEFAULT 0,\n                sync_em   TEXT\n            )\n        ")
        c.execute('\n            CREATE TABLE IF NOT EXISTS loaders_locais (\n                srv_id          INTEGER PRIMARY KEY,\n                dados_protegidos BLOB NOT NULL,\n                hash_verificacao TEXT NOT NULL,\n                data_download   TEXT,\n                ultimo_uso      TEXT,\n                contador_uso    INTEGER DEFAULT 0\n            )\n        ')
        c.execute('\n            CREATE TABLE IF NOT EXISTS testpoints_locais (\n                srv_id           INTEGER PRIMARY KEY,\n                imagem_protegida BLOB NOT NULL,\n                hash_verificacao TEXT NOT NULL,\n                data_download    TEXT\n            )\n        ')
        c.execute('\n            CREATE TABLE IF NOT EXISTS info_sistema (\n                id INTEGER PRIMARY KEY,\n                ultima_atualizacao TEXT,\n                ultima_tentativa_sync TEXT,\n                total_dispositivos INTEGER DEFAULT 0\n            )\n        ')
        c.execute("\n            CREATE TABLE IF NOT EXISTS loaders_auto_cache (\n                id        INTEGER PRIMARY KEY,\n                hw_id     TEXT NOT NULL,\n                pk_hash   TEXT NOT NULL,\n                oem       TEXT,\n                chipset   TEXT,\n                oem_id    TEXT,\n                memoria   TEXT DEFAULT 'emmc',\n                tamanho   INTEGER DEFAULT 0,\n                hash_sha256 TEXT,\n                status    TEXT DEFAULT 'ativo',\n                sync_em   TEXT\n            )\n        ")
        c.execute('\n            CREATE TABLE IF NOT EXISTS loaders_auto_locais (\n                id               INTEGER PRIMARY KEY,\n                dados_protegidos BLOB NOT NULL,\n                hash_verificacao TEXT NOT NULL,\n                data_download    TEXT,\n                ultimo_uso       TEXT,\n                contador_uso     INTEGER DEFAULT 0\n            )\n        ')
        c.execute('\n            CREATE TABLE IF NOT EXISTS edl_auth_vip (\n                id            INTEGER PRIMARY KEY,\n                product_id    INTEGER,\n                chipset       TEXT,\n                descricao     TEXT,\n                marcas        TEXT,\n                digest        BLOB,\n                sign_data     BLOB,\n                ativo         INTEGER DEFAULT 1,\n                sync_em       TEXT\n            )\n        ')
        c.execute('CREATE INDEX IF NOT EXISTS idx_marca ON modelos(marca)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_auto_hwid ON loaders_auto_cache(hw_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_auto_pkhash ON loaders_auto_cache(pk_hash)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_vip_product ON edl_auth_vip(product_id)')
        for col, default in (('tem_testpoint', 'INTEGER DEFAULT 0'), ('requer_auth', 'TEXT DEFAULT NULL'), ('vip_auth_id', 'INTEGER DEFAULT NULL')):
            try:
                c.execute(f'ALTER TABLE modelos ADD COLUMN {col} {default}')
            except sqlite3.OperationalError:
                continue
        try:
            c.execute('ALTER TABLE loaders_auto_cache ADD COLUMN requer_auth TEXT DEFAULT NULL')
        except sqlite3.OperationalError:
            pass
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
    def _tem_modelos_locais(self) -> bool:
        conn = self._get_conn()
        try:
            row = conn.execute('SELECT COUNT(*) as c FROM modelos').fetchone()
            conn.close()
            return row['c'] > 0
        except sqlite3.OperationalError:
            conn.close()
            self._init_db()
            return False
    def pode_sincronizar(self) -> bool:
        '''
        Replica LoaderCache.pode_sincronizar_rede():
        - Sem modelos locais -> sempre sincroniza
        - Com modelos -> so se passou SYNC_HORAS desde ultimo sync
        - Respeita debounce de DEBOUNCE_MIN entre tentativas
        '''
        if not self._tem_modelos_locais():
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
            conn.execute('INSERT OR IGNORE INTO info_sistema (id, ultima_atualizacao, total_dispositivos) VALUES (1, NULL, 0)')
            conn.execute('UPDATE info_sistema SET ultima_tentativa_sync = ? WHERE id = 1', (datetime.now().isoformat(),))
            conn.commit()
        except sqlite3.OperationalError:
            conn.close()
            self._init_db()
            conn = self._get_conn()
            conn.execute('INSERT OR IGNORE INTO info_sistema (id, ultima_atualizacao, total_dispositivos) VALUES (1, NULL, 0)')
            conn.execute('UPDATE info_sistema SET ultima_tentativa_sync = ? WHERE id = 1', (datetime.now().isoformat(),))
            conn.commit()
        conn.close()
    def sincronizar(self) -> bool:
        if not _CONEXAO_DISPONIVEL:
            return False
        self._registrar_tentativa()
        _log('Conectando ao servidor...')
        conn_mysql = None
        try:
            conn_mysql = pymysql.connect(**_CONFIG_CONEXAO, **{'cursorclass': pymysql.cursors.DictCursor})
            cursor_mysql = conn_mysql.cursor()
            _status_filter = _status_loaders()
            _ph = _status_in_clause(_status_filter)
            cursor_mysql.execute(f'\n                SELECT id, marca, modelo, descricao, memoria, operacoes,\n                       LENGTH(loader_blob) as tamanho,\n                       CASE WHEN testpoint_blob IS NOT NULL THEN 1 ELSE 0 END as tem_testpoint,\n                       requer_auth, vip_auth_id\n                FROM loaders\n                WHERE status IN ({_ph}) AND operacoes IS NOT NULL\n                ORDER BY marca, modelo\n            ', _status_filter)
            rows = cursor_mysql.fetchall()
            conn_mysql.close()
            conn_mysql = None
            _log(f'Servidor retornou {len(rows)} modelos')
            with self._lock:
                conn = self._get_conn()
                ids_servidor = set()
                for row in rows:
                    ids_servidor.add(row['id'])
                    ops_raw = row.get('operacoes') or ''
                    if isinstance(ops_raw, dict):
                        ops_raw = json.dumps(ops_raw, ensure_ascii=False)
                    ops_enc = _encrypt_data(ops_raw.encode('utf-8')) if ops_raw else None
                    conn.execute('\n                        INSERT OR REPLACE INTO modelos\n                            (srv_id, marca, modelo, descricao, memoria, ops_enc,\n                             tamanho, tem_testpoint, requer_auth, vip_auth_id, sync_em)\n                        VALUES (?,?,?,?,?,?,?,?,?,?,?)\n                    ', (row['id'], row['marca'], row['modelo'], row.get('descricao') or '', row.get('memoria') or 'emmc', ops_enc, row.get('tamanho') or 0, row.get('tem_testpoint', 0), row.get('requer_auth') or None, row.get('vip_auth_id') or None, datetime.now().isoformat()))
                    continue
                ids_locais = {r['srv_id'] for r in conn.execute('SELECT srv_id FROM modelos').fetchall()}
                ids_orfaos = ids_locais - ids_servidor
                if ids_orfaos:
                    placeholders = ','.join(('?' for _ in ids_orfaos))
                    ids_list = list(ids_orfaos)
                    conn.execute(f'DELETE FROM modelos WHERE srv_id IN ({placeholders})', ids_list)
                    conn.execute(f'DELETE FROM loaders_locais WHERE srv_id IN ({placeholders})', ids_list)
                    conn.execute(f'DELETE FROM testpoints_locais WHERE srv_id IN ({placeholders})', ids_list)
                    _log(f'Removidos {len(ids_orfaos)} modelo(s) orfao(s) do cache: {ids_orfaos}')
                conn.execute('UPDATE info_sistema SET ultima_atualizacao = ?, total_dispositivos = ? WHERE id = 1', (datetime.now().isoformat(), len(rows)))
                conn.commit()
                conn.close()
            _log(f'Sincronizacao concluida ÔÇö {len(rows)} modelos salvos no cache')
            self.sincronizar_loaders_auto()
            self.sincronizar_vip_auth()
        except Exception as exc:
            _log(f'ERRO na sincronizacao ÔÇö {exc}')
        if conn_mysql is not None:
            try:
                conn_mysql.close()
            except Exception:
                pass
            return True
        return True
    def sincronizar_loaders_auto(self) -> bool:
        '''Sincroniza metadados da tabela loaders_auto do MySQL para cache local.'''
        if not _CONEXAO_DISPONIVEL:
            return False
        _log('Sincronizando loaders_auto...')
        conn_mysql = None
        try:
            conn_mysql = pymysql.connect(**_CONFIG_CONEXAO, **{'cursorclass': pymysql.cursors.DictCursor})
            cursor_mysql = conn_mysql.cursor()
            cursor_mysql.execute("\n                SELECT id, hw_id, pk_hash, oem, chipset, oem_id, memoria,\n                       LENGTH(loader_blob) as tamanho,\n                       hash_sha256, status, requer_auth\n                FROM loaders_auto\n                WHERE status IN ('ativo', 'teste')\n                ORDER BY hw_id\n            ")
            rows = cursor_mysql.fetchall()
            conn_mysql.close()
            conn_mysql = None
            _log(f'loaders_auto: {len(rows)} loaders no servidor')
            with self._lock:
                conn = self._get_conn()
                ids_servidor = set()
                for row in rows:
                    ids_servidor.add(row['id'])
                    conn.execute('\n                        INSERT OR REPLACE INTO loaders_auto_cache\n                            (id, hw_id, pk_hash, oem, chipset, oem_id,\n                             memoria, tamanho, hash_sha256, status, requer_auth, sync_em)\n                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)\n                    ', (row['id'], row.get('hw_id') or '', row.get('pk_hash') or '', row.get('oem') or '', row.get('chipset') or '', row.get('oem_id') or '', row.get('memoria') or 'emmc', row.get('tamanho') or 0, row.get('hash_sha256') or '', row.get('status') or 'ativo', row.get('requer_auth') or None, datetime.now().isoformat()))
                    continue
                ids_locais = {r['id'] for r in conn.execute('SELECT id FROM loaders_auto_cache').fetchall()}
                ids_orfaos = ids_locais - ids_servidor
                if ids_orfaos:
                    placeholders = ','.join(('?' for _ in ids_orfaos))
                    ids_list = list(ids_orfaos)
                    conn.execute(f'DELETE FROM loaders_auto_cache WHERE id IN ({placeholders})', ids_list)
                    conn.execute(f'DELETE FROM loaders_auto_locais WHERE id IN ({placeholders})', ids_list)
                    _log(f'Removidos {len(ids_orfaos)} loader(s) auto orfao(s): {ids_orfaos}')
                conn.commit()
                conn.close()
            _log(f'loaders_auto sincronizados ÔÇö {len(rows)} no cache')
        except Exception as exc:
            _log(f'ERRO sincronizar loaders_auto ÔÇö {exc}')
        if conn_mysql is not None:
            try:
                conn_mysql.close()
            except Exception:
                pass
            return True
        return True
    def sincronizar_vip_auth(self) -> bool:
        '''Sincroniza dados de autenticacao VIP do MySQL para cache SQLite.'''
        if not _CONEXAO_DISPONIVEL:
            return False
        _log('Sincronizando edl_auth_vip...')
        conn_mysql = None
        try:
            conn_mysql = pymysql.connect(**_CONFIG_CONEXAO, **{'cursorclass': pymysql.cursors.DictCursor})
            cursor_mysql = conn_mysql.cursor()
            cursor_mysql.execute('\n                SELECT id, product_id, chipset, descricao, marcas,\n                       digest, sign_data, ativo\n                FROM edl_auth_vip\n                WHERE ativo = 1\n            ')
            rows = cursor_mysql.fetchall()
            conn_mysql.close()
            conn_mysql = None
            _log(f'edl_auth_vip: {len(rows)} registros ativos no servidor')
            with self._lock:
                conn = self._get_conn()
                ids_servidor = set()
                for row in rows:
                    ids_servidor.add(row['id'])
                    conn.execute('\n                        INSERT OR REPLACE INTO edl_auth_vip\n                            (id, product_id, chipset, descricao, marcas,\n                             digest, sign_data, ativo, sync_em)\n                        VALUES (?,?,?,?,?,?,?,?,?)\n                    ', (row['id'], row.get('product_id'), row.get('chipset') or '', row.get('descricao') or '', row.get('marcas') or '', row.get('digest'), row.get('sign_data'), row.get('ativo', 1), datetime.now().isoformat()))
                ids_locais = {r['id'] for r in conn.execute('SELECT id FROM edl_auth_vip').fetchall()}
                ids_orfaos = ids_locais - ids_servidor
                if ids_orfaos:
                    placeholders = ','.join(('?' for _ in ids_orfaos))
                    conn.execute(f'DELETE FROM edl_auth_vip WHERE id IN ({placeholders})', list(ids_orfaos))
                    _log(f'Removidos {len(ids_orfaos)} registro(s) VIP orfao(s)')
                conn.commit()
                conn.close()
            _log(f'edl_auth_vip sincronizados ÔÇö {len(rows)} no cache')
        except Exception as exc:
            _log(f'ERRO sincronizar edl_auth_vip ÔÇö {exc}')
        if conn_mysql is not None:
            try:
                conn_mysql.close()
            except Exception:
                pass
            return True
        return True
    def buscar_loader_auto(self, hwid: str, pkhash: str) -> Optional[Dict]:
        '''
        Busca loader compativel no cache local por HWID + PKHASH.
        Retorna o primeiro match (retrocompativel).
        '''
        resultados = self.buscar_loaders_auto(hwid, pkhash)
        if resultados:
            return resultados[0]
    def buscar_loaders_auto(self, hwid: str, pkhash: str) -> List[Dict]:
        """
Busca TODOS os loaders compativeis no cache local por HWID + PKHASH.
Retorna lista de dicts ordenada por tamanho (maior primeiro = mais completo).
7 niveis de fallback (cascata ÔÇö avanca so se anterior retornou 0):
  1)   match completo (hwid + pkhash 16 chars)
  2)   prefixo 8 chars (hwid[:8] + pkhash[:8])
  2.5) MSM do HWID + campo oem_id (pega loaders com OEM=0001 no HWID antigo)
  3)   OEM_ID + PK_HASH (16, depois 8 chars)
  4)   PK_HASH 16 + OEM_ID, depois PK_HASH 16 sem filtro
  5)   OEM_ID + loader generico (MSM=00000000) ÔÇö Xiaomi/OnePlus com auth
Cada resultado recebe um campo 'srv' com label SRV0, SRV1, etc.
"""
        hwid = hwid.lower().strip()
        pkhash = pkhash.lower().strip()
        if not hwid or not pkhash:
            return []
        _cols = 'id, hw_id, pk_hash, oem, chipset, oem_id, memoria, tamanho, hash_sha256, requer_auth'
        _filter = "AND status IN ('ativo', 'teste')"
        _oem_eff = "LOWER(COALESCE(NULLIF(oem_id,''), SUBSTR(hw_id, 9, 4)))"
        conn = self._get_conn()
        rows = conn.execute(f'\n            SELECT {_cols} FROM loaders_auto_cache\n            WHERE LOWER(hw_id) = ? AND LOWER(SUBSTR(pk_hash, 1, 16)) = ?\n                  {_filter}\n            ORDER BY tamanho DESC\n        ', (hwid, pkhash[:16])).fetchall()
        if not rows:
            if len(hwid) >= 8 and len(pkhash) >= 8:
                rows = conn.execute(f'\n                SELECT {_cols} FROM loaders_auto_cache\n                WHERE LOWER(SUBSTR(hw_id, 1, 8)) = ?\n                      AND LOWER(SUBSTR(pk_hash, 1, 8)) = ?\n                      {_filter}\n                ORDER BY tamanho DESC\n            ', (hwid[:8], pkhash[:8])).fetchall()
        if not rows:
            if len(hwid) >= 12:
                oem_id = hwid[8:12]
                if oem_id != '0000':
                    rows = conn.execute(f'\n                    SELECT {_cols} FROM loaders_auto_cache\n                    WHERE LOWER(SUBSTR(hw_id, 1, 8)) = ?\n                          AND {_oem_eff} = ?\n                          {_filter}\n                    ORDER BY tamanho DESC\n                ', (hwid[:8], oem_id)).fetchall()
        if not rows:
            if len(hwid) >= 8:
                oem_id = hwid[8:12] if len(hwid) >= 12 else '0000'
                if oem_id == '0000':
                    rows = conn.execute(f'\n                    SELECT {_cols} FROM loaders_auto_cache\n                    WHERE LOWER(SUBSTR(hw_id, 1, 8)) = ?\n                          {_filter}\n                    ORDER BY tamanho DESC\n                ', (hwid[:8],)).fetchall()
        if not rows:
            if len(hwid) >= 12 and len(pkhash) >= 8:
                oem_id = hwid[8:12]
                rows = conn.execute(f'\n                SELECT {_cols} FROM loaders_auto_cache\n                WHERE {_oem_eff} = ?\n                      AND LOWER(SUBSTR(pk_hash, 1, 16)) = ?\n                      {_filter}\n                ORDER BY tamanho DESC\n            ', (oem_id, pkhash[:16])).fetchall()
                if not rows:
                    rows = conn.execute(f'\n                    SELECT {_cols} FROM loaders_auto_cache\n                    WHERE {_oem_eff} = ?\n                          AND LOWER(SUBSTR(pk_hash, 1, 8)) = ?\n                          {_filter}\n                    ORDER BY tamanho DESC\n                ', (oem_id, pkhash[:8])).fetchall()
        if not rows:
            if len(pkhash) >= 16 and len(hwid) >= 12:
                oem_id = hwid[8:12]
                rows = conn.execute(f'\n                SELECT {_cols} FROM loaders_auto_cache\n                WHERE LOWER(SUBSTR(pk_hash, 1, 16)) = ?\n                      AND {_oem_eff} = ?\n                      {_filter}\n                ORDER BY tamanho DESC\n            ', (pkhash[:16], oem_id)).fetchall()
        if not rows:
            if len(pkhash) >= 16:
                rows = conn.execute(f'\n                SELECT {_cols} FROM loaders_auto_cache\n                WHERE LOWER(SUBSTR(pk_hash, 1, 16)) = ?\n                      {_filter}\n                ORDER BY tamanho DESC\n            ', (pkhash[:16],)).fetchall()
        if not rows:
            if len(hwid) >= 12:
                oem_id = hwid[8:12]
                if oem_id != '0000':
                    rows = conn.execute(f"\n                    SELECT {_cols} FROM loaders_auto_cache\n                    WHERE {_oem_eff} = ?\n                          AND LOWER(SUBSTR(hw_id, 1, 10)) = '0000000000'\n                          {_filter}\n                    ORDER BY tamanho DESC\n                ", (oem_id,)).fetchall()
        conn.close()
        resultados = []
        for i, row in enumerate(rows):
            d = dict(row)
            d['srv'] = f'SRV{i}'
            resultados.append(d)
        return resultados
    def download_loader_auto(self, loader_id: int) -> Optional[bytes]:
        '''Baixa blob do loader_auto e armazena criptografado localmente.'''
        if not _CONEXAO_DISPONIVEL:
            return
        cached = self._get_loader_auto_local(loader_id)
        if cached:
            return cached
        conn_mysql = None
        try:
            conn_mysql = pymysql.connect(**_CONFIG_CONEXAO, **{'cursorclass': pymysql.cursors.DictCursor})
            cursor = conn_mysql.cursor()
            cursor.execute("SELECT loader_blob FROM loaders_auto WHERE id = %s AND status IN ('ativo','teste')", (loader_id,))
            row = cursor.fetchone()
            conn_mysql.close()
            conn_mysql = None
            if not row or not row['loader_blob']:
                if conn_mysql is not None:
                    try:
                        conn_mysql.close()
                    except Exception:
                        pass
                    return
                return
        except Exception as exc:
            _log(f'ERRO ao baixar loader auto {loader_id} ÔÇö {exc}')
        try:
            dados = row['loader_blob']
            hash_v = hashlib.sha256(dados).hexdigest()
            dados_enc = _encrypt_data(dados)
            with self._lock:
                conn = self._get_conn()
                conn.execute('\n                    INSERT OR REPLACE INTO loaders_auto_locais\n                        (id, dados_protegidos, hash_verificacao, data_download, ultimo_uso, contador_uso)\n                    VALUES (?, ?, ?, ?, ?, 1)\n                ', (loader_id, dados_enc, hash_v, datetime.now().isoformat(), datetime.now().isoformat()))
                conn.commit()
                conn.close()
            _log(f'Loader auto {loader_id} baixado ({len(dados)} bytes)')
        except Exception as exc:
            _log(f'ERRO ao baixar loader auto {loader_id} ÔÇö {exc}')
        if conn_mysql is not None:
            try:
                conn_mysql.close()
            except Exception:
                return
            return dados
    def _get_loader_auto_local(self, loader_id: int) -> Optional[bytes]:
        '''Retorna loader_auto do cache local se disponivel e integro.'''
        conn = self._get_conn()
        row = conn.execute('SELECT dados_protegidos, hash_verificacao FROM loaders_auto_locais WHERE id=?', (loader_id,)).fetchone()
        conn.close()
        if not row or not row['dados_protegidos']:
            return
        try:
            dados = _decrypt_data(bytes(row['dados_protegidos']))
            if hashlib.sha256(dados).hexdigest() != row['hash_verificacao']:
                _log(f'Loader auto {loader_id} ÔÇö hash INVALIDO, descartando cache')
                return
            with self._lock:
                conn = self._get_conn()
                conn.execute('UPDATE loaders_auto_locais SET ultimo_uso=?, contador_uso=contador_uso+1 WHERE id=?', (datetime.now().isoformat(), loader_id))
                conn.commit()
                conn.close()
        except Exception:
            return
        return dados
    def total_loaders_auto(self) -> int:
        '''Total de loaders_auto no cache local.'''
        conn = self._get_conn()
        try:
            row = conn.execute('SELECT COUNT(*) as c FROM loaders_auto_cache').fetchone()
        except sqlite3.OperationalError:
            conn.close()
            self._init_db()
            return 0
        conn.close()
        if row:
            return row['c']
        return 0
    def listar_marcas_disponiveis(self) -> List[str]:
        '''Retorna todas as marcas distintas cadastradas no cache local.
        Usado para gerar abas dinamicamente no EdlMainWidget.'''
        conn = self._get_conn()
        try:
            rows = conn.execute('SELECT DISTINCT marca FROM modelos ORDER BY marca').fetchall()
        except Exception:
            conn.close()
            return []
        conn.close()
        return [r['marca'] for r in rows]
    def buscar_modelos_por_marca(self, marca: str) -> List[Dict]:
        '''Busca modelos cadastrados (tabela loaders) por marca.
        Retorna lista leve (sem blob) para sugestao ao usuario.'''
        conn = self._get_conn()
        rows = conn.execute('\n            SELECT srv_id, modelo, descricao, memoria, requer_auth, vip_auth_id\n            FROM modelos WHERE LOWER(marca) = LOWER(?)\n            ORDER BY modelo\n        ', (marca,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    def listar_marca(self, marca: str) -> List[Dict]:
        conn = self._get_conn()
        rows = conn.execute('\n            SELECT srv_id, modelo, descricao, memoria, ops_enc, tamanho,\n                   tem_testpoint, requer_auth, vip_auth_id\n            FROM modelos WHERE LOWER(marca) = LOWER(?)\n            ORDER BY modelo\n        ', (marca,)).fetchall()
        conn.close()
        result = []
        for row in rows:
            operacoes = {}
            if row['ops_enc']:
                try:
                    operacoes = json.loads(_decrypt_data(bytes(row['ops_enc'])).decode('utf-8'))
                except Exception:
                    pass
            result.append({'srv_id': row['srv_id'], 'modelo': row['modelo'], 'descricao': row['descricao'] or '', 'memoria': row['memoria'] or 'emmc', 'operacoes': operacoes, 'tamanho': row['tamanho'] or 0, 'tem_testpoint': bool(row['tem_testpoint']), 'requer_auth': row['requer_auth'] or None, 'vip_auth_id': row['vip_auth_id'] or None})
        return result
    def download_loader(self, srv_id: int) -> Optional[bytes]:
        '''Baixa blob do servidor e armazena criptografado localmente.'''
        if not _CONEXAO_DISPONIVEL:
            return
        cached = self._get_loader_local(srv_id)
        if cached:
            return cached
        conn_mysql = None
        try:
            conn_mysql = pymysql.connect(**_CONFIG_CONEXAO, **{'cursorclass': pymysql.cursors.DictCursor})
            cursor = conn_mysql.cursor()
            _status_filter = _status_loaders()
            _ph = _status_in_clause(_status_filter)
            cursor.execute(f'SELECT loader_blob FROM loaders WHERE id = %s AND status IN ({_ph})', (srv_id,) + _status_filter)
            row = cursor.fetchone()
            conn_mysql.close()
            conn_mysql = None
            if not row or not row['loader_blob']:
                if conn_mysql is not None:
                    try:
                        conn_mysql.close()
                    except Exception:
                        pass
                    return
                return
        except Exception as exc:
            _log(f'ERRO ao baixar loader {srv_id} ÔÇö {exc}')
        try:
            dados = row['loader_blob']
            hash_v = hashlib.sha256(dados).hexdigest()
            dados_enc = _encrypt_data(dados)
            with self._lock:
                conn = self._get_conn()
                conn.execute('\n                    INSERT OR REPLACE INTO loaders_locais\n                        (srv_id, dados_protegidos, hash_verificacao, data_download, ultimo_uso, contador_uso)\n                    VALUES (?, ?, ?, ?, ?, 1)\n                ', (srv_id, dados_enc, hash_v, datetime.now().isoformat(), datetime.now().isoformat()))
                conn.commit()
                conn.close()
            _log(f'Loader {srv_id} baixado ({len(dados)} bytes)')
        except Exception as exc:
            _log(f'ERRO ao baixar loader {srv_id} ÔÇö {exc}')
        if conn_mysql is not None:
            try:
                conn_mysql.close()
            except Exception:
                return
            return dados
    def download_testpoint(self, srv_id: int) -> Optional[bytes]:
        '''Baixa imagem testpoint do servidor e armazena criptografada.'''
        if not _CONEXAO_DISPONIVEL:
            return
        cached = self._get_testpoint_local(srv_id)
        if cached:
            return cached
        conn_mysql = None
        try:
            conn_mysql = pymysql.connect(**_CONFIG_CONEXAO, **{'cursorclass': pymysql.cursors.DictCursor})
            cursor = conn_mysql.cursor()
            _status_filter = _status_loaders()
            _ph = _status_in_clause(_status_filter)
            cursor.execute(f'SELECT testpoint_blob FROM loaders WHERE id = %s AND status IN ({_ph})', (srv_id,) + _status_filter)
            row = cursor.fetchone()
            conn_mysql.close()
            conn_mysql = None
            if not row or not row['testpoint_blob']:
                if conn_mysql is not None:
                    try:
                        conn_mysql.close()
                    except Exception:
                        pass
                    return
                return
        except Exception as exc:
            _log(f'ERRO ao baixar testpoint {srv_id} ÔÇö {exc}')
        try:
            dados = row['testpoint_blob']
            hash_v = hashlib.sha256(dados).hexdigest()
            dados_enc = _encrypt_data(dados)
            with self._lock:
                conn = self._get_conn()
                conn.execute('\n                    INSERT OR REPLACE INTO testpoints_locais\n                        (srv_id, imagem_protegida, hash_verificacao, data_download)\n                    VALUES (?, ?, ?, ?)\n                ', (srv_id, dados_enc, hash_v, datetime.now().isoformat()))
                conn.commit()
                conn.close()
            _log(f'Testpoint {srv_id} baixado ({len(dados)} bytes)')
        except Exception as exc:
            _log(f'ERRO ao baixar testpoint {srv_id} ÔÇö {exc}')
        if conn_mysql is not None:
            try:
                conn_mysql.close()
            except Exception:
                return
            return dados
    def _get_testpoint_local(self, srv_id: int) -> Optional[bytes]:
        '''Retorna testpoint do cache local se disponivel.'''
        conn = self._get_conn()
        row = conn.execute('SELECT imagem_protegida, hash_verificacao FROM testpoints_locais WHERE srv_id=?', (srv_id,)).fetchone()
        conn.close()
        if not row or not row['imagem_protegida']:
            return
        try:
            dados = _decrypt_data(bytes(row['imagem_protegida']))
            if hashlib.sha256(dados).hexdigest() != row['hash_verificacao']:
                return
            return dados
        except Exception:
            return
    def _get_loader_local(self, srv_id: int) -> Optional[bytes]:
        '''Retorna loader do cache local se disponivel.'''
        conn = self._get_conn()
        row = conn.execute('SELECT dados_protegidos, hash_verificacao FROM loaders_locais WHERE srv_id=?', (srv_id,)).fetchone()
        conn.close()
        if not row or not row['dados_protegidos']:
            return
        try:
            dados = _decrypt_data(bytes(row['dados_protegidos']))
            if hashlib.sha256(dados).hexdigest() != row['hash_verificacao']:
                return
            with self._lock:
                conn = self._get_conn()
                conn.execute('UPDATE loaders_locais SET ultimo_uso=?, contador_uso=contador_uso+1 WHERE srv_id=?', (datetime.now().isoformat(), srv_id))
                conn.commit()
                conn.close()
        except Exception:
            return
        return dados
def get_vip_digest_sign(product_id: Optional[int]=None, chipset: Optional[str]=None, vip_auth_id: Optional[int]=None) -> Tuple[Optional[bytes], Optional[bytes]]:
    """Retorna (digest, sign_data) de edl_auth_vip.
Filtros (prioridade: vip_auth_id > product_id > chipset):
  - vip_auth_id: FK direta para edl_auth_vip.id (mais forte, sem ambiguidade)
  - product_id: numero reportado pelo QSaharaServer (ex: 460)
  - chipset: nome do chipset em lowercase (ex: 'sm6115')
  - Nenhum: retorna primeiro registro ativo (retrocompativel)
Ordem: SQLite local (edl_qcom.db), depois MySQL via db_config.
"""
    where = 'WHERE ativo=1'
    params_sqlite = ()
    params_mysql = ()
    if vip_auth_id is not None:
        where = 'WHERE id=?'
        params_sqlite = (vip_auth_id,)
        params_mysql = (vip_auth_id,)
        _log(f'VIP lookup por vip_auth_id={vip_auth_id} (link direto)')
    elif product_id is not None:
        where += ' AND product_id=?'
        params_sqlite = (product_id,)
        params_mysql = (product_id,)
    elif chipset:
        where += ' AND chipset=?'
        params_sqlite = (chipset,)
        params_mysql = (chipset,)
    else:
        _log('AVISO: get_vip_digest_sign chamada sem vip_auth_id, product_id nem chipset ÔÇö retornara primeiro registro ativo (pode ser chipset errado)')
    query_sqlite = f'SELECT digest, sign_data FROM edl_auth_vip {where} LIMIT 1'
    query_mysql = query_sqlite.replace('?', '%s')
    try:
        conn = sqlite3.connect(str(_DB_PATH))
        cur = conn.cursor()
        cur.execute(query_sqlite, params_sqlite)
        row = cur.fetchone()
        conn.close()
        if row and row[0] and row[1]:
            _log(f'VIP digest/sign do cache SQLite ({len(row[0])} + {len(row[1])} B)' + (f' [vip_auth_id={vip_auth_id}]' if vip_auth_id else '') + (f' [pid={product_id}]' if product_id else '') + (f' [chipset={chipset}]' if chipset else ''))
            return row[0], row[1]
    except Exception as exc:
        _log(f'VIP SQLite: {exc}')
    if not _CONEXAO_DISPONIVEL:
        return (None, None)
    try:
        cfg = db_config(connect_timeout=10, read_timeout=15)
        conn = pymysql.connect(**cfg)
        cur = conn.cursor()
        cur.execute(query_mysql, params_mysql)
        row = cur.fetchone()
        conn.close()
        if row and row[0] and row[1]:
            _log(f'VIP digest/sign MySQL ({len(row[0])} + {len(row[1])} B)' + (f' [vip_auth_id={vip_auth_id}]' if vip_auth_id else '') + (f' [pid={product_id}]' if product_id else ''))
            return row[0], row[1]
    except Exception as exc:
        _log(f'VIP MySQL: {exc}')
    return (None, None)
_instancia: Optional[EdlSync] = None
_instancia_lock = threading.Lock()
def get_sync() -> EdlSync:
    global _instancia
    if _instancia is None:
        with _instancia_lock:
            if _instancia is None:
                _instancia = EdlSync()
        return _instancia
    return _instancia
# WARNING: Decompyle incomplete
