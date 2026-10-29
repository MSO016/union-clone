"""Repositório de soluções (vitrine por marca + minhas soluções)."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

from ...models.models import Solucao, SolucaoMidia


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _row_para_solucao(row: sqlite3.Row) -> Solucao:
    return Solucao(
        id=row["id"],
        user_id=row["user_id"],
        marca=row["marca"],
        modelo=row["modelo"],
        descricao=row["descricao"] or "",
        observacoes=row["observacoes"] or "",
        status=row["status"],
        hash=row["hash"] or "",
        versao=int(row["versao"]),
        criado_em=row["criado_em"],
        atualizado_em=row["atualizado_em"],
    )


class SolucaoRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def criar(self, s: Solucao) -> int:
        now = _agora()
        cur = self._conn.execute(
            """
            INSERT INTO solucoes (
                user_id, marca, modelo, descricao, observacoes, status, hash, versao,
                criado_em, atualizado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                s.user_id,
                s.marca,
                s.modelo,
                s.descricao,
                s.observacoes,
                s.status,
                s.hash,
                s.versao,
                now,
                now,
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def atualizar(self, s: Solucao) -> None:
        if s.id is None:
            raise ValueError("solucao sem id")
        self._conn.execute(
            """
            UPDATE solucoes SET
                marca=?, modelo=?, descricao=?, observacoes=?, status=?,
                versao=versao+1, atualizado_em=?
            WHERE id=?
            """,
            (s.marca, s.modelo, s.descricao, s.observacoes, s.status, _agora(), s.id),
        )
        self._conn.commit()

    def excluir(self, solucao_id: int) -> None:
        self._conn.execute("DELETE FROM solucoes WHERE id=?", (solucao_id,))
        self._conn.commit()

    def por_id(self, solucao_id: int) -> Optional[Solucao]:
        row = self._conn.execute(
            "SELECT * FROM solucoes WHERE id=?", (solucao_id,)
        ).fetchone()
        if not row:
            return None
        s = _row_para_solucao(row)
        s.midias = self.midias_da_solucao(solucao_id)
        return s

    def marcas_distintas(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT marca FROM solucoes ORDER BY marca COLLATE NOCASE"
        ).fetchall()
        return [r["marca"] for r in rows]

    def buscar_por_marca(self, marca: str, termo: str = "") -> list[Solucao]:
        sql = "SELECT * FROM solucoes WHERE marca=? AND status='ativo'"
        params: list[object] = [marca]
        if termo.strip():
            sql += " AND modelo LIKE ?"
            params.append(f"%{termo.strip()}%")
        sql += " ORDER BY modelo COLLATE NOCASE"
        rows = self._conn.execute(sql, params).fetchall()
        return [_row_para_solucao(r) for r in rows]

    def listar_todas_ativas(self) -> list[Solucao]:
        rows = self._conn.execute(
            "SELECT * FROM solucoes WHERE status='ativo' ORDER BY marca, modelo"
        ).fetchall()
        return [_row_para_solucao(r) for r in rows]

    # --- mídia -------------------------------------------------------------
    def midias_da_solucao(self, solucao_id: int) -> list[SolucaoMidia]:
        rows = self._conn.execute(
            "SELECT * FROM solucao_midia WHERE solucao_id=? ORDER BY posicao",
            (solucao_id,),
        ).fetchall()
        return [
            SolucaoMidia(
                id=r["id"],
                solucao_id=r["solucao_id"],
                tipo=r["tipo"],
                caminho=r["caminho"],
                posicao=r["posicao"],
            )
            for r in rows
        ]

    def adicionar_midia(self, m: SolucaoMidia) -> int:
        cur = self._conn.execute(
            "INSERT INTO solucao_midia (solucao_id, tipo, caminho, posicao) VALUES (?, ?, ?, ?)",
            (m.solucao_id, m.tipo, m.caminho, m.posicao),
        )
        self._conn.commit()
        return int(cur.lastrowid)
