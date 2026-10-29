"""Migração 0001 — esquema inicial do Union Manager.

Cria todas as tabelas do domínio de gestão de oficina (offline).
"""
from __future__ import annotations

NOME = "0001_init"

SQL = """
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    nome TEXT NOT NULL,
    telefone TEXT NOT NULL,
    email TEXT,
    rua TEXT,
    numero TEXT,
    bairro TEXT,
    cidade TEXT,
    tipo TEXT NOT NULL DEFAULT 'pessoa_fisica',
    observacoes TEXT,
    criado_em TEXT NOT NULL,
    atualizado_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_clientes_nome ON clientes(nome);
CREATE INDEX IF NOT EXISTS idx_clientes_telefone ON clientes(telefone);

CREATE TABLE IF NOT EXISTS ordens_servico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    cliente_id INTEGER NOT NULL,
    tipo_dispositivo TEXT NOT NULL,
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    serie TEXT,
    valor REAL,
    problema TEXT NOT NULL,
    diagnostico TEXT,
    status TEXT NOT NULL DEFAULT 'em_reparo',
    solucao TEXT,
    passos TEXT,
    motivo_falha TEXT,
    observacoes_tecnicas TEXT,
    valor_final REAL,
    foto_conclusao TEXT,
    os_original_id INTEGER,
    data_entrada TEXT NOT NULL,
    data_conclusao TEXT,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    FOREIGN KEY (os_original_id) REFERENCES ordens_servico(id)
);
CREATE INDEX IF NOT EXISTS idx_os_status ON ordens_servico(status);
CREATE INDEX IF NOT EXISTS idx_os_cliente ON ordens_servico(cliente_id);
CREATE INDEX IF NOT EXISTS idx_os_entrada ON ordens_servico(data_entrada);

CREATE TABLE IF NOT EXISTS ordem_fotos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ordem_id INTEGER NOT NULL,
    caminho TEXT NOT NULL,
    ordem INTEGER NOT NULL DEFAULT 0,
    criado_em TEXT NOT NULL,
    FOREIGN KEY (ordem_id) REFERENCES ordens_servico(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_ordem_fotos_os ON ordem_fotos(ordem_id);

CREATE TABLE IF NOT EXISTS conhecimento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    tipo_dispositivo TEXT NOT NULL,
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    problema TEXT NOT NULL,
    solucao TEXT NOT NULL,
    passos TEXT,
    taxa_sucesso INTEGER NOT NULL DEFAULT 100,
    origem TEXT NOT NULL DEFAULT 'manual',
    ordem_origem_id INTEGER,
    criado_em TEXT NOT NULL,
    FOREIGN KEY (ordem_origem_id) REFERENCES ordens_servico(id)
);
CREATE INDEX IF NOT EXISTS idx_conhecimento_marca ON conhecimento(marca);
CREATE INDEX IF NOT EXISTS idx_conhecimento_modelo ON conhecimento(modelo);

CREATE TABLE IF NOT EXISTS conhecimento_anexos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conhecimento_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    caminho TEXT NOT NULL,
    descricao TEXT,
    FOREIGN KEY (conhecimento_id) REFERENCES conhecimento(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS solucoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    descricao TEXT,
    observacoes TEXT,
    status TEXT NOT NULL DEFAULT 'ativo',
    hash TEXT,
    versao INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL,
    atualizado_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_solucoes_marca ON solucoes(marca);

CREATE TABLE IF NOT EXISTS solucao_midia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solucao_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    caminho TEXT NOT NULL,
    posicao INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (solucao_id) REFERENCES solucoes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS config_empresa (
    user_id INTEGER PRIMARY KEY,
    logo BLOB,
    razao_social TEXT,
    cnpj TEXT,
    nome_fantasia TEXT,
    endereco TEXT,
    cidade TEXT,
    estado TEXT,
    telefone TEXT,
    email TEXT,
    website TEXT,
    mensagem_rodape TEXT,
    termos_garantia TEXT DEFAULT
        'Garantia de 90 dias sobre serviços e peças descritas nesta ordem de serviço.'
);

CREATE TABLE IF NOT EXISTS perfil_usuario (
    user_id INTEGER PRIMARY KEY,
    nome TEXT,
    telefone TEXT,
    email TEXT,
    foto BLOB,
    bio TEXT,
    nascimento TEXT,
    notif_email INTEGER NOT NULL DEFAULT 0,
    notif_push INTEGER NOT NULL DEFAULT 0
);
"""
