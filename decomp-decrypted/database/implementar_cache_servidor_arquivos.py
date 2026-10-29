import sqlite3
import pymysql
import json
from app.utils._app_cfg import db_config
import hashlib
import logging
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import (Dict, List, Optional)
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)
class CacheServerArquivos:
    def __init__(self, db_path: str=None):
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / 'app' / 'database' / 'servidor_arquivos_cache.db'
        self.db_path = str(db_path)
        self.cache_timeout_minutos = 15
        self.intervalo_sync_segundos = 300
        self.mysql_config = db_config(ssl={'ca': None}, ssl_verify_cert=False)
        logger.info('­ƒÜÇ Sistema de dados inicializado')
    def criar_estrutura_completa(self):
        try:
            logger.info('­ƒö¿ Criando estrutura do sistema...')
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA synchronous=NORMAL')
                conn.execute('PRAGMA cache_size=50000')
                conn.execute('PRAGMA temp_store=MEMORY')
                conn.execute('PRAGMA mmap_size=268435456')
                cursor = conn.cursor()
                logger.info('­ƒôï Criando tabela principal...')
                cursor.execute("\n                    CREATE TABLE IF NOT EXISTS cache_servidor_arquivos (\n                        id INTEGER PRIMARY KEY,\n                        marca TEXT NOT NULL,\n                        categoria TEXT NOT NULL,\n                        nome TEXT NOT NULL,\n                        descricao TEXT,\n                        versao TEXT,\n                        tamanho_arquivo INTEGER,\n                        tipo_arquivo TEXT,\n                        data_upload DATETIME,\n                        downloads_count INTEGER DEFAULT 0,\n                        is_gratuito BOOLEAN DEFAULT 0,\n                        is_premium BOOLEAN DEFAULT 0,\n                        tags TEXT,\n                        rating REAL DEFAULT 0.0,\n                        status TEXT DEFAULT 'ativo',\n                        preco DECIMAL(10,2),\n                        autor TEXT,\n                        \n                        -- CAMPOS ADICIONAIS DA TABELA SERVIDOR_ARQUIVOS\n                        whatsapp_contato TEXT,\n                        solucao TEXT,\n                        aprovado_admin BOOLEAN DEFAULT 0,\n                        avaliacao_media REAL DEFAULT 0.0,\n                        compatibilidade TEXT,\n                        destaque BOOLEAN DEFAULT 0,\n                        modelo TEXT,\n                        quantidade_downloads INTEGER DEFAULT 0,\n                        total_avaliacoes INTEGER DEFAULT 0,\n                        \n                        -- Campos de controle do cache\n                        cache_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,\n                        cache_valido_ate DATETIME,\n                        hash_metadados TEXT,\n                        ultima_modificacao DATETIME,\n                        \n                        UNIQUE(id)\n                    )\n                ")
                logger.info('­ƒôï Criando tabela de resumos...')
                cursor.execute('\n                    CREATE TABLE IF NOT EXISTS cache_marcas_resumo (\n                        marca TEXT PRIMARY KEY,\n                        total_arquivos INTEGER DEFAULT 0,\n                        total_gratuitos INTEGER DEFAULT 0,\n                        total_premiums INTEGER DEFAULT 0,\n                        total_downloads INTEGER DEFAULT 0,\n                        categorias_json TEXT,\n                        tags_populares_json TEXT,\n                        tamanho_total_mb INTEGER DEFAULT 0,\n                        rating_medio REAL DEFAULT 0.0,\n                        ultima_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP,\n                        cache_valido_ate DATETIME\n                    )\n                ')
                logger.info('­ƒôï Criando tabela de categorias...')
                cursor.execute('\n                    CREATE TABLE IF NOT EXISTS cache_categorias (\n                        marca TEXT NOT NULL,\n                        categoria TEXT NOT NULL,\n                        total_arquivos INTEGER DEFAULT 0,\n                        total_gratuitos INTEGER DEFAULT 0,\n                        total_premiums INTEGER DEFAULT 0,\n                        arquivo_mais_baixado_id INTEGER,\n                        cache_valido_ate DATETIME,\n                        \n                        PRIMARY KEY (marca, categoria)\n                    )\n                ')
                logger.info('­ƒôï Criando tabela de populares...')
                cursor.execute('\n                    CREATE TABLE IF NOT EXISTS cache_arquivos_populares (\n                        ranking INTEGER PRIMARY KEY,\n                        arquivo_id INTEGER NOT NULL,\n                        downloads_count INTEGER DEFAULT 0,\n                        rating REAL DEFAULT 0.0,\n                        cache_valido_ate DATETIME\n                    )\n                ')
                logger.info('­ƒôï Criando tabela de controle...')
                cursor.execute("\n                    CREATE TABLE IF NOT EXISTS cache_sync_control (\n                        id INTEGER PRIMARY KEY AUTOINCREMENT,\n                        tipo_sync TEXT NOT NULL,\n                        timestamp_inicio DATETIME DEFAULT CURRENT_TIMESTAMP,\n                        timestamp_fim DATETIME,\n                        status TEXT DEFAULT 'em_andamento',\n                        registros_processados INTEGER DEFAULT 0,\n                        registros_inseridos INTEGER DEFAULT 0,\n                        registros_atualizados INTEGER DEFAULT 0,\n                        erros INTEGER DEFAULT 0,\n                        detalhes_json TEXT,\n                        duracao_segundos REAL DEFAULT 0.0\n                    )\n                ")
                logger.info('­ƒôï Criando tabela de configura├º├Áes...')
                cursor.execute('\n                    CREATE TABLE IF NOT EXISTS cache_config (\n                        chave TEXT PRIMARY KEY,\n                        valor TEXT NOT NULL,\n                        data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP,\n                        descricao TEXT\n                    )\n                ')
                logger.info('­ƒôï Criando tabela de estat├¡sticas...')
                cursor.execute('\n                    CREATE TABLE IF NOT EXISTS cache_estatisticas (\n                        id INTEGER PRIMARY KEY AUTOINCREMENT,\n                        total_arquivos INTEGER DEFAULT 0,\n                        total_marcas INTEGER DEFAULT 0,\n                        total_categorias INTEGER DEFAULT 0,\n                        total_downloads INTEGER DEFAULT 0,\n                        tamanho_total_gb REAL DEFAULT 0.0,\n                        arquivo_mais_baixado_id INTEGER,\n                        marca_mais_popular TEXT,\n                        categoria_mais_popular TEXT,\n                        timestamp_calculo DATETIME DEFAULT CURRENT_TIMESTAMP\n                    )\n                ')
                logger.info('ÔÜí Criando ├¡ndices de performance...')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_marca ON cache_servidor_arquivos(marca)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_categoria ON cache_servidor_arquivos(categoria)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_marca_categoria ON cache_servidor_arquivos(marca, categoria)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_downloads_desc ON cache_servidor_arquivos(downloads_count DESC)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_rating_desc ON cache_servidor_arquivos(rating DESC)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_gratuito ON cache_servidor_arquivos(is_gratuito)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_premium ON cache_servidor_arquivos(is_premium)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_valido ON cache_servidor_arquivos(cache_valido_ate)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON cache_servidor_arquivos(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_data_upload ON cache_servidor_arquivos(data_upload DESC)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_nome_lower ON cache_servidor_arquivos(LOWER(nome))')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_descricao_lower ON cache_servidor_arquivos(LOWER(descricao))')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_lower ON cache_servidor_arquivos(LOWER(tags))')
                cursor.execute("\n                    INSERT OR REPLACE INTO cache_config (chave, valor, descricao)\n                    VALUES \n                    ('cache_version', '1.0', 'Vers├úo do cache'),\n                    ('cache_timeout_minutos', ?, 'Timeout do cache em minutos'),\n                    ('intervalo_sync_segundos', ?, 'Intervalo de sincroniza├º├úo em segundos'),\n                    ('max_arquivos_populares', '100', 'M├íximo de arquivos populares a cachear'),\n                    ('data_criacao', ?, 'Data de cria├º├úo do cache')\n                ", (str(self.cache_timeout_minutos), str(self.intervalo_sync_segundos), datetime.now().isoformat()))
                conn.commit()
                logger.info('Ô£à Sistema inicializado com sucesso!')
                self._mostrar_info_banco(cursor)
        except Exception as e:
            logger.error(f'ÔØî Erro ao criar estrutura: {str(e)}')
            raise
    def _mostrar_info_banco(self, cursor):
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tabelas = cursor.fetchall()
            logger.info(f'­ƒôè Banco criado com {len(tabelas)} tabelas:')
            for tabela in tabelas:
                cursor.execute(f'SELECT COUNT(*) FROM {tabela[0]}')
                count = cursor.fetchone()[0]
                logger.info(f'   ­ƒôï {tabela[0]}: {count} registros')
            tamanho_mb = Path(self.db_path).stat().st_size / 1048576
            logger.info(f'­ƒÆ¥ Tamanho do cache: {tamanho_mb:.2f} MB')
            return
        except Exception as e:
            logger.error(f'ÔØî Erro ao mostrar info do banco: {str(e)}')
    def conectar_mysql(self) -> Optional[pymysql.Connection]:
        try:
            conn = pymysql.connect(**self.mysql_config, **{'cursorclass': pymysql.cursors.DictCursor})
            return conn
        except Exception as e:
            logger.warning('Falha na conexao com servidor remoto')
    def sincronizar_cache_inicial(self):
        logger.info('­ƒöä Iniciando sincroniza├º├úo completa...')
        with sqlite3.connect(self.db_path) as cache_conn:
            cursor = cache_conn.cursor()
            cursor.execute("\n                INSERT INTO cache_sync_control (tipo_sync, status) \n                VALUES ('inicial_completa', 'em_andamento')\n            ")
            sync_id = cursor.lastrowid
            cache_conn.commit()
        tempo_inicio = time.time()
        try:
            for arquivo in lote:
                hash_metadados = self._gerar_hash_metadados(arquivo)
                cache_cursor.execute('\n                                SELECT id FROM cache_servidor_arquivos WHERE id = ?\n                            ', (arquivo['id'],))
                existe = cache_cursor.fetchone()
                cache_cursor.execute('\n                                INSERT OR REPLACE INTO cache_servidor_arquivos \n                                (id, marca, categoria, nome, descricao, versao,\n                                 tamanho_arquivo, tipo_arquivo, data_upload,\n                                 downloads_count, is_gratuito, is_premium,\n                                 tags, rating, status, preco, autor,\n                                 whatsapp_contato, solucao, aprovado_admin,\n                                 avaliacao_media, compatibilidade, destaque,\n                                 modelo, quantidade_downloads, total_avaliacoes,\n                                 cache_valido_ate, hash_metadados, ultima_modificacao)\n                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n                            ', (arquivo['id'], arquivo['marca'], arquivo['categoria'], arquivo['nome'], arquivo['descricao'], arquivo['versao'], arquivo['tamanho_arquivo'], arquivo['tipo_arquivo'], arquivo['data_upload'], arquivo['downloads_count'], arquivo['is_gratuito'], arquivo['is_premium'], arquivo['tags'], arquivo['rating'], arquivo['status'], arquivo['preco'], arquivo['autor'], arquivo.get('whatsapp_contato'), arquivo.get('solucao'), arquivo.get('aprovado_admin', False), arquivo.get('avaliacao_media', 0.0), arquivo.get('compatibilidade'), arquivo.get('destaque', False), arquivo.get('modelo'), arquivo.get('quantidade_downloads', 0), arquivo.get('total_avaliacoes', 0), cache_valido_ate, hash_metadados, arquivo.get('data_modificacao')))
                if existe:
                    total_atualizados += 1
        except Exception as e:
            with sqlite3.connect(self.db_path) as cache_conn:
                cursor = cache_conn.cursor()
                cursor.execute("\n                    UPDATE cache_sync_control \n                    SET status = 'erro', detalhes_json = ?\n                    WHERE id = ?\n                ", (json.dumps({'erro': str(e)}), sync_id))
                cache_conn.commit()
            if not None:
                pass
            logger.error(f'ÔØî Erro na sincroniza├º├úo: {str(e)}')
            raise
            try:
                try:
                    mysql_conn = self.conectar_mysql()
                    if not mysql_conn:
                        raise Exception('Falha na conexao com servidor')
                    mysql_cursor = mysql_conn.cursor()
                    logger.info('­ƒôÑ Buscando dados...')
                    mysql_cursor.execute("\n                SELECT \n                    id, marca, categoria, titulo as nome, descricao, versao,\n                    tamanho_arquivo, tipo_arquivo, data_upload,\n                    downloads_count, is_gratuito, is_premium,\n                    tags, rating, status, preco, autor,\n                    whatsapp_contato, solucao, aprovado_admin,\n                    avaliacao_media, compatibilidade, destaque,\n                    modelo, quantidade_downloads, total_avaliacoes,\n                    data_modificacao\n                FROM servidor_arquivos \n                WHERE status = 'ativo'\n                ORDER BY downloads_count DESC, id\n            ")
                    arquivos_mysql = mysql_cursor.fetchall()
                    total_arquivos = len(arquivos_mysql)
                    logger.info(f'­ƒôè Encontrados {total_arquivos} arquivos para sincronizar')
                    if total_arquivos == 0:
                        logger.warning('ÔÜá´©Å Nenhum arquivo encontrado!')
                        return
                    lote_size = 200
                    total_inseridos = 0
                    total_atualizados = 0
                    erros = 0
                    cache_valido_ate = datetime.now() + timedelta(minutes=self.cache_timeout_minutos)
                    with sqlite3.connect(self.db_path) as cache_conn:
                        cache_cursor = cache_conn.cursor()
                        for i in range(0, total_arquivos, lote_size):
                            lote = arquivos_mysql[i:i + lote_size]
                            lote_num = i // lote_size + 1
                            total_lotes = (total_arquivos + lote_size - 1) // lote_size
                            logger.info(f'­ƒöä Processando lote {lote_num}/{total_lotes} ({len(lote)} arquivos)')
                            continue
                            total_inseridos += 1
                            continue
                            cache_conn.commit()
                            progresso = (i + len(lote)) / total_arquivos * 100
                            logger.info(f'ÔÜí Progresso: {progresso:.1f}% ({i + len(lote)}/{total_arquivos})')
                            continue
                except Exception as e:
                    logger.error(f'ÔØî Erro no lote {lote_num}: {str(e)}')
                    erros += 1
            finally:
                if not None:
                    pass
        logger.info('­ƒöä Atualizando tabelas auxiliares...')
        self._atualizar_marcas_resumo(cache_cursor)
        self._atualizar_categorias_cache(cache_cursor)
        self._atualizar_arquivos_populares(cache_cursor)
        self._calcular_estatisticas(cache_cursor)
        cache_conn.commit()
        try:
            mysql_conn.close()
            tempo_fim = time.time()
            duracao = tempo_fim - tempo_inicio
            with sqlite3.connect(self.db_path) as cache_conn:
                cursor = cache_conn.cursor()
                cursor.execute("\n                    UPDATE cache_sync_control \n                    SET timestamp_fim = CURRENT_TIMESTAMP,\n                        status = 'concluida',\n                        registros_processados = ?,\n                        registros_inseridos = ?,\n                        registros_atualizados = ?,\n                        erros = ?,\n                        duracao_segundos = ?,\n                        detalhes_json = ?\n                    WHERE id = ?\n                ", (total_arquivos, total_inseridos, total_atualizados, erros, duracao, json.dumps({'total_lotes': total_lotes, 'lote_size': lote_size, 'cache_timeout_minutos': self.cache_timeout_minutos}), sync_id))
                cursor.execute("\n                    INSERT OR REPLACE INTO cache_config (chave, valor, descricao)\n                    VALUES ('ultima_sync_completa', ?, '├Ültima sincroniza├º├úo completa')\n                ", (datetime.now().isoformat(),))
                cache_conn.commit()
            logger.info('Ô£à Sincroniza├º├úo conclu├¡da!')
            logger.info('­ƒôè Estat├¡sticas:')
            logger.info(f'   ­ƒôÑ Inseridos: {total_inseridos}')
            logger.info(f'   ­ƒöä Atualizados: {total_atualizados}')
            logger.info(f'   ÔØî Erros: {erros}')
            logger.info(f'   ÔÅ▒´©Å Dura├º├úo: {duracao:.2f}s')
            logger.info(f'   ÔÜí Performance: {total_arquivos / duracao:.1f} arquivos/s')
        except Exception as e:
            with sqlite3.connect(self.db_path) as cache_conn:
                cursor = cache_conn.cursor()
                cursor.execute("\n                    UPDATE cache_sync_control \n                    SET status = 'erro', detalhes_json = ?\n                    WHERE id = ?\n                ", (json.dumps({'erro': str(e)}), sync_id))
                cache_conn.commit()
            if not None:
                pass
            logger.error(f'ÔØî Erro na sincroniza├º├úo: {str(e)}')
            raise
    def _gerar_hash_metadados(self, arquivo):
        try:
            campos = {'nome': arquivo.get('nome', ''), 'descricao': arquivo.get('descricao', ''), 'versao': arquivo.get('versao', ''), 'downloads_count': arquivo.get('downloads_count', 0), 'is_gratuito': arquivo.get('is_gratuito', False), 'rating': arquivo.get('rating', 0.0), 'preco': str(arquivo.get('preco', 0))}
            hash_string = json.dumps(campos, sort_keys=True)
            return hashlib.md5(hash_string.encode()).hexdigest()
        except:
            return ''
    def _atualizar_marcas_resumo(self, cursor):
        try:
            logger.info('­ƒôè Atualizando resumo de marcas...')
            cache_valido_ate = datetime.now() + timedelta(minutes=self.cache_timeout_minutos)
            cursor.execute('DELETE FROM cache_marcas_resumo')
            cursor.execute('\n                SELECT \n                    marca,\n                    COUNT(*) as total_arquivos,\n                    SUM(CASE WHEN is_gratuito = 1 THEN 1 ELSE 0 END) as total_gratuitos,\n                    SUM(CASE WHEN is_premium = 1 THEN 1 ELSE 0 END) as total_premiums,\n                    SUM(downloads_count) as total_downloads,\n                    GROUP_CONCAT(DISTINCT categoria) as categorias,\n                    SUM(CASE WHEN tamanho_arquivo IS NOT NULL THEN tamanho_arquivo ELSE 0 END) / (1024*1024) as tamanho_total_mb,\n                    AVG(CASE WHEN rating > 0 THEN rating ELSE NULL END) as rating_medio\n                FROM cache_servidor_arquivos\n                GROUP BY marca\n                ORDER BY total_arquivos DESC\n            ')
            marcas = cursor.fetchall()
            for marca in marcas:
                categorias_list = marca[5].split(',') if marca[5] else []
                cursor.execute('\n                    INSERT INTO cache_marcas_resumo \n                    (marca, total_arquivos, total_gratuitos, total_premiums,\n                     total_downloads, categorias_json, tamanho_total_mb, rating_medio, cache_valido_ate)\n                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)\n                ', (marca[0], marca[1], marca[2], marca[3], marca[4], json.dumps(categorias_list), int(marca[6] or 0), round(marca[7] or 0.0, 2), cache_valido_ate))
            logger.info(f'Ô£à {len(marcas)} marcas processadas')
            return
        except Exception as e:
            logger.error(f'ÔØî Erro atualizar marcas: {str(e)}')
    def _atualizar_categorias_cache(self, cursor):
        try:
            logger.info('­ƒôè Atualizando categorias...')
            cache_valido_ate = datetime.now() + timedelta(minutes=self.cache_timeout_minutos)
            cursor.execute('DELETE FROM cache_categorias')
            cursor.execute('\n                SELECT \n                    marca, categoria,\n                    COUNT(*) as total_arquivos,\n                    SUM(CASE WHEN is_gratuito = 1 THEN 1 ELSE 0 END) as total_gratuitos,\n                    SUM(CASE WHEN is_premium = 1 THEN 1 ELSE 0 END) as total_premiums\n                FROM cache_servidor_arquivos\n                GROUP BY marca, categoria\n                ORDER BY marca, total_arquivos DESC\n            ')
            categorias = cursor.fetchall()
            for cat in categorias:
                cursor.execute('\n                    SELECT id FROM cache_servidor_arquivos\n                    WHERE marca = ? AND categoria = ?\n                    ORDER BY downloads_count DESC, rating DESC\n                    LIMIT 1\n                ', (cat[0], cat[1]))
                arquivo_top = cursor.fetchone()
                arquivo_top_id = arquivo_top[0] if arquivo_top else None
                cursor.execute('\n                    INSERT INTO cache_categorias \n                    (marca, categoria, total_arquivos, total_gratuitos, \n                     total_premiums, arquivo_mais_baixado_id, cache_valido_ate)\n                    VALUES (?, ?, ?, ?, ?, ?, ?)\n                ', (cat[0], cat[1], cat[2], cat[3], cat[4], arquivo_top_id, cache_valido_ate))
            logger.info(f'Ô£à {len(categorias)} categorias processadas')
            return
        except Exception as e:
            logger.error(f'ÔØî Erro atualizar categorias: {str(e)}')
    def _atualizar_arquivos_populares(self, cursor):
        try:
            logger.info('­ƒôè Atualizando arquivos populares...')
            cache_valido_ate = datetime.now() + timedelta(minutes=self.cache_timeout_minutos)
            cursor.execute('DELETE FROM cache_arquivos_populares')
            cursor.execute('\n                SELECT id, downloads_count, rating\n                FROM cache_servidor_arquivos\n                ORDER BY downloads_count DESC, rating DESC\n                LIMIT 100\n            ')
            populares = cursor.fetchall()
            for idx, arquivo in enumerate(populares, 1):
                cursor.execute('\n                    INSERT INTO cache_arquivos_populares \n                    (ranking, arquivo_id, downloads_count, rating, cache_valido_ate)\n                    VALUES (?, ?, ?, ?, ?)\n                ', (idx, arquivo[0], arquivo[1], arquivo[2], cache_valido_ate))
            logger.info(f'Ô£à Top {len(populares)} arquivos populares processados')
            return
        except Exception as e:
            logger.error(f'ÔØî Erro atualizar populares: {str(e)}')
    def _calcular_estatisticas(self, cursor):
        try:
            logger.info('­ƒôè Calculando estat├¡sticas gerais...')
            cursor.execute('SELECT COUNT(*) FROM cache_servidor_arquivos')
            total_arquivos = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(DISTINCT marca) FROM cache_servidor_arquivos')
            total_marcas = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(DISTINCT categoria) FROM cache_servidor_arquivos')
            total_categorias = cursor.fetchone()[0]
            cursor.execute('SELECT SUM(downloads_count) FROM cache_servidor_arquivos')
            total_downloads = cursor.fetchone()[0] or 0
            cursor.execute('\n                SELECT SUM(tamanho_arquivo) FROM cache_servidor_arquivos \n                WHERE tamanho_arquivo IS NOT NULL\n            ')
            tamanho_total_bytes = cursor.fetchone()[0] or 0
            tamanho_total_gb = tamanho_total_bytes / 1073741824
            cursor.execute('\n                SELECT id FROM cache_servidor_arquivos \n                ORDER BY downloads_count DESC LIMIT 1\n            ')
            arquivo_mais_baixado = cursor.fetchone()
            arquivo_mais_baixado_id = arquivo_mais_baixado[0] if arquivo_mais_baixado else None
            cursor.execute('\n                SELECT marca FROM cache_marcas_resumo \n                ORDER BY total_downloads DESC LIMIT 1\n            ')
            marca_mais_popular = cursor.fetchone()
            marca_mais_popular = marca_mais_popular[0] if marca_mais_popular else None
            cursor.execute('\n                SELECT categoria FROM cache_categorias \n                ORDER BY total_arquivos DESC LIMIT 1\n            ')
            categoria_mais_popular = cursor.fetchone()
            categoria_mais_popular = categoria_mais_popular[0] if categoria_mais_popular else None
            cursor.execute('DELETE FROM cache_estatisticas')
            cursor.execute('\n                INSERT INTO cache_estatisticas \n                (total_arquivos, total_marcas, total_categorias, total_downloads,\n                 tamanho_total_gb, arquivo_mais_baixado_id, marca_mais_popular, categoria_mais_popular)\n                VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n            ', (total_arquivos, total_marcas, total_categorias, total_downloads, round(tamanho_total_gb, 2), arquivo_mais_baixado_id, marca_mais_popular, categoria_mais_popular))
            logger.info('Ô£à Estat├¡sticas calculadas:')
            logger.info(f'   ­ƒôü {total_arquivos} arquivos')
            logger.info(f'   ­ƒÅó {total_marcas} marcas')
            logger.info(f'   ­ƒôé {total_categorias} categorias')
            logger.info(f'   Ô¼ç´©Å {total_downloads:,} downloads')
            logger.info(f'   ­ƒÆ¥ {tamanho_total_gb:.2f} GB total')
            return
        except Exception as e:
            logger.error(f'ÔØî Erro calcular estat├¡sticas: {str(e)}')
    def mostrar_estatisticas_cache(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                print('\n================================================================================')
                print('­ƒôè ESTAT├ìSTICAS DO SISTEMA')
                print('================================================================================')
                cursor.execute('SELECT * FROM cache_estatisticas ORDER BY id DESC LIMIT 1')
                stats = cursor.fetchone()
                if stats:
                    print('\n­ƒôê ESTAT├ìSTICAS GERAIS:')
                    print(f'   ­ƒôü Total de arquivos: {stats[1]:,}')
                    print(f'   ­ƒÅó Total de marcas: {stats[2]:,}')
                    print(f'   ­ƒôé Total de categorias: {stats[3]:,}')
                    print(f'   Ô¼ç´©Å Total de downloads: {stats[4]:,}')
                    print(f'   ­ƒÆ¥ Tamanho total: {stats[5]:.2f} GB')
                    print(f'   ­ƒÅå Marca mais popular: {stats[7] or 'N/A'}')
                    print(f'   ­ƒôé Categoria mais popular: {stats[8] or 'N/A'}')
                cursor.execute('\n                    SELECT marca, total_arquivos, total_downloads \n                    FROM cache_marcas_resumo \n                    ORDER BY total_arquivos DESC LIMIT 5\n                ')
                top_marcas = cursor.fetchall()
                print('\n­ƒÅå TOP 5 MARCAS:')
                for i, marca in enumerate(top_marcas, 1):
                    print(f'   {i}. {marca[0]}: {marca[1]:,} arquivos, {marca[2]:,} downloads')
                cursor.execute("\n                    SELECT timestamp_fim, duracao_segundos, registros_processados\n                    FROM cache_sync_control \n                    WHERE status = 'concluida'\n                    ORDER BY id DESC LIMIT 1\n                ")
                ultima_sync = cursor.fetchone()
                if ultima_sync:
                    print('\n­ƒöä ├ÜLTIMA SINCRONIZA├ç├âO:')
                    print(f'   ­ƒôà Data: {ultima_sync[0]}')
                    print(f'   ÔÅ▒´©Å Dura├º├úo: {ultima_sync[1]:.2f}s')
                    print(f'   ­ƒôè Registros: {ultima_sync[2]:,}')
                tamanho_mb = Path(self.db_path).stat().st_size / 1048576
                print('\n­ƒÆ¥ SISTEMA DE DADOS:')
                print('   ­ƒôü Status: Operacional')
                print(f'   ­ƒÆ¥ Tamanho: {tamanho_mb:.2f} MB')
                cursor.execute("\n                    SELECT COUNT(*) FROM cache_servidor_arquivos \n                    WHERE cache_valido_ate > datetime('now')\n                ")
                cache_validos = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM cache_servidor_arquivos')
                total_cache = cursor.fetchone()[0]
                print(f'   Ô£à Registros v├ílidos: {cache_validos:,}')
                print(f'   ­ƒôè Total em cache: {total_cache:,}')
                print(f'   ­ƒöÑ Cache hit rate: {cache_validos / total_cache * 100 if total_cache > 0 else 0:.1f}%')
                print('\n================================================================================')
        except Exception as e:
            logger.error(f'ÔØî Erro mostrar estat├¡sticas: {str(e)}')
    def monitorar_performance(self, duracao_minutos=5):
        print(f'\n­ƒöì Iniciando monitoramento por {duracao_minutos} minutos...')
        print('Pressione Ctrl+C para parar\n')
        try:
            inicio = time.time()
            fim = inicio + duracao_minutos * 60
            while time.time() < fim:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM cache_servidor_arquivos')
                    total = cursor.fetchone()[0]
                    cursor.execute("\n                        SELECT COUNT(*) FROM cache_servidor_arquivos \n                        WHERE cache_valido_ate > datetime('now')\n                    ")
                    validos = cursor.fetchone()[0]
                    tamanho_mb = Path(self.db_path).stat().st_size / 1048576
                    agora = datetime.now().strftime('%H:%M:%S')
                    hit_rate = validos / total * 100 if total > 0 else 0
                    print(f'[{agora}] ­ƒôè Total: {total:,} | Ô£à V├ílidos: {validos:,} | ­ƒÄ» Hit Rate: {hit_rate:.1f}% | ­ƒÆ¥ {tamanho_mb:.1f}MB')
                time.sleep(30)
        except KeyboardInterrupt:
            print('\n­ƒøæ Monitoramento interrompido pelo usu├írio')
        except Exception as e:
            logger.error(f'ÔØî Erro no monitoramento: {str(e)}')
def main():
    print('\n­ƒÜÇ SISTEMA DE OTIMIZA├ç├âO DE DADOS')
    print('============================================================')
    try:
        cache = CacheServerArquivos()
        while True:
            print('\n­ƒôï OP├ç├òES DISPON├ìVEIS:')
            print('1. ­ƒö¿ Criar/Atualizar estrutura do cache')
            print('2. ­ƒöä Sincroniza├º├úo inicial completa')
            print('3. ­ƒôè Mostrar estat├¡sticas')
            print('4. ­ƒöì Monitorar performance')
            print('5. ­ƒº¬ Testar consultas')
            print('0. ­ƒÜ¬ Sair')
            opcao = input('\nEscolha uma op├º├úo: ').strip()
            if opcao == '1':
                cache.criar_estrutura_completa()
            elif opcao == '2':
                cache.sincronizar_cache_inicial()
            elif opcao == '3':
                cache.mostrar_estatisticas_cache()
            elif opcao == '4':
                duracao = input('Dura├º├úo do monitoramento em minutos (padr├úo 5): ').strip()
                duracao = int(duracao) if duracao.isdigit() else 5
                cache.monitorar_performance(duracao)
            elif opcao == '5':
                print('­ƒº¬ Fun├º├úo de teste ser├í implementada...')
            else:
                if opcao == '0':
                    print('­ƒæï Saindo...')
                    return
                print('ÔØî Op├º├úo inv├ílida!')
    except KeyboardInterrupt:
        print('\n­ƒæï Script interrompido pelo usu├írio')
    except Exception as e:
        logger.error(f'ÔØî Erro no script principal: {str(e)}')
if __name__ == '__main__':
    main()
# WARNING: Decompyle incomplete
