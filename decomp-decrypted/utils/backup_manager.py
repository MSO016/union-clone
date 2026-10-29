import os
import sqlite3
import zipfile
import logging
from datetime import datetime
from PyQt5.QtWidgets import (QMessageBox, QFileDialog, QProgressDialog, QApplication)
from PyQt5.QtCore import Qt, QStandardPaths
from app.utils.path_manager import PathManager
from app.utils._app_cfg import db_config
_logger = logging.getLogger(__name__)
_ERROR_CODES = {'BR-001': 'Backup restaurado, mas alguns dados podem precisar de revis├úo.\nContate o suporte: BR-001', 'BR-002': 'Servidor temporariamente indispon├¡vel.\nRestaura├º├úo conclu├¡da em modo local: BR-002', 'BR-003': 'Backup parece pertencer a outra conta.\nContate o suporte: BR-003', 'BR-004': 'Restaura├º├úo conclu├¡da com sucesso.\nReinicie o aplicativo para aplicar.', 'BR-005': 'Pasta de destino indispon├¡vel.\nUsando local padr├úo: BR-005', 'BR-006': 'Arquivo de backup incompat├¡vel.\nContate o suporte: BR-006'}
def _registrar_evento_backup(codigo, detalhe=''):
    try:
        msg = f'[backup_manager] {codigo}'
        if detalhe:
            msg = f'{msg} | {detalhe}'
        _logger.warning(msg)
        return
    except Exception:
        return
