from PyQt5.QtWidgets import QCompleter, QLineEdit
from PyQt5.QtCore import Qt
import sqlite3
class DeviceCompleter:
    def __init__(self, user_id):
        self.user_id = user_id
        self.marca_completer = None
        self.modelo_completer = None
    def setup_completers(self, marca_input: QLineEdit, modelo_input: QLineEdit, tipo_dispositivo: str=None):
        '''Configura os completers para marca e modelo'''
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            if tipo_dispositivo:
                cursor.execute('\n                    SELECT DISTINCT brand\n                    FROM service_orders\n                    WHERE user_id = ? AND device_type = ?\n                    ORDER BY brand\n                ', (self.user_id, tipo_dispositivo))
            else:
                cursor.execute('\n                    SELECT DISTINCT brand\n                    FROM service_orders\n                    WHERE user_id = ?\n                    ORDER BY brand\n                ', (self.user_id,))
        except Exception as e:
            print(f'Erro ao configurar autocompletar: {str(e)}')
        try:
            marcas = [row[0] for row in cursor.fetchall() if row[0]]
            self.marca_completer = QCompleter(marcas)
            self.marca_completer.setCaseSensitivity(Qt.CaseInsensitive)
            marca_input.setCompleter(self.marca_completer)
            marca_input.textChanged.connect((lambda text: self.atualizar_modelos(text, modelo_input, tipo_dispositivo)))
        except Exception as e:
            print(f'Erro ao configurar autocompletar: {str(e)}')
        if conn:
            conn.close()
    def atualizar_modelos(self, marca: str, modelo_input: QLineEdit, tipo_dispositivo: str=None):
        '''Atualiza os modelos baseado na marca selecionada'''
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            if tipo_dispositivo:
                cursor.execute('\n                    SELECT DISTINCT model\n                    FROM service_orders\n                    WHERE user_id = ? AND brand = ? AND device_type = ?\n                    ORDER BY model\n                ', (self.user_id, marca, tipo_dispositivo))
            else:
                cursor.execute('\n                    SELECT DISTINCT model\n                    FROM service_orders\n                    WHERE user_id = ? AND brand = ?\n                    ORDER BY model\n                ', (self.user_id, marca))
        except Exception as e:
            print(f'Erro ao atualizar modelos: {str(e)}')
        try:
            modelos = [row[0] for row in cursor.fetchall() if row[0]]
            self.modelo_completer = QCompleter(modelos)
            self.modelo_completer.setCaseSensitivity(Qt.CaseInsensitive)
            modelo_input.setCompleter(self.modelo_completer)
        except Exception as e:
            print(f'Erro ao atualizar modelos: {str(e)}')
        if conn:
            conn.close()
    def get_device_stats(self, marca: str=None, modelo: str=None, tipo_dispositivo: str=None):
        '''Retorna estat├¡sticas do dispositivo'''
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            query = "\n                SELECT \n                    COUNT(*) as total,\n                    SUM(CASE WHEN status = 'concluido_sucesso' THEN 1 ELSE 0 END) as sucesso,\n                    SUM(CASE WHEN status = 'concluido_sem_solucao' THEN 1 ELSE 0 END) as sem_solucao\n                FROM service_orders\n                WHERE user_id = ?\n            "
            params = [self.user_id]
            if marca:
                query += ' AND brand = ?'
                params.append(marca)
            if modelo:
                query += ' AND model = ?'
                params.append(modelo)
            if tipo_dispositivo:
                query += ' AND device_type = ?'
                params.append(tipo_dispositivo)
            cursor.execute(query, params)
            total, sucesso, sem_solucao = cursor.fetchone()
            if total > 0:
                taxa_sucesso = sucesso / total * 100
                taxa_falha = sem_solucao / total * 100
            else:
                taxa_sucesso = taxa_falha = 0
        except Exception as e:
            print(f'Erro ao buscar estat├¡sticas: {str(e)}')
            try:
                pass
            finally:
                if conn:
                    conn.close()
            return
        if conn:
            conn.close()
            return {'total': total, 'sucesso': sucesso, 'sem_solucao': sem_solucao, 'taxa_sucesso': taxa_sucesso, 'taxa_falha': taxa_falha}
# WARNING: Decompyle incomplete
