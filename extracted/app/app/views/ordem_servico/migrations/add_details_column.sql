-- Verifica se a coluna details existe
SELECT COUNT(*) FROM pragma_table_info('audit_logs') WHERE name='details';

-- Se não existir, adiciona a coluna details
ALTER TABLE audit_logs ADD COLUMN details TEXT;

-- Verifica se existe a coluna timestamp
SELECT COUNT(*) FROM pragma_table_info('audit_logs') WHERE name='timestamp';

-- Se existir timestamp mas não created_at, renomeia a coluna
ALTER TABLE audit_logs RENAME COLUMN timestamp TO created_at;

-- Se não existir nem timestamp nem created_at, adiciona created_at
ALTER TABLE audit_logs ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;
