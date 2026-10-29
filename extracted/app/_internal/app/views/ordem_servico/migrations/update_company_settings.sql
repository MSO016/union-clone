-- Backup da tabela atual
CREATE TABLE company_settings_backup AS SELECT * FROM company_settings;

-- Remove a tabela atual
DROP TABLE company_settings;

-- Cria a nova tabela com CNPJ e phone nullable
CREATE TABLE company_settings (
    id INTEGER PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    cnpj VARCHAR(14),
    address VARCHAR(200),
    phone VARCHAR(15),
    email VARCHAR(120),
    logo_path VARCHAR(200),
    warranty_terms TEXT
);

-- Restaura os dados, tratando telefones inválidos
INSERT INTO company_settings 
SELECT id, company_name, 
       CASE WHEN cnpj = '00000000000000' THEN NULL ELSE cnpj END,
       address, 
       CASE 
           WHEN phone IS NULL OR phone = '' OR LENGTH(REPLACE(REPLACE(REPLACE(REPLACE(phone, '(', ''), ')', ''), '-', ''), ' ', '')) NOT IN (10,11) 
           THEN NULL 
           ELSE phone 
       END,
       email, logo_path, warranty_terms
FROM company_settings_backup;

-- Remove a tabela de backup
DROP TABLE company_settings_backup; 