"""Runner de migrações versionadas.

- cria a tabela `migrations` se não existir
- aplica, em ordem, as migrações pendentes (definidas em MIGRACOES)
- cada migração é um dict {version: (nome, sql_ou_callable)}
"""
from __future__ import annotations

import sqlite3
from datetime import datetime

from .m0001_init import SQL as M0001_SQL
from .m0001_init import NOME as M0001_NOME

# Ordem de aplicação. Chave = versão (int).
MIGRACOES: dict[int, tuple[str, str]] = {
    1: (M0001_NOME, M0001_SQL),
}


def _tabela_migracoes(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS migrations (
            version INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            aplicado_em TEXT NOT NULL
        )
        """
    )
    conn.commit()


def _versao_atual(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT MAX(version) AS v FROM migrations").fetchone()
    return int(row["v"] or 0)


def rodar_migracoes(conn: sqlite3.Connection) -> None:
    _tabela_migracoes(conn)
    atual = _versao_atual(conn)
    for version in sorted(MIGRACOES):
        if version <= atual:
            continue
        nome, sql = MIGRACOES[version]
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO migrations (version, nome, aplicado_em) VALUES (?, ?, ?)",
            (version, nome, datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
