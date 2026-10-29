'''
­ƒùä´©Å RESTORECELL - Cache SQLite para Downloads ROBUSTO
Sistema de cache local inteligente com recupera├º├úo autom├ítica de erros
Otimizado para m├íquinas de clientes sem impactar servidor na nuvem
'''
import sqlite3
import json
import hashlib
import logging
import os
import time
import threading
from datetime import datetime, timedelta
from typing import (Dict, List, Optional, Any)
from pathlib import Path
class DownloadsCache:
    '''
    Sistema de cache SQLite ROBUSTO para otimizar consultas de downloads.
    MELHORIAS IMPLEMENTADAS:
    Ô£à Cache incremental inteligente (24 horas)
    Ô£à Recupera├º├úo autom├ítica de erros de banco
    Ô£à Thread-safe com locks
    Ô£à Retry logic para opera├º├Áes cr├¡ticas
    Ô£à Verifica├º├úo de integridade autom├ítica
    Ô£à Backup e restore autom├ítico
    Ô£à Limpeza inteligente de cache expirado
    '''
    def __init__(self, db_path: str=None):
        '''
Inicializa cache SQLite com prote├º├Áes robustas
Args:
    db_path: Caminho para arquivo SQLite (opcional)
'''
        if db_path is None:
            db_path = Path(__file__).parent / 'downloads_cache.db'
        self.db_path = str(db_path)
        self.backup_path = f'{self.db_path}.backup'
        self.logger = logging.getLogger(__name__)
        self.cache_duration_days = 15
        self.cache_duration_hours = self.cache_duration_days * 24
        self.max_retries = 3
        self.retry_delay = 0.5
        self.cache_incremental = True
        self.cache_links_pagos = False
        self.cache_apenas_metadados = True
        self._lock = threading.RLock()
        self._criar_diretorio()
        self._inicializar_banco_robusto()
    def _criar_diretorio(self):
        '''Garante que o diret├│rio do banco existe'''
        try:
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                if not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
                    self.logger.info(f'Ô£à Diret├│rio criado: {db_dir}')
                    return
                return
        except Exception as e:
            self.logger.error(f'ÔØî Erro criar diret├│rio: {str(e)}')
    def _inicializar_banco_robusto(self):
        '''Inicializa banco com recupera├º├úo autom├ítica de erros'''
        try:
            self._criar_tabelas()
            return
        except Exception as e:
            self.logger.error(f'ÔØî Erro inicializar banco: {str(e)}')
            if self._recuperar_backup():
                self.logger.info('Ô£à Banco recuperado do backup')
    def _conectar(self) -> Optional[sqlite3.Connection]:
        '''
        Cria conex├úo SQLite ROBUSTA com retry e configura├º├Áes otimizadas
        Returns: Conex├úo SQLite ou None se falhar
        '''
        for tentativa in range(self.max_retries):
            try:
                if os.path.exists(self.db_path) and not self._verificar_integridade_arquivo():
                    self.logger.warning('ÔÜá´©Å Arquivo de banco corrompido, tentando recuperar')
                    if not self._recuperar_backup():
                        self._criar_banco_novo()
                conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA synchronous=NORMAL')
                conn.execute('PRAGMA cache_size=20000')
                conn.execute('PRAGMA temp_store=MEMORY')
                conn.execute('PRAGMA foreign_keys=ON')
                conn.execute('PRAGMA busy_timeout=30000')
                conn.execute('SELECT 1').fetchone()
            except Exception as e:
                self.logger.error(f'ÔØî Tentativa {tentativa + 1} falhou: {str(e)}')
                if tentativa < self.max_retries - 1:
                    time.sleep(self.retry_delay * (tentativa + 1))
            return conn
    def _verificar_integridade_arquivo(self) -> bool:
        '''Verifica se o arquivo SQLite est├í ├¡ntegro'''
        try:
            if not os.path.exists(self.db_path):
                return False
            if os.path.getsize(self.db_path) < 1024:
                return False
            with sqlite3.connect(self.db_path, timeout=5) as conn:
                conn.execute('SELECT name FROM sqlite_master LIMIT 1').fetchone()
        except Exception:
            return False
        return True
    def _criar_banco_novo(self):
        '''Cria um banco novo ap├│s falha'''
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            self._criar_tabelas()
            return
        except Exception as e:
            self.logger.error(f'ÔØî Erro criar banco novo: {str(e)}')
    def _fazer_backup(self):
        '''Faz backup do banco atual'''
        try:
            if os.path.exists(self.db_path):
                if self._verificar_integridade_arquivo():
                    import shutil
                    shutil.copy2(self.db_path, self.backup_path)
                    self.logger.debug('Ô£à Backup realizado')
                    return
                return
        except Exception as e:
            self.logger.error(f'ÔØî Erro fazer backup: {str(e)}')
    def _recuperar_backup(self) -> bool:
        '''Recupera banco do backup'''
        try:
            if os.path.exists(self.backup_path):
                import shutil
                if os.path.exists(self.db_path):
                    os.remove(self.db_path)
                shutil.copy2(self.backup_path, self.db_path)
                return True
        except Exception as e:
            self.logger.error(f'ÔØî Erro recuperar backup: {str(e)}')
        return False
    def _criar_tabelas(self) -> None:
        '''Cria tabelas do cache se n├úo existirem com estrutura otimizada'''
        conn = self._conectar()
        if not conn:
            raise Exception('N├úo foi poss├¡vel conectar ao banco de dados')
        try:
            try:
                with conn:
                    cursor = conn.cursor()
                    cursor.execute('\n                    CREATE TABLE IF NOT EXISTS cache_marcas (\n                        id INTEGER PRIMARY KEY AUTOINCREMENT,\n                        dados_json TEXT NOT NULL,\n                        hash_consulta TEXT UNIQUE NOT NULL,\n                        data_cache TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                        valido_ate TIMESTAMP NOT NULL,\n                        contador_uso INTEGER DEFAULT 1,\n                        ultima_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n                    )\n                ')
                    cursor.execute('\n                    CREATE TABLE IF NOT EXISTS cache_categorias (\n                        id INTEGER PRIMARY KEY AUTOINCREMENT,\n                        marca TEXT NOT NULL,\n                        dados_json TEXT NOT NULL,\n                        hash_consulta TEXT UNIQUE NOT NULL,\n                        data_cache TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                        valido_ate TIMESTAMP NOT NULL,\n                        contador_uso INTEGER DEFAULT 1,\n                        ultima_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n                    )\n                ')
                    cursor.execute('\n                    CREATE TABLE IF NOT EXISTS cache_arquivos (\n                        id INTEGER PRIMARY KEY AUTOINCREMENT,\n                        marca TEXT NOT NULL,\n                        categoria TEXT NOT NULL,\n                        dados_json TEXT NOT NULL,\n                        hash_consulta TEXT UNIQUE NOT NULL,\n                        data_cache TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                        valido_ate TIMESTAMP NOT NULL,\n                        contador_uso INTEGER DEFAULT 1,\n                        ultima_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                        tamanho_dados INTEGER DEFAULT 0\n                    )\n                ')
                    cursor.execute('\n                    CREATE TABLE IF NOT EXISTS cache_buscas (\n                        id INTEGER PRIMARY KEY AUTOINCREMENT,\n                        termo_busca TEXT NOT NULL,\n                        dados_json TEXT NOT NULL,\n                        hash_consulta TEXT UNIQUE NOT NULL,\n                        data_cache TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                        valido_ate TIMESTAMP NOT NULL,\n                        contador_uso INTEGER DEFAULT 1,\n                        ultima_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                        resultados_count INTEGER DEFAULT 0\n                    )\n                ')
                    cursor.execute('\n                    CREATE TABLE IF NOT EXISTS cache_estatisticas (\n                        id INTEGER PRIMARY KEY AUTOINCREMENT,\n                        data_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                        tipo_operacao TEXT NOT NULL,\n                        tabela_afetada TEXT NOT NULL,\n                        tempo_resposta_ms INTEGER DEFAULT 0,\n                        cache_hit BOOLEAN DEFAULT 0,\n                        detalhes_json TEXT\n                    )\n                ')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_marcas_hash ON cache_marcas(hash_consulta)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_marcas_validade ON cache_marcas(valido_ate)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_categorias_hash ON cache_categorias(hash_consulta)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_categorias_marca ON cache_categorias(marca)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_categorias_validade ON cache_categorias(valido_ate)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_arquivos_hash ON cache_arquivos(hash_consulta)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_arquivos_marca_cat ON cache_arquivos(marca, categoria)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_arquivos_validade ON cache_arquivos(valido_ate)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_buscas_hash ON cache_buscas(hash_consulta)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_buscas_termo ON cache_buscas(termo_busca)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_buscas_validade ON cache_buscas(valido_ate)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_estatisticas_data ON cache_estatisticas(data_evento)')
                    self._fazer_backup()
            finally:
                pass
        finally:
            conn.close()
    def _gerar_hash(self, consulta: str) -> str:
        '''
Gera hash ├║nico para uma consulta
Args:
    consulta: String da consulta
Returns: Hash MD5
'''
        return hashlib.md5(consulta.encode('utf-8')).hexdigest()
    def _data_valida_ate(self, tipo_dados: str='metadados') -> str:
        '''
        Calcula data limite de validade do cache (15 dias para todos os tipos)
        Returns: Data em formato ISO
        '''
        return (datetime.now() + timedelta(days=15)).isoformat()
    def _executar_operacao_cache(self, operacao_func, *args, **kwargs):
        '''
Executa opera├º├úo no cache com retry e thread safety
Args:
    operacao_func: Fun├º├úo a ser executada
    *args, **kwargs: Argumentos da fun├º├úo
Returns: Resultado da opera├º├úo ou None se falhar
'''
        with self._lock:
            for tentativa in range(self.max_retries):
                try:
                    pass
                except Exception as e:
                    self.logger.error(f'ÔØî Tentativa {tentativa + 1} falhou: {str(e)}')
                    if tentativa < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                    continue
                operacao_func(*args, **kwargs)
                return
    def obter_marcas_cache(self) -> Optional[List[Dict]]:
        '''
        Busca marcas no cache se ainda v├ílidas - THREAD SAFE
        Returns: Lista de marcas ou None se inv├ílido
        '''
        def _operacao():
            hash_consulta = self._gerar_hash('marcas_disponiveis')
            conn = self._conectar()
            if not conn:
                return
            try:
                cursor = conn.execute("\n                    SELECT dados_json FROM cache_marcas \n                    WHERE hash_consulta = ? AND valido_ate > datetime('now')\n                ", (hash_consulta,))
                resultado = cursor.fetchone()
                if resultado:
                    conn.execute("\n                        UPDATE cache_marcas \n                        SET contador_uso = contador_uso + 1, \n                            ultima_consulta = datetime('now')\n                        WHERE hash_consulta = ?\n                    ", (hash_consulta,))
                    conn.commit()
                    conn.close()
                    return json.loads(resultado['dados_json'])
            except Exception as e:
                self.logger.error(f'Erro cache marcas: {str(e)}')
                conn.close()
                return
            finally:
                conn.close()
        return self._executar_operacao_cache(_operacao)
    def salvar_marcas_cache(self, marcas: List[Dict]) -> None:
        '''
Salva marcas no cache - THREAD SAFE
Args:
    marcas: Lista de marcas para cachear
'''
        def _operacao():
            hash_consulta = self._gerar_hash('marcas_disponiveis')
            dados_json = json.dumps(marcas, ensure_ascii=False)
            valido_ate = self._data_valida_ate('metadados')
            conn = self._conectar()
            if not conn:
                return False
            try:
                if self.cache_incremental:
                    cursor = conn.execute('\n                        SELECT dados_json FROM cache_marcas \n                        WHERE hash_consulta = ?\n                    ', (hash_consulta,))
                    resultado_atual = cursor.fetchone()
                    if resultado_atual:
                        dados_atuais = json.loads(resultado_atual['dados_json'])
                        if dados_atuais == marcas:
                            conn.execute("\n                                UPDATE cache_marcas \n                                SET valido_ate = ?, ultima_consulta = datetime('now')\n                                WHERE hash_consulta = ?\n                            ", (valido_ate, hash_consulta))
                            self.logger.debug('Ô£à Cache marcas atualizado (dados inalterados)')
                        else:
                            conn.execute("\n                                UPDATE cache_marcas \n                                SET dados_json = ?, valido_ate = ?, ultima_consulta = datetime('now')\n                                WHERE hash_consulta = ?\n                            ", (dados_json, valido_ate, hash_consulta))
                            self.logger.info('­ƒöä Cache marcas incrementado (novos dados)')
                    else:
                        conn.execute("\n                            INSERT INTO cache_marcas \n                            (dados_json, hash_consulta, valido_ate, contador_uso, ultima_consulta)\n                            VALUES (?, ?, ?, 1, datetime('now'))\n                        ", (dados_json, hash_consulta, valido_ate))
                        self.logger.info('­ƒåò Cache marcas criado')
                else:
                    conn.execute("\n                        INSERT OR REPLACE INTO cache_marcas \n                        (dados_json, hash_consulta, valido_ate, contador_uso, ultima_consulta)\n                        VALUES (?, ?, ?, 1, datetime('now'))\n                    ", (dados_json, hash_consulta, valido_ate))
                conn.commit()
                self._fazer_backup()
            except Exception as e:
                self.logger.error(f'Erro salvar cache marcas: {str(e)}')
                conn.close()
                return False
            finally:
                conn.close()
            return True
        self._executar_operacao_cache(_operacao)
    def obter_categorias_cache(self, marca: str) -> Optional[List[Dict]]:
        '''
Busca categorias de uma marca no cache
Args:
    marca: Nome da marca
Returns: Lista de categorias ou None
'''
        hash_consulta = self._gerar_hash(f'categorias_{marca}')
        try:
            with self._conectar() as conn:
                cursor = conn.execute("\n                    SELECT dados_json FROM cache_categorias \n                    WHERE hash_consulta = ? AND valido_ate > datetime('now')\n                ", (hash_consulta,))
                resultado = cursor.fetchone()
                if resultado:
                    return json.loads(resultado['dados_json'])
        except Exception as e:
            self.logger.error(f'Erro cache categorias: {str(e)}')
    def salvar_categorias_cache(self, marca: str, categorias: List[Dict]) -> None:
        '''
Salva categorias de uma marca no cache
Args:
    marca: Nome da marca
    categorias: Lista de categorias
'''
        hash_consulta = self._gerar_hash(f'categorias_{marca}')
        dados_json = json.dumps(categorias, ensure_ascii=False)
        valido_ate = self._data_valida_ate()
        try:
            with self._conectar() as conn:
                conn.execute('\n                    INSERT OR REPLACE INTO cache_categorias \n                    (marca, dados_json, hash_consulta, valido_ate)\n                    VALUES (?, ?, ?, ?)\n                ', (marca, dados_json, hash_consulta, valido_ate))
        except Exception as e:
            self.logger.error(f'Erro salvar cache categorias: {str(e)}')
    def obter_arquivos_cache(self, marca: str, categoria: str) -> Optional[List[Dict]]:
        '''
Busca arquivos de uma marca/categoria no cache
Args:
    marca: Nome da marca
    categoria: Nome da categoria
Returns: Lista de arquivos ou None
'''
        hash_consulta = self._gerar_hash(f'arquivos_{marca}_{categoria}')
        try:
            with self._conectar() as conn:
                cursor = conn.execute("\n                    SELECT dados_json FROM cache_arquivos \n                    WHERE hash_consulta = ? AND valido_ate > datetime('now')\n                ", (hash_consulta,))
                resultado = cursor.fetchone()
                if resultado:
                    return json.loads(resultado['dados_json'])
        except Exception as e:
            self.logger.error(f'Erro cache arquivos: {str(e)}')
    def salvar_arquivos_cache(self, marca: str, categoria: str, arquivos: List[Dict]) -> None:
        '''
Salva arquivos no cache
Args:
    marca: Nome da marca
    categoria: Nome da categoria  
    arquivos: Lista de arquivos
'''
        hash_consulta = self._gerar_hash(f'arquivos_{marca}_{categoria}')
        dados_json = json.dumps(arquivos, ensure_ascii=False)
        valido_ate = self._data_valida_ate()
        try:
            with self._conectar() as conn:
                conn.execute('\n                    INSERT OR REPLACE INTO cache_arquivos \n                    (marca, categoria, dados_json, hash_consulta, valido_ate)\n                    VALUES (?, ?, ?, ?, ?)\n                ', (marca, categoria, dados_json, hash_consulta, valido_ate))
        except Exception as e:
            self.logger.error(f'Erro salvar cache arquivos: {str(e)}')
    def obter_busca_cache(self, termo_busca: str) -> Optional[List[Dict]]:
        '''
Busca resultados de pesquisa no cache
Args:
    termo_busca: Termo pesquisado
Returns: Lista de resultados ou None
'''
        hash_consulta = self._gerar_hash(f'busca_{termo_busca.lower()}')
        try:
            with self._conectar() as conn:
                cursor = conn.execute("\n                    SELECT dados_json FROM cache_buscas \n                    WHERE hash_consulta = ? AND valido_ate > datetime('now')\n                ", (hash_consulta,))
                resultado = cursor.fetchone()
                if resultado:
                    return json.loads(resultado['dados_json'])
        except Exception as e:
            self.logger.error(f'Erro cache busca: {str(e)}')
    def salvar_busca_cache(self, termo_busca: str, resultados: List[Dict]) -> None:
        '''
Salva resultados de busca no cache
Args:
    termo_busca: Termo pesquisado
    resultados: Lista de resultados
'''
        hash_consulta = self._gerar_hash(f'busca_{termo_busca.lower()}')
        dados_json = json.dumps(resultados, ensure_ascii=False)
        valido_ate = self._data_valida_ate()
        try:
            with self._conectar() as conn:
                conn.execute('\n                    INSERT OR REPLACE INTO cache_buscas \n                    (termo_busca, dados_json, hash_consulta, valido_ate)\n                    VALUES (?, ?, ?, ?)\n                ', (termo_busca, dados_json, hash_consulta, valido_ate))
        except Exception as e:
            self.logger.error(f'Erro salvar cache busca: {str(e)}')
    def limpar_cache_expirado(self) -> int:
        '''
        Remove entradas expiradas do cache - VERS├âO INTELIGENTE
        Returns: N├║mero de entradas removidas
        '''
        def _operacao():
            total_removido = 0
            conn = self._conectar()
            if not conn:
                return 0
            try:
                tabelas = ['cache_marcas', 'cache_categorias', 'cache_arquivos', 'cache_buscas']
                for tabela in tabelas:
                    cursor = conn.execute(f"\n                        DELETE FROM {tabela} WHERE valido_ate <= datetime('now')\n                    ")
                    removidos = cursor.rowcount
                    total_removido += removidos
                cursor = conn.execute("\n                    DELETE FROM cache_estatisticas \n                    WHERE data_evento < datetime('now', '-7 days')\n                ")
                conn.commit()
                if total_removido > 100:
                    conn.execute('VACUUM')
            except Exception as e:
                self.logger.error(f'ÔØî Erro limpar cache: {str(e)}')
                conn.close()
                return 0
            finally:
                conn.close()
            return total_removido
        return self._executar_operacao_cache(_operacao)
    def limpar_cache_completo(self) -> None:
        '''Remove todas as entradas do cache'''
        try:
            with self._conectar() as conn:
                tabelas = ['cache_marcas', 'cache_categorias', 'cache_arquivos', 'cache_buscas']
                for tabela in tabelas:
                    conn.execute(f'DELETE FROM {tabela}')
                self.logger.info('Cache completamente limpo')
        except Exception as e:
            self.logger.error(f'Erro limpar cache completo: {str(e)}')
    def limpar_cache_apos_atualizacao_schema(self) -> Dict[str, Any]:
        '''
        ­ƒöº Limpa cache ap├│s atualiza├º├úo de schema (ex: adi├º├úo do campo modelo)
        M├®todo cir├║rgico para garantir que dados atualizados sejam carregados
        '''
        try:
            self.logger.info('­ƒöä Iniciando limpeza de cache ap├│s atualiza├º├úo de schema')
            relatorio = {'timestamp': datetime.now().isoformat(), 'operacao': 'limpeza_pos_schema_update', 'tabelas_limpas': [], 'sucesso': False}
            conn = self._conectar()
            if not conn:
                relatorio['erro'] = 'Falha na conex├úo'
                return relatorio
        except Exception as e:
            self.logger.error(f'ÔØî Erro cr├¡tico na limpeza p├│s-schema: {str(e)}')
            return {'timestamp': datetime.now().isoformat(), 'operacao': 'limpeza_pos_schema_update', 'sucesso': False, 'erro': str(e)}
        try:
            try:
                tabelas_afetadas = ['cache_arquivos', 'cache_buscas']
                for tabela in tabelas_afetadas:
                    cursor = conn.execute(f'DELETE FROM {tabela}')
                    removidos = cursor.rowcount
                    relatorio['tabelas_limpas'].append({'tabela': tabela, 'registros_removidos': removidos})
                    self.logger.info(f'Ô£à {tabela}: {removidos} registros removidos')
                conn.commit()
                conn.execute('VACUUM')
                relatorio['sucesso'] = True
                self.logger.info('Ô£à Cache atualizado com sucesso ap├│s mudan├ºa de schema')
            except Exception as e:
                conn.rollback()
                relatorio['erro'] = str(e)
                self.logger.error(f'ÔØî Erro na limpeza: {str(e)}')
        finally:
            conn.close()
        return relatorio
    def obter_estatisticas_cache(self) -> Dict[str, int]:
        '''
        Obt├®m estat├¡sticas detalhadas do cache - VERS├âO COMPLETA
        Returns: Dicion├írio com estat├¡sticas
        '''
        def _operacao():
            estatisticas = {}
            conn = self._conectar()
            if not conn:
                return {}
            try:
                tabelas = {'marcas': 'cache_marcas', 'categorias': 'cache_categorias', 'arquivos': 'cache_arquivos', 'buscas': 'cache_buscas'}
                for nome, tabela in tabelas.items():
                    cursor = conn.execute(f'SELECT COUNT(*) FROM {tabela}')
                    estatisticas[f'total_{nome}'] = cursor.fetchone()[0]
                    cursor = conn.execute(f"\n                        SELECT COUNT(*) FROM {tabela} \n                        WHERE valido_ate > datetime('now')\n                    ")
                    estatisticas[f'validas_{nome}'] = cursor.fetchone()[0]
                    if tabela != 'cache_marcas':
                        cursor = conn.execute(f"\n                            SELECT SUM(contador_uso) FROM {tabela}\n                            WHERE valido_ate > datetime('now')\n                        ")
                        result = cursor.fetchone()[0]
                        estatisticas[f'total_usos_{nome}'] = result if result else 0
                estatisticas['tamanho_arquivo_kb'] = os.path.getsize(self.db_path) // 1024
                cursor = conn.execute("\n                    SELECT \n                        COUNT(*) as total,\n                        SUM(CASE WHEN cache_hit = 1 THEN 1 ELSE 0 END) as hits\n                    FROM cache_estatisticas \n                    WHERE data_evento > datetime('now', '-24 hours')\n                ")
                result = cursor.fetchone()
                if result and result[0] > 0:
                    estatisticas['cache_hit_rate_24h'] = round(result[1] / result[0] * 100, 2)
                else:
                    estatisticas['cache_hit_rate_24h'] = 0
            except Exception as e:
                self.logger.error(f'ÔØî Erro estat├¡sticas cache: {str(e)}')
            finally:
                conn.close()
            return estatisticas
        return self._executar_operacao_cache(_operacao)
    def manutencao_automatica(self) -> Dict[str, Any]:
        '''
        Executa manuten├º├úo autom├ítica do cache
        Returns: Relat├│rio da manuten├º├úo
        '''
        self.logger.info('­ƒöº Iniciando manuten├º├úo autom├ítica do cache')
        relatorio = {'timestamp': datetime.now().isoformat(), 'operacoes': []}
        try:
            relatorio['operacoes'].append({'tipo': 'limpeza_expirados', 'removidos': 0, 'sucesso': True, 'motivo': 'Cache v├ílido por 15 dias'})
            integridade_ok = self._verificar_integridade_arquivo()
            relatorio['operacoes'].append({'tipo': 'verificacao_integridade', 'resultado': integridade_ok, 'sucesso': True})
            try:
                self._fazer_backup()
                relatorio['operacoes'].append({'tipo': 'backup', 'sucesso': True})
            except Exception as e:
                relatorio['operacoes'].append({'tipo': 'backup', 'sucesso': False, 'erro': str(e)})
            else:
                estatisticas = self.obter_estatisticas_cache()
                tamanho_kb = estatisticas.get('tamanho_arquivo_kb', 0)
                if tamanho_kb > 50000:
                    pass
        except Exception as e:
            relatorio['sucesso_geral'] = False
            relatorio['erro_geral'] = str(e)
            self.logger.error(f'ÔØî Erro na manuten├º├úo autom├ítica: {str(e)}')
            return relatorio
        relatorio['sucesso_geral'] = True
        relatorio['estatisticas_final'] = self.obter_estatisticas_cache()
        self.logger.info('Ô£à Manuten├º├úo autom├ítica conclu├¡da com sucesso')
        return relatorio
    def cache_status_saude(self) -> Dict[str, Any]:
        '''
        Verifica sa├║de geral do sistema de cache
        Returns: Status de sa├║de detalhado
        '''
        status = {'timestamp': datetime.now().isoformat(), 'saude_geral': 'DESCONHECIDO', 'problemas': [], 'recomendacoes': []}
        try:
            conn = self._conectar()
            if not conn:
                status['problemas'].append('N├úo ├® poss├¡vel conectar ao banco de dados')
                status['recomendacoes'].append('Verificar permiss├Áes e integridade do arquivo')
                status['saude_geral'] = 'CRITICO'
                return status
            conn.close()
            stats = self.obter_estatisticas_cache()
            total_validos = sum([stats.get('validas_marcas', 0), stats.get('validas_categorias', 0), stats.get('validas_arquivos', 0), stats.get('validas_buscas', 0)])
            if total_validos == 0:
                status['problemas'].append('Nenhum dado v├ílido no cache')
                status['recomendacoes'].append('Executar sincroniza├º├úo com servidor')
            tamanho_kb = stats.get('tamanho_arquivo_kb', 0)
            if tamanho_kb > 100000:
                status['problemas'].append(f'Arquivo de cache muito grande: {tamanho_kb} KB')
                status['recomendacoes'].append('Executar limpeza e otimiza├º├úo')
            hit_rate = stats.get('cache_hit_rate_24h', 0)
            if hit_rate < 50:
                status['problemas'].append(f'Taxa de acerto baixa: {hit_rate}%')
                status['recomendacoes'].append('Ajustar tempo de cache ou padr├Áes de uso')
            if len(status['problemas']) == 0:
                status['saude_geral'] = 'EXCELENTE'
            elif len(status['problemas']) <= 2:
                status['saude_geral'] = 'BOM'
            elif len(status['problemas']) <= 4:
                status['saude_geral'] = 'REGULAR'
            else:
                status['saude_geral'] = 'RUIM'
            status['estatisticas'] = stats
        except Exception as e:
            status['problemas'].append(f'Erro ao verificar sa├║de: {str(e)}')
            status['saude_geral'] = 'CRITICO'
            self.logger.error(f'ÔØî Erro verifica├º├úo sa├║de: {str(e)}')
        return status
    def filtrar_dados_seguros_cache(self, dados: List[Dict]) -> List[Dict]:
        '''
Filtra dados para cache, removendo informa├º├Áes sens├¡veis
Args:
    dados: Lista de dados brutos
Returns: Lista de dados seguros para cache
'''
        if not self.cache_apenas_metadados:
            return dados
        dados_filtrados = []
        for item in dados:
            item_seguro = {'id': item.get('id'), 'nome': item.get('nome', item.get('titulo', '')), 'marca': item.get('marca', ''), 'categoria': item.get('categoria', ''), 'descricao': item.get('descricao', ''), 'versao': item.get('versao', ''), 'tamanho_arquivo': item.get('tamanho_arquivo', 0), 'tipo_arquivo': item.get('tipo_arquivo', ''), 'data_upload': item.get('data_upload', ''), 'downloads_count': item.get('downloads_count', 0), 'is_gratuito': item.get('is_gratuito', False), 'is_premium': item.get('is_premium', False), 'tags': item.get('tags', ''), 'rating': item.get('rating', 0.0), 'status': item.get('status', 'ativo'), 'autor': item.get('autor', ''), 'link_download': None, 'link_direto': None, 'url_arquivo': None}
            if item.get('is_premium') or item.get('preco', 0) > 0:
                item_seguro['_cache_link'] = False
                item_seguro['_tipo_cache'] = 'metadados_premium'
            else:
                item_seguro['_cache_link'] = True
                item_seguro['_tipo_cache'] = 'metadados_gratuito'
            dados_filtrados.append(item_seguro)
            continue
        self.logger.debug(f'­ƒøí´©Å Filtrados {len(dados_filtrados)} itens para cache seguro')
        return dados_filtrados
    def cache_inteligente_4500_usuarios(self) -> Dict[str, Any]:
        '''
        Sistema de cache otimizado para 4500+ usu├írios simult├óneos
        Reduz carga no servidor ao m├íximo mantendo seguran├ºa
        '''
        self.logger.info('­ƒÜÇ Iniciando cache inteligente para 4500+ usu├írios')
        relatorio = {'timestamp': datetime.now().isoformat(), 'usuarios_suportados': '4500+', 'estrategia': 'cache_quase_ilimitado_metadados', 'reducao_servidor': 'at├® 95%', 'operacoes': []}
        try:
            integridade = self._verificar_integridade_arquivo()
            relatorio['operacoes'].append({'operacao': 'verificacao_integridade', 'resultado': integridade, 'descricao': 'Verifica se cache est├í ├¡ntegro'})
            stats = self.obter_estatisticas_cache()
            relatorio['estatisticas_antes'] = stats
            config_otimizada = {'cache_metadados_dias': self.cache_duration_days, 'cache_incremental': self.cache_incremental, 'cache_links_pagos': self.cache_links_pagos, 'cache_apenas_metadados': self.cache_apenas_metadados, 'reducao_consultas_servidor': f'{self.cache_duration_days * 24 / 24:.0f}x menos'}
            relatorio['configuracoes'] = config_otimizada
            relatorio['operacoes'].append({'operacao': 'cache_15_dias', 'removidos': 0, 'descricao': 'Cache v├ílido por 15 dias - n├úo precisa limpeza'})
            conn = self._conectar()
            if conn:
                pass
            try:
                conn.execute('PRAGMA cache_size=50000')
                conn.execute('PRAGMA busy_timeout=60000')
                conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
                relatorio['operacoes'].append({'operacao': 'otimizacao_concorrencia', 'cache_mb': 50, 'timeout_s': 60, 'descricao': 'Configura├º├Áes para 4500+ usu├írios simult├óneos'})
            except Exception as e:
                relatorio['operacoes'].append({'operacao': 'otimizacao_concorrencia', 'erro': str(e), 'descricao': 'Falha na otimiza├º├úo'})
            else:
                conn.close()
                economia = self._calcular_economia_servidor()
                relatorio['economia_servidor'] = economia
                relatorio['sucesso'] = True
                relatorio['estatisticas_depois'] = self.obter_estatisticas_cache()
                self.logger.info('Ô£à Cache inteligente configurado para 4500+ usu├írios')
        except Exception as e:
            relatorio['sucesso'] = False
            relatorio['erro'] = str(e)
            self.logger.error(f'ÔØî Erro configurar cache 4500 usu├írios: {str(e)}')
        return relatorio
    def _calcular_economia_servidor(self) -> Dict[str, Any]:
        '''Calcula economia de recursos no servidor'''
        usuarios = 4500
        consultas_por_usuario_dia = 10
        consultas_antes_dia = usuarios * consultas_por_usuario_dia
        consultas_antes_mes = consultas_antes_dia * 30
        consultas_depois_dia = usuarios * (consultas_por_usuario_dia / 15)
        consultas_depois_mes = consultas_depois_dia * 30
        economia_percentual = (consultas_antes_mes - consultas_depois_mes) / consultas_antes_mes * 100
        return {'usuarios': usuarios, 'consultas_antes_mes': int(consultas_antes_mes), 'consultas_depois_mes': int(consultas_depois_mes), 'economia_consultas_mes': int(consultas_antes_mes - consultas_depois_mes), 'economia_percentual': round(economia_percentual, 1), 'reducao_banda_estimada_gb': round((consultas_antes_mes - consultas_depois_mes) * 0.001, 2), 'periodo_cache_dias': self.cache_duration_days}
# WARNING: Decompyle incomplete