class BackupManager:
    @staticmethod
    def _get_documentos_path():
        return PathManager.get_user_documents_dir()
    @staticmethod
    def criar_backup(parent=None):
        try:
            db_path = PathManager.get_database_path('service_orders.db')
            if not os.path.exists(db_path):
                QMessageBox.warning(parent, 'Aviso', 'Banco de dados n├úo encontrado!')
                return False
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'backup_os_{timestamp}.zip'
            docs_path = PathManager.get_user_documents_dir('UNION_OS/Backups')
            default_path = os.path.join(docs_path, backup_filename)
            save_path, _ = QFileDialog.getSaveFileName(parent, 'Salvar Backup', default_path, 'Arquivos ZIP (*.zip)')
            if not save_path:
                return False
            progress = QProgressDialog('Criando backup...', 'Cancelar', 0, 100, parent)
            progress.setWindowTitle('Backup em Progresso')
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            QApplication.processEvents()
            progress.setValue(20)
            QApplication.processEvents()
            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                progress.setValue(40)
                QApplication.processEvents()
                zipf.write(db_path, 'service_orders.db')
                progress.setValue(60)
                QApplication.processEvents()
                backup_info = f'BACKUP UNION - ORDENS DE SERVI├çO\nData: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\nArquivo: service_orders.db\nVers├úo: 1.3\nSistema: UNION Solutions\n'
                zipf.writestr('backup_info.txt', backup_info)
                progress.setValue(80)
                QApplication.processEvents()
            progress.setValue(100)
            progress.close()
            file_size = os.path.getsize(save_path) / 1024
            QMessageBox.information(parent, 'Backup Conclu├¡do', f'Backup criado com sucesso!\n\nArquivo: {os.path.basename(save_path)}\nTamanho: {file_size:.1f} KB\nLocal: {save_path}')
        except Exception as e:
            QMessageBox.critical(parent, 'Erro', f'Erro ao criar backup:\n{str(e)}')
            return False
        return True
    @staticmethod
    def criar_backup_automatico(db_path=None, prefixo='backup'):
        try:
            if not db_path:
                db_path = PathManager.get_database_path('service_orders.db')
            if not db_path or not os.path.exists(db_path):
                _registrar_evento_backup('BR-AUTO', 'banco inexistente p/ backup automatico')
                return
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'{prefixo}_{timestamp}.zip'
            docs_path = PathManager.get_user_documents_dir('UNION_OS/Backups')
            save_path = os.path.join(docs_path, backup_filename)
            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(db_path, 'service_orders.db')
                backup_info = f'BACKUP AUTOMATICO UNION - ORDENS DE SERVICO\nData: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\nOrigem: backup de seguranca anterior a uma operacao destrutiva\nArquivo: service_orders.db\nSistema: UNION Solutions\n'
                zipf.writestr('backup_info.txt', backup_info)
            if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                _registrar_evento_backup('BR-AUTO', 'backup automatico OK')
                return save_path
        except Exception as exc:
            _registrar_evento_backup('BR-AUTO', f'falha: {type(exc).__name__}')
    @staticmethod
    def restaurar_backup(parent=None):
        try:
            docs_path = PathManager.get_user_documents_dir('UNION_OS/Backups')
            backup_path, _ = QFileDialog.getOpenFileName(parent, 'Selecionar Backup', docs_path, 'Arquivos ZIP (*.zip)')
            if not backup_path:
                return False
            reply = QMessageBox.question(parent, 'Confirmar Restaura├º├úo', 'ÔÜá´©Å ATEN├ç├âO ÔÜá´©Å\n\nEsta opera├º├úo ir├í substituir completamente o banco de dados atual!\nTodas as ordens de servi├ºo atuais ser├úo perdidas.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return False
            progress = QProgressDialog('Restaurando backup...', 'Cancelar', 0, 100, parent)
            progress.setWindowTitle('Restaura├º├úo em Progresso')
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            QApplication.processEvents()
            if not zipfile.is_zipfile(backup_path):
                QMessageBox.warning(parent, 'Erro', 'Arquivo de backup inv├ílido!')
                progress.close()
                return False
            progress.setValue(20)
            QApplication.processEvents()
            db_path = PathManager.get_database_path('service_orders.db')
            if os.path.exists(db_path):
                backup_atual = db_path + f'.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}'
                os.rename(db_path, backup_atual)
            progress.setValue(40)
            QApplication.processEvents()
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                if 'service_orders.db' not in zipf.namelist():
                    QMessageBox.warning(parent, 'Erro', 'Backup n├úo cont├®m o arquivo de banco de dados!')
                    progress.close()
                    return False
                progress.setValue(60)
                QApplication.processEvents()
                zipf.extract('service_orders.db', os.path.dirname(db_path))
                extracted_path = os.path.join(os.path.dirname(db_path), 'service_orders.db')
                if extracted_path != db_path:
                    os.rename(extracted_path, db_path)
                progress.setValue(80)
                QApplication.processEvents()
        except Exception as e:
            if 'progress' in locals():
                progress.close()
            QMessageBox.critical(parent, 'Erro', f'Erro ao restaurar backup:\n{str(e)}')
            return False
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            _br_codigo, _br_total = BackupManager._aplicar_correcao_automatica_silenciosa(cursor, parent)
            cursor.execute('SELECT COUNT(*) FROM service_orders')
            total_os = cursor.fetchone()[0]
            conn.close()
            progress.setValue(100)
            progress.close()
            if _br_codigo:
                QMessageBox.warning(parent, 'Restaura├º├úo conclu├¡da ÔÇö aten├º├úo', _ERROR_CODES.get(_br_codigo, f'Restaura├º├úo conclu├¡da. C├│digo: {_br_codigo}') + f'\n\nTotal de Ordens de Servi├ºo: {total_os}')
            else:
                QMessageBox.information(parent, 'Restaura├º├úo Conclu├¡da', f'Backup restaurado com sucesso!\n\nTotal de Ordens de Servi├ºo: {total_os}\n\nÔÜá´©Å Reinicie o sistema para aplicar as mudan├ºas completamente.')
        except Exception as e:
            progress.close()
            QMessageBox.critical(parent, 'Erro de Integridade', f'O banco foi restaurado mas pode estar corrompido:\n{str(e)}\n\nVerifique a integridade dos dados.')
            try:
                return False
            except Exception as e:
                if 'progress' in locals():
                    progress.close()
                QMessageBox.critical(parent, 'Erro', f'Erro ao restaurar backup:\n{str(e)}')
                return False
        return True
    @staticmethod
    def verificar_integridade(parent=None):
        try:
            db_path = PathManager.get_database_path('service_orders.db')
            if not os.path.exists(db_path):
                QMessageBox.warning(parent, 'Aviso', 'Banco de dados n├úo encontrado!')
                return False
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('PRAGMA integrity_check')
            result = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM service_orders')
            total_os = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM clients')
            total_clients = cursor.fetchone()[0]
            conn.close()
            if result == 'ok':
                QMessageBox.information(parent, 'Integridade OK', f'Ô£à Banco de dados ├¡ntegro!\n\nOrdens de Servi├ºo: {total_os}\nClientes: {total_clients}\nTamanho: {os.path.getsize(db_path) / 1024:.1f} KB')
                return True
            QMessageBox.warning(parent, 'Problemas Detectados', f'ÔÜá´©Å Problemas na integridade:\n{result}\n\nRecomenda-se fazer backup e verificar dados.')
            return False
        except Exception as e:
            QMessageBox.critical(parent, 'Erro', f'Erro ao verificar integridade:\n{str(e)}')
            return False
    @staticmethod
    def criar_backup_solucoes(parent=None):
        try:
            db_path = PathManager.get_data_path()
            solucoes_db = os.path.join(db_path, 'user_solutions_1.db')
            if not os.path.exists(solucoes_db):
                QMessageBox.warning(parent, 'Aviso', 'Banco de solu├º├Áes n├úo encontrado!')
                return False
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'backup_solucoes_{timestamp}.zip'
            docs_path = BackupManager._get_documentos_path()
            default_path = os.path.join(docs_path, backup_filename)
            save_path, _ = QFileDialog.getSaveFileName(parent, '­ƒÆ¥ Salvar Backup das Solu├º├Áes - TECH UNION', default_path, 'Arquivos ZIP (*.zip)')
            if not save_path:
                return False
            progress = QProgressDialog('Criando backup das suas solu├º├Áes...', 'Cancelar', 0, 100, parent)
            progress.setWindowTitle('­ƒöä Backup em Progresso - TECH UNION')
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            QApplication.processEvents()
            progress.setValue(20)
            QApplication.processEvents()
            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                progress.setValue(40)
                QApplication.processEvents()
                zipf.write(solucoes_db, 'user_solutions_1.db')
                progress.setValue(60)
                QApplication.processEvents()
                backup_info = f'BACKUP TECH UNION - MINHAS SOLU├ç├òES\nData: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\nArquivo: user_solutions_1.db\nVers├úo: 1.3\nSistema: TECH UNION Solutions\nTipo: Solu├º├Áes T├®cnicas do Usu├írio\n\nÔÜá´©Å IMPORTANTE:\n- Este backup cont├®m suas solu├º├Áes t├®cnicas pessoais\n- Mantenha este arquivo em local seguro\n- Use para restaurar em caso de perda de dados\n'
                zipf.writestr('backup_info.txt', backup_info)
                progress.setValue(80)
                QApplication.processEvents()
            progress.setValue(100)
            progress.close()
            file_size = os.path.getsize(save_path) / 1024
            QMessageBox.information(parent, 'Ô£à Backup Criado - TECH UNION', f'Backup das suas solu├º├Áes criado com sucesso!\n\n­ƒôä Arquivo: {os.path.basename(save_path)}\n­ƒôè Tamanho: {file_size:.1f} KB\n­ƒôü Local: {save_path}\n\n­ƒÆí Dica: Guarde este arquivo em local seguro!\nEle cont├®m todas as suas solu├º├Áes t├®cnicas.\n                '.strip())
        except Exception as e:
            QMessageBox.critical(parent, 'ÔØî Erro no Backup', f'Erro ao criar backup das solu├º├Áes:\n{str(e)}')
            return False
        return True
    @staticmethod
    def restaurar_backup_solucoes(parent=None):
        try:
            try:
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    if 'user_solutions_1.db' not in zipf.namelist():
                        QMessageBox.warning(parent, 'ÔØî Erro', 'Backup n├úo cont├®m o arquivo de solu├º├Áes!')
                        progress.close()
                        try:
                            import shutil
                            shutil.rmtree(temp_dir)
                        except:
                            pass
                        return False
            finally:
                try:
                    docs_path = BackupManager._get_documentos_path()
                    backup_path, _ = QFileDialog.getOpenFileName(parent, '­ƒôÑ Selecionar Backup de Solu├º├Áes - TECH UNION', docs_path, 'Arquivos ZIP (*.zip)')
                    if not backup_path:
                        return False
                    reply = QMessageBox.question(parent, 'ÔÜá´©Å Confirmar Restaura├º├úo - TECH UNION', '­ƒöä ATEN├ç├âO - Restaura├º├úo de Solu├º├Áes\n\nEsta opera├º├úo ir├í substituir TODAS as suas solu├º├Áes atuais!\n\nÔÜá´©Å Suas solu├º├Áes atuais ser├úo perdidas\nÔ£à Um backup autom├ítico ser├í criado antes da restaura├º├úo\n­ƒôï As solu├º├Áes do arquivo selecionado ser├úo restauradas\n\nDeseja continuar?\n                '.strip(), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if reply != QMessageBox.Yes:
                        return False
                    progress = QProgressDialog('Restaurando suas solu├º├Áes...', 'Cancelar', 0, 100, parent)
                    progress.setWindowTitle('­ƒöä Restaura├º├úo em Progresso - TECH UNION')
                    progress.setWindowModality(Qt.WindowModal)
                    progress.show()
                    QApplication.processEvents()
                    if not zipfile.is_zipfile(backup_path):
                        QMessageBox.warning(parent, 'ÔØî Erro', 'Arquivo de backup inv├ílido!')
                        progress.close()
                        return False
                    progress.setValue(20)
                    QApplication.processEvents()
                    db_path = PathManager.get_data_path()
                    solucoes_db = os.path.join(db_path, 'user_solutions_1.db')
                except Exception as e:
                    if 'progress' in locals():
                        progress.close()
                    QMessageBox.critical(parent, 'ÔØî Erro na Restaura├º├úo', f'Erro ao restaurar backup:\n{str(e)}')
                    return False
                try:
                    import gc
                    import sqlite3
                    gc.collect()
                    for obj in gc.get_objects():
                        if isinstance(obj, sqlite3.Connection):
                            try:
                                try:
                                    obj.close()
                                except:
                                    continue
                            except:
                                pass
                except:
                    pass
                try:
                    backup_atual = None
                    if os.path.exists(solucoes_db):
                        for tentativa in range(3):
                            pass
                    try:
                        backup_atual = solucoes_db + f'.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}'
                        import shutil
                        shutil.copy2(solucoes_db, backup_atual)
                        print(f'­ƒöÉ Backup de seguran├ºa criado: {backup_atual}')
                    except PermissionError:
                        if tentativa < 2:
                            import time
                            time.sleep(1)
                    else:
                        progress.setValue(40)
                        QApplication.processEvents()
                        import tempfile
                        temp_dir = tempfile.mkdtemp(prefix='union_restore_')
                except Exception as e:
                    if 'progress' in locals():
                        progress.close()
                    QMessageBox.critical(parent, 'ÔØî Erro na Restaura├º├úo', f'Erro ao restaurar backup:\n{str(e)}')
                    return False
        finally:
            zipf = None
            if 'user_solutions_1.db' not in zipf.namelist():
                QMessageBox.warning(parent, 'ÔØî Erro', 'Backup n├úo cont├®m o arquivo de solu├º├Áes!')
                progress.close()
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except:
                    pass
        progress.setValue(50)
        QApplication.processEvents()
        zipf.extract('user_solutions_1.db', temp_dir)
        progress.setValue(60)
        QApplication.processEvents()
        try:
            temp_db = os.path.join(temp_dir, 'user_solutions_1.db')
            sucesso_substituicao = False
            for tentativa in range(3):
                temp_old = None
                try:
                    if os.path.exists(solucoes_db):
                        temp_old = solucoes_db + f'.temp_old_{tentativa}'
                        os.rename(solucoes_db, temp_old)
                    import shutil
                    shutil.copy2(temp_db, solucoes_db)
                    if temp_old and os.path.exists(temp_old):
                        pass
                    try:
                        os.remove(temp_old)
                    except:
                        pass
                    else:
                        sucesso_substituicao = True
                except PermissionError as e:
                    if tentativa < 2:
                        import time
                        time.sleep(2)
                    continue
                break
            progress.setValue(80)
            QApplication.processEvents()
            if not sucesso_substituicao:
                progress.close()
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except:
                    pass
                return False
        finally:
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except:
                pass
        try:
            conn = sqlite3.connect(solucoes_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM user_solutions WHERE status = 'ativo'")
            total_solucoes = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM user_solutions WHERE status = 'ativo' AND compartilhada = 1")
            solucoes_compartilhadas = cursor.fetchone()[0]
            conn.close()
            progress.setValue(100)
            progress.close()
            QMessageBox.information(parent, 'Ô£à Restaura├º├úo Conclu├¡da - TECH UNION', f'Backup restaurado com sucesso!\n\n­ƒôè Total de Solu├º├Áes: {total_solucoes}\n­ƒÜÇ Compartilhadas: {solucoes_compartilhadas}\n\n­ƒöä Recarregue a lista para ver as altera├º├Áes\n­ƒôï Suas solu├º├Áes foram restauradas completamente\n\n­ƒÆ¥ Backup de seguran├ºa foi salvo automaticamente\n                    '.strip())
        except Exception as e:
            progress.close()
            QMessageBox.critical(parent, 'ÔÜá´©Å Erro de Integridade', f'O banco foi restaurado mas pode estar corrompido:\n{str(e)}\n\nVerifique a integridade dos dados.\n                    '.strip())
            try:
                return False
            except Exception as e:
                if 'progress' in locals():
                    progress.close()
                QMessageBox.critical(parent, 'ÔØî Erro na Restaura├º├úo', f'Erro ao restaurar backup:\n{str(e)}')
                return False
        return True
    @staticmethod
    def _detectar_email_irmao(email):
        if not email or '@' not in str(email):
            return
        email_str = str(email).lower().strip()
        if email_str.endswith('.com.br'):
            return email_str.replace('.com.br', '.com')
        if email_str.endswith('.com') and not email_str.endswith('.com.br'):
            return email_str + '.br'
    @staticmethod
    def _obter_contexto_usuario_atual(parent):
        if parent is None:
            return (None, None)
        user_id = None
        user_email = None
        try:
            if hasattr(parent, 'window') and callable(parent.window):
                top = parent.window()
                if top is not None:
                    _id = getattr(top, 'user_id', None)
                    _em = getattr(top, 'user_email', None)
                    if isinstance(_id, int) and _id > 0:
                        user_id = _id
                    if isinstance(_em, str) and '@' in _em:
                        user_email = _em
        except Exception:
            pass
        if user_id and user_email:
            return user_id, user_email
        obj = parent
        for _ in range(5):
            if obj is None:
                return user_id, user_email
            try:
                if user_id is None:
                    _id = getattr(obj, 'user_id', None)
                    if isinstance(_id, int) and _id > 0:
                        user_id = _id
                if user_email is None:
                    _em = getattr(obj, 'user_email', None)
                    if isinstance(_em, str) and '@' in _em:
                        user_email = _em
            except Exception:
                pass
            if user_id and user_email:
                return user_id, user_email
            try:
                p = getattr(obj, 'parent', None)
                obj = p() if callable(p) else None
            except Exception:
                obj = None
                continue
        return user_id, user_email
    @staticmethod
    def _coletar_user_ids_completo(cursor):
        todos = set()
        for tabela, coluna in (('service_orders', 'user_id'), ('clients', 'user_id')):
            try:
                cursor.execute(f'SELECT DISTINCT {coluna} FROM {tabela}')
                todos.update((r[0] for r in cursor.fetchall()))
            except Exception:
                continue
        for tabela, coluna in (('knowledge_base', 'user_id'), ('users', 'id')):
            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabela,))
                if cursor.fetchone():
                    cursor.execute(f'SELECT DISTINCT {coluna} FROM {tabela}')
                    todos.update((r[0] for r in cursor.fetchall()))
            except Exception:
                continue
        return todos
    @staticmethod
    def _aplicar_correcao_automatica_silenciosa(cursor, parent):
        try:
            current_user_id, current_user_email = BackupManager._obter_contexto_usuario_atual(parent)
            todos_user_ids = BackupManager._coletar_user_ids_completo(cursor)
            if not current_user_id or not current_user_email:
                emails_backup = [uid for uid in todos_user_ids if isinstance(uid, str) if '@' in str(uid)]
                if emails_backup:
                    email_pista = emails_backup[0]
                    mysql_id = BackupManager._obter_user_id_mysql(email_pista)
                    if mysql_id:
                        current_user_id = current_user_id or mysql_id
                        current_user_email = current_user_email or email_pista
                    else:
                        irmao = BackupManager._detectar_email_irmao(email_pista)
                        if irmao:
                            mysql_id = BackupManager._obter_user_id_mysql(irmao)
                            if mysql_id:
                                current_user_id = current_user_id or mysql_id
                                current_user_email = current_user_email or irmao
        except Exception as e:
            _registrar_evento_backup('BR-001', f'exc: {type(e).__name__}: {e}')
            return ('BR-001', 0)
        if not current_user_id:
            _registrar_evento_backup('BR-001', f'todos_user_ids={len(todos_user_ids)}, parent_type={type(parent).__name__ if parent else 'None'}')
            return ('BR-001', 0)
        total_corrigidos = 0
        try:
            ids_alvo = None
            for uid_antigo in ids_alvo:
                try:
                    cursor.execute('UPDATE service_orders SET user_id = ? WHERE user_id = ?', (current_user_id, uid_antigo))
                    total_corrigidos += cursor.rowcount or 0
                except Exception:
                    pass
            try:
                cursor.execute('UPDATE clients SET user_id = ? WHERE user_id = ?', (current_user_id, uid_antigo))
                total_corrigidos += cursor.rowcount or 0
            except Exception:
                pass
            else:
                try:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_base'")
                    if cursor.fetchone():
                        cursor.execute('UPDATE knowledge_base SET user_id = ? WHERE user_id = ?', (current_user_id, uid_antigo))
                        total_corrigidos += cursor.rowcount or 0
                except Exception:
                    pass
        except Exception as e:
            _registrar_evento_backup('BR-001', f'exc: {type(e).__name__}: {e}')
            return ('BR-001', 0)
        try:
            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if cursor.fetchone():
                    cursor.execute('DELETE FROM users')
                    cursor.execute('INSERT INTO users (id, email, password, is_admin) VALUES (?, ?, ?, ?)', (current_user_id, current_user_email or f'user_{current_user_id}@local', 'mysql_auth', 0))
            except Exception as e:
                _registrar_evento_backup('BR-001', f'users-table: {e}')
        except Exception as e:
            _registrar_evento_backup('BR-001', f'exc: {type(e).__name__}: {e}')
            return ('BR-001', 0)
        cursor.connection.commit()
        return None, total_corrigidos
    @staticmethod
    def _obter_user_id_mysql(email):
        try:
            import pymysql
            conn = pymysql.connect(**db_config(connect_timeout=5, read_timeout=5, ssl={'ca': None}, ssl_verify_cert=False), **{'cursorclass': pymysql.cursors.DictCursor, 'autocommit': False})
            cursor = conn.cursor()
            cursor.execute('SELECT id_usuario FROM usuarios WHERE email = %s', (email,))
            resultado = cursor.fetchone()
            if resultado:
                cursor.close()
                conn.close()
                return resultado['id_usuario']
            email_irmao = BackupManager._detectar_email_irmao(email)
            if email_irmao:
                cursor.execute('SELECT id_usuario FROM usuarios WHERE email = %s', (email_irmao,))
                resultado = cursor.fetchone()
                if resultado:
                    cursor.close()
                    conn.close()
                    return resultado['id_usuario']
            cursor.close()
            conn.close()
            return
        except Exception as e:
            return
# WARNING: Decompyle incomplete
