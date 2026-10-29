import sqlite3
import pymysql
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import (Dict, List, Optional, Any)
from pathlib import Path
import threading
import time
from app.utils._app_cfg import db_config
class ServidorArquivosCacheManager:
    def __init__(self, db_path: str=None):
        if db_path is None:
            db_path = Path(__file__).parent / 'servidor_arquivos_cache.db'
        self.db_path = str(db_path)
        self.logger = logging.getLogger(__name__)
        self.cache_timeout_minutos = 21600
        self.max_tentativas_sync = 3
        self.intervalo_sync_segundos = 1296000
        self._lock = threading.Lock()
        self._sync_ativa = False
        self._ultima_sync = None
        self._criar_estrutura_cache()
    def _criar_estrutura_cache(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA synchronous=NORMAL')
                conn.execute('PRAGMA cache_size=20000')
                conn.execute('PRAGMA temp_store=MEMORY')
                cursor = conn.cursor()
                cursor.execute("\n                    CREATE TABLE IF NOT EXISTS cache_servidor_arquivos (\n                        id INTEGER PRIMARY KEY,\n                        marca TEXT NOT NULL,\n                        categoria TEXT NOT NULL,\n                        nome TEXT NOT NULL,\n                        descricao TEXT,\n                        versao TEXT,\n                        tamanho_arquivo INTEGER,\n                        tipo_arquivo TEXT,\n                        data_upload DATETIME,\n                        downloads_count INTEGER DEFAULT 0,\n                        is_gratuito BOOLEAN DEFAULT 0,\n                        is_premium BOOLEAN DEFAULT 0,\n                        tags TEXT,\n                        rating REAL DEFAULT 0.0,\n                        status TEXT DEFAULT 'ativo',\n                        \n                        -- CAMPOS ADICIONAIS DA TABELA SERVIDOR_ARQUIVOS\n                        whatsapp_contato TEXT,\n                        solucao TEXT,\n                        aprovado_admin BOOLEAN DEFAULT 0,\n                        avaliacao_media REAL DEFAULT 0.0,\n                        compatibilidade TEXT,\n                        destaque BOOLEAN DEFAULT 0,\n                        modelo TEXT,\n                        quantidade_downloads INTEGER DEFAULT 0,\n                        total_avaliacoes INTEGER DEFAULT 0,\n                        preco DECIMAL(10,2) DEFAULT 0.00,\n                        \n                        -- Campos de controle do cache\n                        cache_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,\n                        cache_valido_ate DATETIME,\n                        hash_metadados TEXT,\n                        sync_version INTEGER DEFAULT 1,\n                        \n                        -- ├ìndices otimizados\n                        UNIQUE(id)\n                    )\n                ")
                cursor.execute('\n                    CREATE TABLE IF NOT EXISTS cache_marcas_resumo (\n                        marca TEXT PRIMARY KEY,\n                        total_arquivos INTEGER DEFAULT 0,\n                        total_gratuitos INTEGER DEFAULT 0,\n                        total_premiums INTEGER DEFAULT 0,\n                        total_downloads INTEGER DEFAULT 0,\n                        categorias_json TEXT,\n                        ultima_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP,\n                        cache_valido_ate DATETIME\n                    )\n                ')
                cursor.execute("\n                    CREATE TABLE IF NOT EXISTS cache_sync_control (\n                        id INTEGER PRIMARY KEY AUTOINCREMENT,\n                        tipo_sync TEXT NOT NULL,\n                        timestamp_inicio DATETIME DEFAULT CURRENT_TIMESTAMP,\n                        timestamp_fim DATETIME,\n                        status TEXT DEFAULT 'em_andamento',\n                        registros_processados INTEGER DEFAULT 0,\n                        erros INTEGER DEFAULT 0,\n                        detalhes_json TEXT\n                    )\n                ")
                cursor.execute('\n                    CREATE TABLE IF NOT EXISTS cache_config (\n                        chave TEXT PRIMARY KEY,\n                        valor TEXT NOT NULL,\n                        data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP\n                    )\n                ')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_marca ON cache_servidor_arquivos(marca)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_categoria ON cache_servidor_arquivos(categoria)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_marca_categoria ON cache_servidor_arquivos(marca, categoria)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_gratuito ON cache_servidor_arquivos(is_gratuito)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_downloads ON cache_servidor_arquivos(downloads_count DESC)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_valido ON cache_servidor_arquivos(cache_valido_ate)')
                conn.commit()
        except Exception as e:
            self.logger.warning('Erro na estrutura de cache local')
            raise
    def _conectar_mysql(self) -> Optional[pymysql.Connection]:
        try:
            return pymysql.connect(**db_config(cursorclass=pymysql.cursors.DictCursor, ssl={'ca': None}, ssl_verify_cert=False, connect_timeout=10, read_timeout=30))
        except Exception as e:
            self.logger.warning('Falha na conexao com servidor remoto')
    def sincronizar_cache_completo(self) -> Dict[str, Any]:
        if self._sync_ativa:
            return {'status': 'em_andamento', 'mensagem': 'Sincroniza├º├úo j├í em andamento'}
        with self._lock:
            self._sync_ativa = True
            sync_id = None
            tempo_inicio = datetime.now()
            with sqlite3.connect(self.db_path) as cache_conn:
                cursor = cache_conn.cursor()
                cursor.execute("\n                        INSERT INTO cache_sync_control (tipo_sync, status) \n                        VALUES ('completa', 'em_andamento')\n                    ")
                sync_id = cursor.lastrowid
                cache_conn.commit()
            mysql_conn = self._conectar_mysql()
            if not mysql_conn:
                raise Exception('Falha na conexao com servidor')
            mysql_cursor = mysql_conn.cursor()
            mysql_cursor.execute("\n                    SELECT \n                        id, marca, categoria, titulo as nome, descricao, versao,\n                        tamanho_arquivo, tipo_arquivo, data_criacao as data_upload,\n                        quantidade_downloads as downloads_count, \n                        CASE WHEN tipo_arquivo = 'gratuito' THEN 1 ELSE 0 END as is_gratuito,\n                        CASE WHEN tipo_arquivo = 'pago' THEN 1 ELSE 0 END as is_premium,\n                        '' as tags, avaliacao_media as rating, status,\n                        whatsapp_contato, solucao, aprovado_admin,\n                        avaliacao_media, compatibilidade, destaque,\n                        modelo, quantidade_downloads, total_avaliacoes, preco\n                    FROM servidor_arquivos \n                    WHERE status = 'ativo'\n                    ORDER BY id\n                ")
            arquivos_mysql = mysql_cursor.fetchall()
            total_arquivos = len(arquivos_mysql)
            lote_size = 100
            total_inseridos = 0
            total_atualizados = 0
            erros = 0
            cache_valido_ate = datetime.now() + timedelta(minutes=self.cache_timeout_minutos)
            with sqlite3.connect(self.db_path) as cache_conn:
                cache_cursor = cache_conn.cursor()
                for i in range(0, total_arquivos, lote_size):
                    lote = arquivos_mysql[i:i + lote_size]
                    continue
                    cache_cursor.execute('\n                                        INSERT OR REPLACE INTO cache_servidor_arquivos \n                                        (id, marca, categoria, nome, descricao, versao,\n                                         tamanho_arquivo, tipo_arquivo, data_upload,\n                                         downloads_count, is_gratuito, is_premium,\n                                         tags, rating, status, whatsapp_contato, solucao,\n                                         aprovado_admin, avaliacao_media, compatibilidade,\n                                         destaque, modelo, quantidade_downloads, total_avaliacoes,\n                                         preco, cache_valido_ate, hash_metadados)\n                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n                                    ', (arquivo['id'], arquivo['marca'], arquivo['categoria'], arquivo['nome'], arquivo['descricao'], arquivo['versao'], arquivo['tamanho_arquivo'], arquivo['tipo_arquivo'], arquivo['data_upload'], arquivo['downloads_count'], arquivo['is_gratuito'], arquivo['is_premium'], arquivo['tags'], arquivo['rating'], arquivo['status'], arquivo.get('whatsapp_contato'), arquivo.get('solucao'), arquivo.get('aprovado_admin', False), arquivo.get('avaliacao_media', 0.0), arquivo.get('compatibilidade'), arquivo.get('destaque', False), arquivo.get('modelo'), arquivo.get('quantidade_downloads', 0), arquivo.get('total_avaliacoes', 0), arquivo.get('preco', 0.0), cache_valido_ate, hash_metadados))
                    if existe:
                        total_atualizados += 1
                        continue
                    total_inseridos += 1
                    continue
                    cache_conn.commit()
                    continue
            self._atualizar_resumo_marcas(cache_cursor)
            cache_conn.commit()
            self._limpar_arquivos_inativos(arquivos_mysql)
            tempo_fim = datetime.now()
            duracao = (tempo_fim - tempo_inicio).total_seconds()
            with sqlite3.connect(self.db_path) as cache_conn:
                cursor = cache_conn.cursor()
                cursor.execute("\n                        UPDATE cache_sync_control \n                        SET timestamp_fim = ?, status = 'concluida',\n                            registros_processados = ?, erros = ?\n                        WHERE id = ?\n                    ", (tempo_fim, total_arquivos, erros, sync_id))
                cursor.execute("\n                        INSERT OR REPLACE INTO cache_config (chave, valor) \n                        VALUES ('ultima_sync_completa', ?)\n                    ", (datetime.now().isoformat(),))
                cache_conn.commit()
            mysql_conn.close()
            self._ultima_sync = datetime.now()
            resultado = {'status': 'sucesso', 'total_arquivos': total_arquivos, 'inseridos': total_inseridos, 'atualizados': total_atualizados, 'erros': erros, 'duracao_segundos': duracao}
            self._sync_ativa = False
        return resultado
    def obter_marcas_disponiveis(self) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("\n                    SELECT COUNT(*) FROM cache_marcas_resumo \n                    WHERE cache_valido_ate > datetime('now')\n                ")
                if cursor.fetchone()[0] == 0:
                    self._atualizar_resumo_marcas(cursor)
                    conn.commit()
                cursor.execute('\n                    SELECT marca, total_arquivos, total_gratuitos, \n                           total_premiums, total_downloads, categorias_json\n                    FROM cache_marcas_resumo\n                    WHERE total_arquivos > 0\n                    ORDER BY total_arquivos DESC\n                ')
                marcas = []
                for row in cursor.fetchall():
                    categorias = json.loads(row[5]) if row[5] else []
                    marcas.append({'marca': row[0], 'total_arquivos': row[1], 'total_gratuitos': row[2], 'total_premiums': row[3], 'total_downloads': row[4], 'categorias': categorias})
                return marcas
        except Exception as e:
            self.logger.warning('Erro ao obter marcas do cache')
            return []
    def obter_arquivos_por_marca_categoria(self, marca: str, categoria: str='', limit: int=50, offset: int=0) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as cache_conn:
                cursor = cache_conn.cursor()
                where_clause = 'WHERE marca = ?'
                params = [marca]
                if categoria:
                    where_clause += ' AND categoria = ?'
                    params.append(categoria)
                where_clause += " AND cache_valido_ate > datetime('now')"
                cursor.execute(f'\n                    SELECT id, marca, categoria, nome, descricao, versao,\n                           tamanho_arquivo, tipo_arquivo, data_upload,\n                           downloads_count, is_gratuito, is_premium,\n                           tags, rating, status, whatsapp_contato, solucao,\n                           aprovado_admin, avaliacao_media, compatibilidade,\n                           destaque, modelo, quantidade_downloads, total_avaliacoes, preco\n                    FROM cache_servidor_arquivos\n                    {where_clause}\n                    ORDER BY downloads_count DESC, nome\n                    LIMIT ? OFFSET ?\n                ', params + [limit, offset])
                arquivos_cache = cursor.fetchall()
                if not arquivos_cache:
                    return []
                ids_arquivos = [str(row[0]) for row in arquivos_cache]
                mysql_conn = self._conectar_mysql()
                if not mysql_conn:
                    return self._formatar_arquivos_sem_links(arquivos_cache)
        except Exception:
            return []
        try:
            mysql_cursor = mysql_conn.cursor()
            placeholders = ','.join(['%s'] * len(ids_arquivos))
            mysql_cursor.execute(f"\n                        SELECT id, link_download \n                        FROM servidor_arquivos \n                        WHERE id IN ({placeholders}) AND status = 'ativo'\n                    ", ids_arquivos)
        except Exception:
            mysql_conn.close()
            try:
                return self._formatar_arquivos_sem_links(arquivos_cache)
            except Exception:
                return []
        try:
            links_mysql = {row['id']: row['link_download'] for row in mysql_cursor.fetchall()}
            mysql_conn.close()
        except Exception:
            mysql_conn.close()
            try:
                return self._formatar_arquivos_sem_links(arquivos_cache)
            except Exception:
                return []
        return self._combinar_cache_com_links(arquivos_cache, links_mysql)
    def buscar_arquivos(self, termo_busca: str, limit: int=100) -> List[Dict[str, Any]]:
        try:
            termo = f'%{termo_busca.lower()}%'
            with sqlite3.connect(self.db_path) as cache_conn:
                cursor = cache_conn.cursor()
                cursor.execute("\n                    SELECT id, marca, categoria, nome, descricao, versao,\n                           tamanho_arquivo, tipo_arquivo, data_upload,\n                           downloads_count, is_gratuito, is_premium,\n                           tags, rating, status, whatsapp_contato, solucao,\n                           aprovado_admin, avaliacao_media, compatibilidade,\n                           destaque, modelo, quantidade_downloads, total_avaliacoes, preco\n                    FROM cache_servidor_arquivos\n                    WHERE (\n                        LOWER(nome) LIKE ? OR \n                        LOWER(descricao) LIKE ? OR \n                        LOWER(tags) LIKE ? OR\n                        LOWER(marca) LIKE ? OR\n                        LOWER(solucao) LIKE ?\n                    )\n                    AND cache_valido_ate > datetime('now')\n                    ORDER BY downloads_count DESC, nome\n                    LIMIT ?\n                ", [termo, termo, termo, termo, termo, limit])
                resultados_cache = cursor.fetchall()
                if not resultados_cache:
                    return []
                ids_arquivos = [str(row[0]) for row in resultados_cache]
                mysql_conn = self._conectar_mysql()
                if mysql_conn:
                    try:
                        try:
                            mysql_cursor = mysql_conn.cursor()
                            placeholders = ','.join(['%s'] * len(ids_arquivos))
                            mysql_cursor.execute(f"\n                            SELECT id, link_download \n                            FROM servidor_arquivos \n                            WHERE id IN ({placeholders}) AND status = 'ativo'\n                        ", ids_arquivos)
                        except Exception:
                            mysql_conn.close()
                    finally:
                        pass
                    try:
                        try:
                            links_mysql = {row['id']: row['link_download'] for row in mysql_cursor.fetchall()}
                            mysql_conn.close()
                        except Exception:
                            mysql_conn.close()
                    finally:
                        pass
                    return self._combinar_cache_com_links(resultados_cache, links_mysql)
        except Exception:
            return []
        try:
            return self._formatar_arquivos_sem_links(resultados_cache)
        except Exception:
            return []
    def obter_arquivo_por_id(self, arquivo_id: int) -> Optional[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as cache_conn:
                cursor = cache_conn.cursor()
                cursor.execute("\n                    SELECT id, marca, categoria, nome, descricao, versao,\n                           tamanho_arquivo, tipo_arquivo, data_upload,\n                           downloads_count, is_gratuito, is_premium,\n                           tags, rating, status, whatsapp_contato, solucao,\n                           aprovado_admin, avaliacao_media, compatibilidade,\n                           destaque, modelo, quantidade_downloads, total_avaliacoes, preco\n                    FROM cache_servidor_arquivos\n                    WHERE id = ? AND cache_valido_ate > datetime('now')\n                ", (arquivo_id,))
                arquivo_cache = cursor.fetchone()
                if not arquivo_cache:
                    return self._obter_arquivo_mysql_direto(arquivo_id)
                mysql_conn = self._conectar_mysql()
                if not mysql_conn:
                    return self._formatar_arquivo_sem_link(arquivo_cache)
        except Exception:
            return
        try:
            mysql_cursor = mysql_conn.cursor()
            mysql_cursor.execute("\n                        SELECT link_download \n                        FROM servidor_arquivos \n                        WHERE id = %s AND status = 'ativo'\n                    ", (arquivo_id,))
            link_result = mysql_cursor.fetchone()
            mysql_conn.close()
            if link_result:
                return self._combinar_arquivo_cache_com_link(arquivo_cache, link_result['link_download'])
        except Exception:
            mysql_conn.close()
            try:
                return self._formatar_arquivo_sem_link(arquivo_cache)
            except Exception:
                return
        try:
            return
        except Exception:
            return
    def cache_precisa_atualizacao(self) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("\n                    SELECT valor FROM cache_config \n                    WHERE chave = 'ultima_sync_completa'\n                ")
                result = cursor.fetchone()
                if not result:
                    return True
                ultima_sync = datetime.fromisoformat(result[0])
                agora = datetime.now()
                diferenca_segundos = (agora - ultima_sync).total_seconds()
                return diferenca_segundos > self.intervalo_sync_segundos
        except Exception:
            return False
    def obter_estatisticas_cache(self) -> Dict[str, Any]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM cache_servidor_arquivos')
                total_cache = cursor.fetchone()[0]
                cursor.execute("\n                    SELECT COUNT(*) FROM cache_servidor_arquivos \n                    WHERE cache_valido_ate > datetime('now')\n                ")
                cache_validos = cursor.fetchone()[0]
                cursor.execute('\n                    SELECT marca, COUNT(*) FROM cache_servidor_arquivos \n                    GROUP BY marca ORDER BY COUNT(*) DESC LIMIT 5\n                ')
                top_marcas = cursor.fetchall()
                cursor.execute("\n                    SELECT valor FROM cache_config \n                    WHERE chave = 'ultima_sync_completa'\n                ")
                ultima_sync = cursor.fetchone()
                tamanho_mb = Path(self.db_path).stat().st_size / 1048576
        except Exception:
            return {}
        return {'total_arquivos_cache': total_cache, 'cache_validos': cache_validos, 'cache_expirados': total_cache - cache_validos, 'top_marcas': [{'marca': row[0], 'arquivos': row[1]} for row in top_marcas], 'ultima_sincronizacao': ultima_sync[0] if ultima_sync else None, 'tamanho_cache_mb': round(tamanho_mb, 2), 'cache_ativo': cache_validos > 0, 'sync_em_andamento': self._sync_ativa}
    def _gerar_hash_metadados(self, arquivo: Dict[str, Any]) -> str:
        try:
            campos_hash = {'nome': arquivo.get('nome', ''), 'descricao': arquivo.get('descricao', ''), 'versao': arquivo.get('versao', ''), 'tamanho_arquivo': arquivo.get('tamanho_arquivo', 0), 'downloads_count': arquivo.get('downloads_count', 0), 'is_gratuito': arquivo.get('is_gratuito', False), 'is_premium': arquivo.get('is_premium', False), 'rating': float(arquivo.get('rating', 0.0)) if arquivo.get('rating') is not None else 0.0, 'preco': float(arquivo.get('preco', 0.0)) if arquivo.get('preco') is not None else 0.0, 'avaliacao_media': float(arquivo.get('avaliacao_media', 0.0)) if arquivo.get('avaliacao_media') is not None else 0.0}
            hash_string = json.dumps(campos_hash, sort_keys=True)
            return hashlib.md5(hash_string.encode()).hexdigest()
        except Exception:
            return ''
    def _atualizar_resumo_marcas(self, cursor):
        try:
            cache_valido_ate = datetime.now() + timedelta(minutes=self.cache_timeout_minutos)
            cursor.execute('DELETE FROM cache_marcas_resumo')
            cursor.execute("\n                SELECT \n                    marca,\n                    COUNT(*) as total_arquivos,\n                    SUM(CASE WHEN is_gratuito = 1 THEN 1 ELSE 0 END) as total_gratuitos,\n                    SUM(CASE WHEN is_premium = 1 THEN 1 ELSE 0 END) as total_premiums,\n                    SUM(downloads_count) as total_downloads,\n                    GROUP_CONCAT(DISTINCT categoria) as categorias\n                FROM cache_servidor_arquivos\n                WHERE cache_valido_ate > datetime('now')\n                GROUP BY marca\n            ")
            for row in cursor.fetchall():
                categorias_list = row[5].split(',') if row[5] else []
                cursor.execute('\n                    INSERT INTO cache_marcas_resumo \n                    (marca, total_arquivos, total_gratuitos, total_premiums,\n                     total_downloads, categorias_json, cache_valido_ate)\n                    VALUES (?, ?, ?, ?, ?, ?, ?)\n                ', (row[0], row[1], row[2], row[3], row[4], json.dumps(categorias_list), cache_valido_ate))
            return
        except Exception:
            return
    def _limpar_arquivos_inativos(self, arquivos_ativos):
        try:
            pass
        except Exception:
            return
        try:
            ids_ativos = {arquivo['id'] for arquivo in arquivos_ativos}
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM cache_servidor_arquivos')
                ids_cache = {row[0] for row in cursor.fetchall()}
                ids_remover = ids_cache - ids_ativos
                if ids_remover:
                    placeholders = ','.join('?' * len(ids_remover))
                    cursor.execute(f'\n                        DELETE FROM cache_servidor_arquivos \n                        WHERE id IN ({placeholders})\n                    ', list(ids_remover))
                    conn.commit()
            return
        except Exception:
            return
    def _combinar_cache_com_links(self, arquivos_cache, links_mysql) -> List[Dict[str, Any]]:
        arquivos = []
        for row in arquivos_cache:
            arquivo_id = row[0]
            arquivo = {'id': row[0], 'marca': row[1], 'categoria': row[2], 'nome': row[3], 'descricao': row[4], 'versao': row[5], 'tamanho_arquivo': row[6], 'tipo_arquivo': row[7], 'data_upload': row[8], 'downloads_count': row[9], 'is_gratuito': bool(row[10]), 'is_premium': bool(row[11]), 'tags': row[12], 'rating': row[13], 'status': row[14], 'whatsapp_contato': row[15], 'solucao': row[16], 'aprovado_admin': bool(row[17]) if row[17] is not None else False, 'avaliacao_media': row[18] if row[18] is not None else 0.0, 'compatibilidade': row[19], 'destaque': bool(row[20]) if row[20] is not None else False, 'modelo': row[21], 'quantidade_downloads': row[22] if row[22] is not None else 0, 'total_avaliacoes': row[23] if row[23] is not None else 0, 'preco': row[24] if row[24] is not None else 0.0, 'link_download': links_mysql.get(arquivo_id, None)}
            arquivos.append(arquivo)
            continue
        return arquivos
    def _formatar_arquivos_sem_links(self, arquivos_cache) -> List[Dict[str, Any]]:
        arquivos = []
        for row in arquivos_cache:
            arquivo = {'id': row[0], 'marca': row[1], 'categoria': row[2], 'nome': row[3], 'descricao': row[4], 'versao': row[5], 'tamanho_arquivo': row[6], 'tipo_arquivo': row[7], 'data_upload': row[8], 'downloads_count': row[9], 'is_gratuito': bool(row[10]), 'is_premium': bool(row[11]), 'tags': row[12], 'rating': row[13], 'status': row[14], 'whatsapp_contato': row[15], 'solucao': row[16], 'aprovado_admin': bool(row[17]) if row[17] is not None else False, 'avaliacao_media': row[18] if row[18] is not None else 0.0, 'compatibilidade': row[19], 'destaque': bool(row[20]) if row[20] is not None else False, 'modelo': row[21], 'quantidade_downloads': row[22] if row[22] is not None else 0, 'total_avaliacoes': row[23] if row[23] is not None else 0, 'preco': row[24] if row[24] is not None else 0.0, 'link_download': None}
            arquivos.append(arquivo)
        return arquivos
    def _combinar_arquivo_cache_com_link(self, arquivo_cache, link) -> Dict[str, Any]:
        return {'id': arquivo_cache[0], 'marca': arquivo_cache[1], 'categoria': arquivo_cache[2], 'nome': arquivo_cache[3], 'descricao': arquivo_cache[4], 'versao': arquivo_cache[5], 'tamanho_arquivo': arquivo_cache[6], 'tipo_arquivo': arquivo_cache[7], 'data_upload': arquivo_cache[8], 'downloads_count': arquivo_cache[9], 'is_gratuito': bool(arquivo_cache[10]), 'is_premium': bool(arquivo_cache[11]), 'tags': arquivo_cache[12], 'rating': arquivo_cache[13], 'status': arquivo_cache[14], 'whatsapp_contato': arquivo_cache[15], 'solucao': arquivo_cache[16], 'aprovado_admin': bool(arquivo_cache[17]) if arquivo_cache[17] is not None else False, 'avaliacao_media': arquivo_cache[18] if arquivo_cache[18] is not None else 0.0, 'compatibilidade': arquivo_cache[19], 'destaque': bool(arquivo_cache[20]) if arquivo_cache[20] is not None else False, 'modelo': arquivo_cache[21], 'quantidade_downloads': arquivo_cache[22] if arquivo_cache[22] is not None else 0, 'total_avaliacoes': arquivo_cache[23] if arquivo_cache[23] is not None else 0, 'preco': arquivo_cache[24] if arquivo_cache[24] is not None else 0.0, 'link_download': link}
    def _formatar_arquivo_sem_link(self, arquivo_cache) -> Dict[str, Any]:
        return {'id': arquivo_cache[0], 'marca': arquivo_cache[1], 'categoria': arquivo_cache[2], 'nome': arquivo_cache[3], 'descricao': arquivo_cache[4], 'versao': arquivo_cache[5], 'tamanho_arquivo': arquivo_cache[6], 'tipo_arquivo': arquivo_cache[7], 'data_upload': arquivo_cache[8], 'downloads_count': arquivo_cache[9], 'is_gratuito': bool(arquivo_cache[10]), 'is_premium': bool(arquivo_cache[11]), 'tags': arquivo_cache[12], 'rating': arquivo_cache[13], 'status': arquivo_cache[14], 'whatsapp_contato': arquivo_cache[15], 'solucao': arquivo_cache[16], 'aprovado_admin': bool(arquivo_cache[17]) if arquivo_cache[17] is not None else False, 'avaliacao_media': arquivo_cache[18] if arquivo_cache[18] is not None else 0.0, 'compatibilidade': arquivo_cache[19], 'destaque': bool(arquivo_cache[20]) if arquivo_cache[20] is not None else False, 'modelo': arquivo_cache[21], 'quantidade_downloads': arquivo_cache[22] if arquivo_cache[22] is not None else 0, 'total_avaliacoes': arquivo_cache[23] if arquivo_cache[23] is not None else 0, 'preco': arquivo_cache[24] if arquivo_cache[24] is not None else 0.0, 'link_download': None}
    def _obter_arquivo_mysql_direto(self, arquivo_id: int) -> Optional[Dict[str, Any]]:
        try:
            mysql_conn = self._conectar_mysql()
            if not mysql_conn:
                return
            mysql_cursor = mysql_conn.cursor()
            mysql_cursor.execute("\n                SELECT id, marca, categoria, titulo as nome, descricao, versao,\n                       tamanho_arquivo, tipo_arquivo, data_criacao as data_upload,\n                       quantidade_downloads as downloads_count,\n                       CASE WHEN tipo_arquivo = 'gratuito' THEN 1 ELSE 0 END as is_gratuito,\n                       CASE WHEN tipo_arquivo = 'pago' THEN 1 ELSE 0 END as is_premium,\n                       '' as tags, avaliacao_media as rating, status, \n                       whatsapp_contato, solucao, aprovado_admin,\n                       avaliacao_media, compatibilidade, destaque, modelo, \n                       quantidade_downloads, total_avaliacoes, preco, link_download\n                FROM servidor_arquivos \n                WHERE id = %s AND status = 'ativo'\n            ", (arquivo_id,))
            arquivo_mysql = mysql_cursor.fetchone()
            mysql_conn.close()
            if arquivo_mysql:
                self._adicionar_arquivo_ao_cache(arquivo_mysql)
                return dict(arquivo_mysql)
        except Exception:
            pass
    def _adicionar_arquivo_ao_cache(self, arquivo_mysql):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cache_valido_ate = datetime.now() + timedelta(minutes=self.cache_timeout_minutos)
                hash_metadados = self._gerar_hash_metadados(arquivo_mysql)
                cursor.execute('\n                    INSERT OR REPLACE INTO cache_servidor_arquivos \n                    (id, marca, categoria, nome, descricao, versao,\n                     tamanho_arquivo, tipo_arquivo, data_upload,\n                     downloads_count, is_gratuito, is_premium,\n                     tags, rating, status, whatsapp_contato, solucao,\n                     aprovado_admin, avaliacao_media, compatibilidade,\n                     destaque, modelo, quantidade_downloads, total_avaliacoes,\n                     preco, cache_valido_ate, hash_metadados)\n                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n                ', (arquivo_mysql['id'], arquivo_mysql['marca'], arquivo_mysql['categoria'], arquivo_mysql['nome'], arquivo_mysql['descricao'], arquivo_mysql['versao'], arquivo_mysql['tamanho_arquivo'], arquivo_mysql['tipo_arquivo'], arquivo_mysql['data_upload'], arquivo_mysql['downloads_count'], arquivo_mysql['is_gratuito'], arquivo_mysql['is_premium'], arquivo_mysql['tags'], arquivo_mysql['rating'], arquivo_mysql['status'], arquivo_mysql.get('whatsapp_contato'), arquivo_mysql.get('solucao'), arquivo_mysql.get('aprovado_admin', False), arquivo_mysql.get('avaliacao_media', 0.0), arquivo_mysql.get('compatibilidade'), arquivo_mysql.get('destaque', False), arquivo_mysql.get('modelo'), arquivo_mysql.get('quantidade_downloads', 0), arquivo_mysql.get('total_avaliacoes', 0), arquivo_mysql.get('preco', 0.0), cache_valido_ate, hash_metadados))
                conn.commit()
        except Exception:
            return
