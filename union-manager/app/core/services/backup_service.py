"""Backup e restauração do banco local — uso pessoal (SPEC RF-CFG-*).

Usa a API nativa `sqlite3.Connection.backup`, que é segura mesmo com o
WAL ativo (sem simples cópia de arquivo com transações pendentes).
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path


class BackupError(RuntimeError):
    pass


def backup_para(conn: sqlite3.Connection, destino: Path) -> Path:
    """Grava um snapshot consistente do banco em `destino`."""
    destino = Path(destino)
    if destino.exists():
        raise BackupError(f"O arquivo de destino já existe: {destino}")
    destino.parent.mkdir(parents=True, exist_ok=True)
    alvo = sqlite3.connect(str(destino))
    try:
        conn.backup(alvo)
    finally:
        alvo.close()
    return destino


def restaurar_de(origem: Path, conexao_atual: sqlite3.Connection,
                 caminho_banco: Path) -> None:
    """Restaura o banco a partir de `origem`, substituindo o arquivo atual.

    A conexão atual é fechada; o chamador deve reabrê-la em `caminho_banco`.
    """
    origem = Path(origem)
    if not origem.exists():
        raise BackupError(f"Arquivo de backup inexistente: {origem}")
    # Valida que é um SQLite antes de substituir o banco vivo.
    try:
        verificador = sqlite3.connect(f"file:{origem}?mode=ro", uri=True)
        try:
            verificador.execute("PRAGMA schema_version").fetchone()
        finally:
            verificador.close()
    except sqlite3.DatabaseError as e:
        raise BackupError(f"Backup inválido: {e}") from e

    conexao_atual.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conexao_atual.close()
    destino = Path(caminho_banco)
    # Preserva um .old por segurança antes de sobrescrever.
    if destino.exists():
        sufixo = datetime.now().strftime("%Y%m%d-%H%M%S")
        destino.replace(destino.with_suffix(f".old-{sufixo}.db"))
    # Copia byte a byte do backup validado.
    destino.write_bytes(origem.read_bytes())


def backup_nome_sugerido(pasta: Path) -> Path:
    """Caminho único sugerido: union-backup-YYYYMMDD-HHMMSS.db."""
    carimbo = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path(pasta) / f"union-backup-{carimbo}.db"
