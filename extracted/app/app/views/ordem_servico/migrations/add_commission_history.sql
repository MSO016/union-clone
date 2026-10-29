-- Cria a tabela commission_history
CREATE TABLE IF NOT EXISTS commission_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    technician_id INTEGER NOT NULL,
    commission_rate FLOAT NOT NULL,
    commission_value FLOAT NOT NULL,
    service_value FLOAT NOT NULL,
    paid BOOLEAN DEFAULT 0,
    paid_at DATETIME,
    paid_by_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES service_orders(id),
    FOREIGN KEY (technician_id) REFERENCES technicians(id),
    FOREIGN KEY (paid_by_id) REFERENCES users(id)
);

-- Cria índices para melhor performance
CREATE INDEX IF NOT EXISTS ix_commission_history_order_id ON commission_history(order_id);
CREATE INDEX IF NOT EXISTS ix_commission_history_technician_id ON commission_history(technician_id);
CREATE INDEX IF NOT EXISTS ix_commission_history_paid ON commission_history(paid); 