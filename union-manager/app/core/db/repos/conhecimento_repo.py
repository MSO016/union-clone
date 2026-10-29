"""Repositório da base de conhecimento (CRUD + busca + anexos)."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

from ...models.models import (
    Conhecimento,
    ConhecimentoAnexo,
    OrigemConhecimento,
    TipoDispositivo,
)


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _row_para_conhecimento(row: sqlite3.Row) -> Conhecimento:
    return Conhecimento(
        id=row["id"],
        user_id=row["user_id"],
        tipo_dispositivo=TipoDispositivo(row["tipo_dispositivo"]),
        marca=row["marca"],
        modelo=row["modelo"],
        problema=row["problema"],
        solucao=row["solucao"],
        passos=row["passos"] or "",
        taxa_sucesso=int(row["taxa_sucesso"]),
        origem=OrigemConhecimento(row["origem"]),
        ordem_origem_id=row["ordem_origem_id"],
        criado_em=row["criado_em"],
    )


class ConhecimentoRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def criar(self, k: Conhecimento) -> int:
        cur = self._conn.execute(
            """
            INSERT INTO conhecimento (
                user_id, tipo_dispositivo, marca, modelo, problema, solucao, passos,
                taxa_sucesso, origem, ordem_origem_id, criado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                k.user_id,
                k.tipo_dispositivo.value,
                k.marca,
                k.modelo,
                k.problema,
                k.solucao,
                k.passos,
                k.taxa_sucesso,
                k.origem.value,
                k.ordem_origem_id,
                k.criado_em or _agora(),
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def atualizar(self, k: Conhecimento) -> None:
        if k.id is None:
            raise ValueError("conhecimento sem id")
        self._conn.execute(
            """
            UPDATE conhecimento SET
                tipo_dispositivo=?, marca=?, modelo=?, problema=?, solucao=?,
                passos=?, taxa_sucesso=?
            WHERE id=?
            """,
            (
                k.tipo_dispositivo.value,
                k.marca,
                k.modelo,
                k.problema,
                k.solucao,
                k.passos,
                k.taxa_sucesso,
                k.id,
            ),
        )
        self._conn.commit()

    def excluir(self, conhecimento_id: int) -> None:
        self._conn.execute("DELETE FROM conhecimento WHERE id=?", (conhecimento_id,))
        self._conn.commit()

    def por_id(self, conhecimento_id: int) -> Optional[Conhecimento]:
        row = self._conn.execute(
            "SELECT * FROM conhecimento WHERE id=?", (conhecimento_id,)
        ).fetchone()
        if not row:
            return None
        k = _row_para_conhecimento(row)
        k.anexos = self.anexos_do_conhecimento(conhecimento_id)
        return k

    def buscar(
        self, termo: str = "", tipo_dispositivo: Optional[TipoDispositivo] = None
    ) -> list[Conhecimento]:
        sql = "SELECT * FROM conhecimento WHERE 1=1"
        params: list[object] = []
        if termo.strip():
            like = f"%{termo.strip()}%"
            sql += " AND (marca LIKE ? OR modelo LIKE ? OR problema LIKE ?)"
            params.extend([like, like, like])
        if tipo_dispositivo is not None:
            sql += " AND tipo_dispositivo=?"
            params.append(tipo_dispositivo.value)
        sql += " ORDER BY marca, modelo"
        rows = self._conn.execute(sql, params).fetchall()
        return [_row_para_conhecimento(r) for r in rows]

    # --- anexos ------------------------------------------------------------
    def anexos_do_conhecimento(self, conhecimento_id: int) -> list[ConhecimentoAnexo]:
        rows = self._conn.execute(
            "SELECT * FROM conhecimento_anexos WHERE conhecimento_id=?",
            (conhecimento_id,),
        ).fetchall()
        return [
            ConhecimentoAnexo(
                id=r["id"],
                conhecimento_id=r["conhecimento_id"],
                tipo=r["tipo"],
                caminho=r["caminho"],
                descricao=r["descricao"] or "",
            )
            for r in rows
        ]

    def adicionar_anexo(self, a: ConhecimentoAnexo) -> int:
        cur = self._conn.execute(
            "INSERT INTO conhecimento_anexos (conhecimento_id, tipo, caminho, descricao) VALUES (?, ?, ?, ?)",
            (a.conhecimento_id, a.tipo, a.caminho, a.descricao),
        )
        self._conn.commit()
        return int(cur.lastrowid)
