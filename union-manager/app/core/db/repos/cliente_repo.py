"""Repositório de clientes (CRUD + busca + duplicidade)."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

from ...models.models import Cliente, TipoCliente


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _row_para_cliente(row: sqlite3.Row) -> Cliente:
    return Cliente(
        id=row["id"],
        user_id=row["user_id"],
        nome=row["nome"],
        telefone=row["telefone"],
        email=row["email"] or "",
        rua=row["rua"] or "",
        numero=row["numero"] or "",
        bairro=row["bairro"] or "",
        cidade=row["cidade"] or "",
        tipo=TipoCliente(row["tipo"]),
        observacoes=row["observacoes"] or "",
        criado_em=row["criado_em"],
        atualizado_em=row["atualizado_em"],
    )


class ClienteRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def criar(self, c: Cliente) -> int:
        now = _agora()
        cur = self._conn.execute(
            """
            INSERT INTO clientes (
                user_id, nome, telefone, email, rua, numero, bairro, cidade,
                tipo, observacoes, criado_em, atualizado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                c.user_id,
                c.nome,
                c.telefone,
                c.email,
                c.rua,
                c.numero,
                c.bairro,
                c.cidade,
                c.tipo.value,
                c.observacoes,
                now,
                now,
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def atualizar(self, c: Cliente) -> None:
        if c.id is None:
            raise ValueError("cliente sem id")
        self._conn.execute(
            """
            UPDATE clientes SET
                nome=?, telefone=?, email=?, rua=?, numero=?, bairro=?, cidade=?,
                tipo=?, observacoes=?, atualizado_em=?
            WHERE id=?
            """,
            (
                c.nome,
                c.telefone,
                c.email,
                c.rua,
                c.numero,
                c.bairro,
                c.cidade,
                c.tipo.value,
                c.observacoes,
                _agora(),
                c.id,
            ),
        )
        self._conn.commit()

    def excluir(self, cliente_id: int) -> None:
        self._conn.execute("DELETE FROM clientes WHERE id=?", (cliente_id,))
        self._conn.commit()

    def por_id(self, cliente_id: int) -> Optional[Cliente]:
        row = self._conn.execute(
            "SELECT * FROM clientes WHERE id=?", (cliente_id,)
        ).fetchone()
        return _row_para_cliente(row) if row else None

    def contar_ordens(self, cliente_id: int) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS n FROM ordens_servico WHERE cliente_id=?",
            (cliente_id,),
        ).fetchone()
        return int(row["n"])

    def buscar(self, termo: str) -> list[Cliente]:
        like = f"%{termo.strip()}%"
        rows = self._conn.execute(
            """
            SELECT * FROM clientes
            WHERE nome LIKE ? OR telefone LIKE ? OR email LIKE ?
            ORDER BY nome COLLATE NOCASE
            """,
            (like, like, like),
        ).fetchall()
        return [_row_para_cliente(r) for r in rows]

    def listar_todos(self) -> list[Cliente]:
        rows = self._conn.execute(
            "SELECT * FROM clientes ORDER BY nome COLLATE NOCASE"
        ).fetchall()
        return [_row_para_cliente(r) for r in rows]

    def duplicado(self, nome: str, telefone: str, excluir_id: Optional[int] = None) -> bool:
        sql = "SELECT COUNT(*) AS n FROM clientes WHERE nome=? AND telefone=?"
        params: list[object] = [nome, telefone]
        if excluir_id is not None:
            sql += " AND id != ?"
            params.append(excluir_id)
        row = self._conn.execute(sql, params).fetchone()
        return int(row["n"]) > 0
