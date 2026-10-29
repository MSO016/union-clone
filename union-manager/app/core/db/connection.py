"""Conexão e utilitários do SQLite.

- abre conexão com PRAGMAs adequados (WAL, foreign_keys)
- garante o diretório de dados
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


def garantir_diretorio_dados(dados_dir: Path) -> None:
    dados_dir.mkdir(parents=True, exist_ok=True)
    (dados_dir / "fotos").mkdir(exist_ok=True)
    (dados_dir / "attachments" / "kb").mkdir(parents=True, exist_ok=True)
    (dados_dir / "backups").mkdir(exist_ok=True)


def abrir_conexao(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    _aplicar_pragmas(conn)
    return conn


def _aplicar_pragmas(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")
    cur.execute("PRAGMA journal_mode = WAL")
    cur.execute("PRAGMA synchronous = NORMAL")
    conn.commit()
