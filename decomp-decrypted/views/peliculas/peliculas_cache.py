import sqlite3
import hashlib
import json
import os
import time
import unicodedata
import re
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import (Optional, List, Dict, Tuple)
import logging
from app.utils._app_cfg import db_config
logger = logging.getLogger(__name__)
class PeliculasCache:
    SYNC_COOLDOWN_SECONDS = 86400
    CACHE_EXPIRY_HOURS = 24
    MYSQL_CONFIG = db_config(connect_timeout=10, ssl={'ca': None}, ssl_verify_cert=False)
    def __init__(self, cache_dir: Optional[str]=None):
        if cache_dir:
            self._cache_dir = Path(cache_dir)
        else:
            self._cache_dir = self._get_default_cache_dir()
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            self._cache_dir = self._get_default_cache_dir()
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._cache_dir / 'pc_data.db'
        self._meta_path = self._cache_dir / 'pc_meta.json'
        self._lock = threading.RLock()
        self._last_sync = None
        self._checksum = None
        self._load_metadata()
    def _get_default_cache_dir(self) -> Path:
        if os.name == 'nt':
            base = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')))
        else:
            base = Path.home() / '.cache'
        return base / '.tus_data' / 'pc'
    def _load_metadata(self) -> None:
        try:
            if self._meta_path.exists():
                with open(self._meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    last_sync_str = meta.get('last_sync')
                    if last_sync_str:
                        self._last_sync = datetime.fromisoformat(last_sync_str)
                    self._checksum = meta.get('checksum')
                return
        except Exception as e:
            logger.warning(f'Erro ao carregar metadados: {e}')
            self._last_sync = None
            self._checksum = None
    def _save_metadata(self) -> None:
        try:
            meta = {'last_sync': self._last_sync.isoformat() if self._last_sync else None, 'checksum': self._checksum, 'version': '1.1'}
            with open(self._meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f)
        except Exception as e:
            logger.error(f'Erro ao salvar metadados: {e}')
    def _calculate_checksum(self) -> str:
        if not self._db_path.exists():
            return ''
        sha256 = hashlib.sha256()
        with open(self._db_path, 'rb') as f:
            for chunk in iter((lambda: f.read(4096)), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    def _validate_integrity(self) -> bool:
        if not self._checksum:
            return True
        current = self._calculate_checksum()
        return current == self._checksum
    def _conectar(self) -> Optional[sqlite3.Connection]:
        try:
            conn = sqlite3.connect(str(self._db_path), timeout=10, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')
            conn.execute('PRAGMA cache_size=10000')
            conn.execute('PRAGMA temp_store=MEMORY')
            return conn
        except Exception as e:
            logger.error(f'Erro ao conectar SQLite: {e}')
    def _criar_tabelas(self, conn: sqlite3.Connection) -> None:
        conn.execute('\n            CREATE TABLE IF NOT EXISTS peliculas (\n                id INTEGER PRIMARY KEY,\n                grupo_id INTEGER NOT NULL,\n                modelo TEXT NOT NULL,\n                modelo_normalizado TEXT NOT NULL,\n                codigo_modelo TEXT,\n                marca TEXT,\n                data_atualizacao TEXT\n            )\n        ')
        conn.execute('\n            CREATE INDEX IF NOT EXISTS idx_modelo_norm \n            ON peliculas(modelo_normalizado)\n        ')
        conn.execute('\n            CREATE INDEX IF NOT EXISTS idx_grupo \n            ON peliculas(grupo_id)\n        ')
        conn.execute('\n            CREATE INDEX IF NOT EXISTS idx_marca \n            ON peliculas(marca)\n        ')
        conn.commit()
    def inicializar(self) -> bool:
        with self._lock:
            try:
                if not self._validate_integrity():
                    logger.warning('Cache corrompido detectado, ser├í recriado na pr├│xima sincroniza├º├úo')
                conn = self._conectar()
                if not conn:
                    return False
            except Exception as e:
                logger.error(f'Erro ao inicializar cache: {e}')
                return False
            try:
                self._criar_tabelas(conn)
                conn.close()
                logger.info('Cache inicializado com sucesso')
            except Exception as e:
                logger.error(f'Erro ao inicializar cache: {e}')
                return False
        return True
    @staticmethod
    def normalizar_texto(texto: str) -> str:
        if not texto:
            return ''
        texto = unicodedata.normalize('NFKD', texto)
        texto = ''.join((c for c in texto if not unicodedata.combining(c)))
        texto = texto.upper()
        texto = re.sub('[^A-Z0-9\\s]', ' ', texto)
        texto = re.sub('\\s+', ' ', texto).strip()
        return texto
    def buscar(self, termo: str) -> List[Dict]:
        if not termo or len(termo.strip()) < 2:
            return []
        termo_norm = self.normalizar_texto(termo)
        with self._lock:
            pass
        try:
            conn = self._conectar()
            if not conn:
                return []
        except Exception as e:
            logger.error(f'Erro na busca: {e}')
            return []
        try:
            cursor = conn.cursor()
            cursor.execute('\n                    SELECT DISTINCT grupo_id \n                    FROM peliculas \n                    WHERE modelo_normalizado LIKE ?\n                       OR codigo_modelo LIKE ?\n                    LIMIT 10\n                ', (f'%{termo_norm}%', f'%{termo_norm}%'))
        except Exception as e:
            logger.error(f'Erro na busca: {e}')
            return []
        try:
            grupos = [row['grupo_id'] for row in cursor.fetchall()]
            if not grupos:
                conn.close()
                return []
        except Exception as e:
            logger.error(f'Erro na busca: {e}')
            return []
        try:
            placeholders = ','.join('?' * len(grupos))
            cursor.execute(f'\n                    SELECT modelo, codigo_modelo, marca, grupo_id\n                    FROM peliculas\n                    WHERE grupo_id IN ({placeholders})\n                    ORDER BY marca, modelo\n                ', grupos)
            resultados = []
            for row in cursor.fetchall():
                resultados.append({'modelo': row['modelo'], 'codigo': row['codigo_modelo'], 'marca': row['marca'], 'grupo_id': row['grupo_id']})
            conn.close()
        except Exception as e:
            logger.error(f'Erro na busca: {e}')
            return []
        return resultados
    def get_estatisticas(self) -> Dict:
        stats = {'total_modelos': 0, 'total_grupos': 0, 'marcas': [], 'ultima_sync': None, 'cache_idade_horas': None, 'cache_valido': False}
        with self._lock:
            pass
        try:
            conn = self._conectar()
            if not conn:
                return stats
        except Exception as e:
            logger.error(f'Erro ao obter estat├¡sticas: {e}')
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as total FROM peliculas')
            row = cursor.fetchone()
            stats['total_modelos'] = row['total'] if row else 0
            cursor.execute('SELECT COUNT(DISTINCT grupo_id) as total FROM peliculas')
            row = cursor.fetchone()
            stats['total_grupos'] = row['total'] if row else 0
            cursor.execute('\n                    SELECT DISTINCT marca FROM peliculas \n                    WHERE marca IS NOT NULL \n                    ORDER BY marca\n                ')
        except Exception as e:
            logger.error(f'Erro ao obter estat├¡sticas: {e}')
        try:
            stats['marcas'] = [row['marca'] for row in cursor.fetchall()]
            conn.close()
            if self._last_sync:
                stats['ultima_sync'] = self._last_sync.isoformat()
                delta = datetime.now() - self._last_sync
                stats['cache_idade_horas'] = delta.total_seconds() / 3600
                stats['cache_valido'] = delta.total_seconds() < self.CACHE_EXPIRY_HOURS * 3600
        except Exception as e:
            logger.error(f'Erro ao obter estat├¡sticas: {e}')
        return stats
    def pode_sincronizar(self) -> Tuple[bool, int]:
        if not self._last_sync:
            return (True, 0)
        delta = (datetime.now() - self._last_sync).total_seconds()
        if delta >= self.SYNC_COOLDOWN_SECONDS:
            return (True, 0)
        return False, int(self.SYNC_COOLDOWN_SECONDS - delta)
    def sincronizar(self, force: bool=False) -> Tuple[bool, str]:
        pode, restante = self.pode_sincronizar()
        if not pode and not force:
            return False, f'Aguarde {restante} segundos para sincronizar novamente'
        try:
            import pymysql
        except ImportError:
            return (False, 'M├│dulo pymysql n├úo instalado')
        with self._lock:
            try:
                conn_mysql = pymysql.connect(**self.MYSQL_CONFIG)
                cursor_mysql = conn_mysql.cursor(pymysql.cursors.DictCursor)
                cursor_mysql.execute('\n                    SELECT id, grupo_id, modelo, modelo_normalizado, \n                           codigo_modelo, marca, data_atualizacao\n                    FROM peliculas_compatibilidade\n                    WHERE ativo = 1\n                    ORDER BY grupo_id, marca, modelo\n                ')
                modelos = cursor_mysql.fetchall()
                cursor_mysql.close()
                conn_mysql.close()
                if not modelos:
                    return (False, 'Nenhum modelo encontrado no servidor')
            except pymysql.Error as e:
                logger.error(f'Erro MySQL: {e}')
                return False, f'Erro de conex├úo: {str(e)}'
            except Exception as e:
                logger.error(f'Erro na sincroniza├º├úo: {e}')
                return False, f'Erro: {str(e)}'
            try:
                conn = self._conectar()
                if not conn:
                    return (False, 'Erro ao conectar cache local')
            except pymysql.Error as e:
                logger.error(f'Erro MySQL: {e}')
                return False, f'Erro de conex├úo: {str(e)}'
            except Exception as e:
                logger.error(f'Erro na sincroniza├º├úo: {e}')
                return False, f'Erro: {str(e)}'
            try:
                self._criar_tabelas(conn)
                conn.execute('DELETE FROM peliculas')
                for m in modelos:
                    marca = m['marca'].upper() if m['marca'] else None
                    conn.execute('\n                        INSERT INTO peliculas \n                        (id, grupo_id, modelo, modelo_normalizado, codigo_modelo, marca, data_atualizacao)\n                        VALUES (?, ?, ?, ?, ?, ?, ?)\n                    ', (m['id'], m['grupo_id'], m['modelo'], m['modelo_normalizado'], m['codigo_modelo'], marca, str(m['data_atualizacao']) if m['data_atualizacao'] else None))
                conn.commit()
                conn.close()
                self._last_sync = datetime.now()
                self._checksum = self._calculate_checksum()
                self._save_metadata()
                logger.info(f'Sincroniza├º├úo conclu├¡da: {len(modelos)} modelos')
            except pymysql.Error as e:
                logger.error(f'Erro MySQL: {e}')
                return False, f'Erro de conex├úo: {str(e)}'
            except Exception as e:
                logger.error(f'Erro na sincroniza├º├úo: {e}')
                return False, f'Erro: {str(e)}'
        return True, f'Sincronizado: {len(modelos)} modelos carregados'
    def get_modelos_por_marca(self, marca: str) -> List[Dict]:
        with self._lock:
            pass
        try:
            conn = self._conectar()
            if not conn:
                return []
        except Exception as e:
            logger.error(f'Erro ao buscar por marca: {e}')
            return []
        try:
            cursor = conn.cursor()
            cursor.execute('\n                    SELECT modelo, codigo_modelo, grupo_id\n                    FROM peliculas\n                    WHERE marca = ?\n                    ORDER BY modelo\n                ', (marca.upper(),))
        except Exception as e:
            logger.error(f'Erro ao buscar por marca: {e}')
            return []
        try:
            resultados = [dict(row) for row in cursor.fetchall()]
            conn.close()
        except Exception as e:
            logger.error(f'Erro ao buscar por marca: {e}')
            return []
        return resultados
    def verificar_integridade(self) -> Dict:
        status = {'arquivo_existe': self._db_path.exists(), 'checksum_valido': False, 'tabelas_ok': False, 'erro': None}
        if not status['arquivo_existe']:
            return status
        status['checksum_valido'] = self._validate_integrity()
        with self._lock:
            pass
        try:
            conn = self._conectar()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tabelas = [row['name'] for row in cursor.fetchall()]
                status['tabelas_ok'] = 'peliculas' in tabelas
                conn.close()
        except Exception as e:
            status['erro'] = str(e)
        return status
_cache_instance: Optional[PeliculasCache] = None
_cache_lock = threading.Lock()
def get_cache() -> PeliculasCache:
    global _cache_instance
    with _cache_lock:
        if _cache_instance is None:
            _cache_instance = PeliculasCache()
        return _cache_instance
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    cache = PeliculasCache(cache_dir='./teste_cache')
    print('=== TESTE DO CACHE DE PELICULAS ===\n')
    print('1. Inicializando cache...')
    if cache.inicializar():
        print('   OK - Cache inicializado\n')
    else:
        print('   ERRO - Falha ao inicializar\n')
        exit(1)
    print('2. Sincronizando com MySQL...')
    sucesso, msg = cache.sincronizar(force=True)
    print(f'   {msg}\n')
    print('3. Estatisticas:')
    stats = cache.get_estatisticas()
    print(f'   Total modelos: {stats['total_modelos']}')
    print(f'   Total grupos: {stats['total_grupos']}')
    print(f'   Marcas: {', '.join(stats['marcas'])}\n')
    print('4. Teste de busca:')
    termos = ['A52', 'iPhone 11', 'Moto G', 'Xiaomi']
    for termo in termos:
        resultados = cache.buscar(termo)
        print(f"   '{termo}': {len(resultados)} modelos compativeis")
        if resultados[:3]:
            for r in resultados[:3]:
                print(f'      - {r['modelo']}')
            if len(resultados) > 3:
                print(f'      ... e mais {len(resultados) - 3}')
        print()
    print('5. Verificando cooldown:')
    pode, segundos = cache.pode_sincronizar()
    if pode:
        print('   Pode sincronizar agora')
    else:
        print(f'   Aguardar {segundos} segundos')
    print('\n6. Verificando integridade:')
    integ = cache.verificar_integridade()
    print(f'   Arquivo existe: {integ['arquivo_existe']}')
    print(f'   Checksum valido: {integ['checksum_valido']}')
    print(f'   Tabelas OK: {integ['tabelas_ok']}')
    print('\n=== TESTE CONCLUIDO ===')
