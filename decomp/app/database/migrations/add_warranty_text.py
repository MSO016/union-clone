import sqlite3
import os
def migrate():
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'service_orders.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('PRAGMA table_info(company_settings)')
        columns = cursor.fetchall()
    except Exception as e:
        print(f'ÔØî Erro ao adicionar coluna: {str(e)}')
    try:
        column_names = [column[1] for column in columns]
        if 'warranty_text' not in column_names:
            cursor.execute('\n                ALTER TABLE company_settings\n                ADD COLUMN warranty_text TEXT DEFAULT "TERMOS DE GARANTIA:\n\n1. A garantia dos servi├ºos prestados ├® de 90 dias, contados a partir da data de entrega do equipamento.\n2. A garantia cobre apenas os servi├ºos realizados e pe├ºas substitu├¡das descritas nesta ordem de servi├ºo.\n3. A garantia n├úo cobre:\n   - Danos causados por mau uso, quedas ou acidentes\n   - Problemas diferentes dos originalmente consertados\n   - Oxida├º├úo ou danos por ├ígua\n   - Viola├º├úo do equipamento por terceiros\n4. Para acionar a garantia, ├® necess├írio apresentar esta ordem de servi├ºo."\n            ')
            print('Ô£à Coluna warranty_text adicionada com sucesso!')
        else:
            print('Ôä╣´©Å Coluna warranty_text j├í existe.')
        conn.commit()
    except Exception as e:
        print(f'ÔØî Erro ao adicionar coluna: {str(e)}')
    if conn:
        conn.close()
if __name__ == '__main__':
    migrate()
