from PyQt5.QtWidgets import QMessageBox
from cryptography.fernet import Fernet
import sqlite3
import os
import hashlib
from utils.solucoes_window import SolucoesWindow
from .path_manager import PathManager
class DatabaseManager:
    def __init__(self):
        self.db_path = PathManager.get_database_path('base.db')
        self.init_database()
    def init_database(self):
        try:
            if not os.path.exists('database'):
                os.makedirs('database')
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("\n                CREATE TABLE IF NOT EXISTS solucoes (\n                    id INTEGER PRIMARY KEY AUTOINCREMENT,\n                    marca TEXT NOT NULL,\n                    modelo TEXT NOT NULL,\n                    descricao TEXT,\n                    observacoes TEXT,\n                    diagrama_blob BLOB,\n                    imagem_blob BLOB,\n                    status TEXT DEFAULT 'ativo'\n                )\n            ")
            conn.commit()
            conn.close()
            return
        except Exception as e:
            print(f'Erro ao inicializar banco de dados: {str(e)}')
    def get_solutions_by_brand(self, marca, modelo_filter=None):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if modelo_filter:
                cursor.execute("\n                    SELECT id, modelo, descricao, observacoes, diagrama_blob, imagem_blob \n                    FROM solucoes \n                    WHERE marca=? AND status='ativo' AND lower(modelo) LIKE ?\n                    ORDER BY modelo\n                ", (marca, f'%{modelo_filter.lower()}%'))
            else:
                cursor.execute("\n                    SELECT id, modelo, descricao, observacoes, diagrama_blob, imagem_blob \n                    FROM solucoes \n                    WHERE marca=? AND status='ativo'\n                    ORDER BY modelo\n                ", (marca,))
            solucoes = cursor.fetchall()
            conn.close()
            return solucoes
        except Exception as e:
            raise Exception(f'Erro ao buscar solu├º├Áes: {str(e)}')
    def get_solution_by_id(self, id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("\n                SELECT modelo, descricao, observacoes, diagrama_blob, imagem_blob \n                FROM solucoes \n                WHERE id=? AND status='ativo'\n            ", (id,))
            solucao = cursor.fetchone()
            conn.close()
            return solucao
        except Exception as e:
            raise Exception(f'Erro ao buscar solu├º├úo: {str(e)}')
    def verify_login(self, username, password):
        try:
            conn = sqlite3.connect(self.users_path)
            cursor = conn.cursor()
            pass_hash = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute('\n                SELECT id, is_admin FROM users \n                WHERE username = ? AND password_hash = ?\n            ', (username, pass_hash))
            user = cursor.fetchone()
            if not user:
                conn.close()
                return (False, 'Credenciais inv├ílidas')
        finally:
            conn.close()
        try:
            return True, 'admin' if user[1] else 'user'
        finally:
            conn.close()
    def ver_solucoes(self, marca):
        try:
            self.solucoes_window = SolucoesWindow(marca, self)
            self.solucoes_window.show()
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao abrir solu├º├Áes: {str(e)}')
    def get_user_solutions(self, user_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('\n                SELECT id, marca, modelo, descricao, status\n                FROM solucoes \n                WHERE user_id=?\n                ORDER BY data_criacao DESC\n            ', (user_id,))
            solucoes = cursor.fetchall()
            conn.close()
            return solucoes
        except Exception as e:
            raise Exception(f'Erro ao buscar solu├º├Áes do usu├írio: {str(e)}')
    def add_user_solution(self, user_id, marca, modelo, descricao, imagem_blob=None, diagrama_blob=None):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("\n                INSERT INTO solucoes (\n                    user_id, marca, modelo, descricao, \n                    imagem_blob, diagrama_blob, status,\n                    data_criacao\n                ) VALUES (?, ?, ?, ?, ?, ?, 'pendente', datetime('now'))\n            ", (user_id, marca, modelo, descricao, imagem_blob, diagrama_blob))
            conn.commit()
            conn.close()
            return
        except Exception as e:
            raise Exception(f'Erro ao adicionar solu├º├úo: {str(e)}')
