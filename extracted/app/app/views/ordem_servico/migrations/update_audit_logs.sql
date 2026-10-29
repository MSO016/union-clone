-- Backup da tabela atual
CREATE TABLE audit_logs_backup AS SELECT * FROM audit_logs;

-- Remove a tabela atual
DROP TABLE audit_logs;

-- Cria a nova tabela com a estrutura correta
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    old_data TEXT,
    new_data TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Restaura os dados
INSERT INTO audit_logs (id, user_id, action, entity_type, entity_id, old_data, new_data)
SELECT id, user_id, action, entity_type, entity_id, old_data, new_data
FROM audit_logs_backup;

-- Remove a tabela de backup
DROP TABLE audit_logs_backup; 