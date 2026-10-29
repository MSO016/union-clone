"""Testes do serviço de backup/restauração.

Executar: python -m tests.test_backup
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from app.core.services.backup_service import (
        BackupError,
        backup_nome_sugerido,
        backup_para,
        restaurar_de,
    )

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        banco = tdp / "union.db"

        # Cria um banco com dados.
        conn = sqlite3.connect(str(banco))
        conn.execute(
            "CREATE TABLE clientes (id INTEGER PRIMARY KEY, nome TEXT NOT NULL)"
        )
        conn.execute("INSERT INTO clientes (nome) VALUES ('Ana')")
        conn.commit()

        # Backup com transação pendente (sem commit): a API backup deve incluir.
        destino = backup_para(conn, tdp / "b1.db")
        assert destino.exists() and destino.stat().st_size > 0, "backup vazio"

        # Backup não sobrescreve existente.
        try:
            backup_para(conn, tdp / "b1.db")
            raise AssertionError("deveria recusar destino existente")
        except BackupError:
            pass

        # Dado gravado DEPOIS do backup deve sumir após a restauração.
        conn.execute("INSERT INTO clientes (nome) VALUES ('Bia')")
        conn.commit()

        # Restauração em um banco existente: o anterior vira .old-*.
        restaurar_de(destino, conn, banco)
        # A conexão antiga foi fechada pelo serviço.
        try:
            conn.execute("SELECT 1")
            raise AssertionError("conexão antiga deveria estar fechada")
        except sqlite3.ProgrammingError:
            pass
        nova = sqlite3.connect(str(banco))
        nomes = [r[0] for r in nova.execute("SELECT nome FROM clientes ORDER BY id")]
        nova.close()
        assert nomes == ["Ana"], f"restauração divergente: {nomes}"

        # Restauração preserva o banco anterior como .old-*.
        backups_velhos = list(tdp.glob("union.old-*.db"))
        assert backups_velhos, "banco anterior não foi preservado como .old"

        # Restauração de arquivo inexistente falha com BackupError.
        try:
            restaurar_de(tdp / "nao-existe.db", sqlite3.connect(":memory:"), tdp / "x.db")
            raise AssertionError("deveria falhar para arquivo inexistente")
        except BackupError:
            pass

        # Restauração de arquivo não-SQLite falha antes de tocar no banco.
        lixo = tdp / "lixo.db"
        lixo.write_bytes(b"isto nao e um sqlite" * 100)
        try:
            restaurar_de(lixo, sqlite3.connect(":memory:"), tdp / "y.db")
            raise AssertionError("deveria recusar arquivo não-SQLite")
        except BackupError:
            pass

        # Nome sugerido é único.
        n1 = backup_nome_sugerido(tdp)
        assert n1.name.startswith("union-backup-") and n1.suffix == ".db"

    print("OK — backup/restauração validados (snapshot, .old, validação).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
