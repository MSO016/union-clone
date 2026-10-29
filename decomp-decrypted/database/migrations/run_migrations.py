from add_warranty_text import migrate as add_warranty_text
def run_all_migrations():
    print('­ƒöä Iniciando migra├º├Áes do banco de dados...')
    migrations = [('Adicionar coluna warranty_text', add_warranty_text)]
    for description, migration in migrations:
        print(f'\nÔûÂ´©Å Executando: {description}')
        migration()
    print('\nÔ£à Todas as migra├º├Áes foram conclu├¡das!')
if __name__ == '__main__':
    run_all_migrations()
