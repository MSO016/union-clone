"""Repositório de ordens de serviço (CRUD + ciclo de vida + histórico)."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

from ...models.models import (
    OrdemFoto,
    OrdemServico,
    StatusOrdem,
    TipoDispositivo,
)


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _row_para_ordem(row: sqlite3.Row) -> OrdemServico:
    return OrdemServico(
        id=row["id"],
        user_id=row["user_id"],
        cliente_id=row["cliente_id"],
        tipo_dispositivo=TipoDispositivo(row["tipo_dispositivo"]),
        marca=row["marca"],
        modelo=row["modelo"],
        serie=row["serie"] or "",
        valor=row["valor"],
        problema=row["problema"],
        diagnostico=row["diagnostico"] or "",
        status=StatusOrdem(row["status"]),
        solucao=row["solucao"] or "",
        passos=row["passos"] or "",
        motivo_falha=row["motivo_falha"] or "",
        observacoes_tecnicas=row["observacoes_tecnicas"] or "",
        valor_final=row["valor_final"],
        foto_conclusao=row["foto_conclusao"] or "",
        os_original_id=row["os_original_id"],
        data_entrada=row["data_entrada"],
        data_conclusao=row["data_conclusao"] or "",
    )


class OrdemRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    # --- CRUD -------------------------------------------------------------
    def criar(self, o: OrdemServico) -> int:
        cur = self._conn.execute(
            """
            INSERT INTO ordens_servico (
                user_id, cliente_id, tipo_dispositivo, marca, modelo, serie, valor,
                problema, diagnostico, status, solucao, passos, motivo_falha,
                observacoes_tecnicas, valor_final, foto_conclusao, os_original_id,
                data_entrada, data_conclusao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                o.user_id,
                o.cliente_id,
                o.tipo_dispositivo.value,
                o.marca,
                o.modelo,
                o.serie,
                o.valor,
                o.problema,
                o.diagnostico,
                o.status.value,
                o.solucao,
                o.passos,
                o.motivo_falha,
                o.observacoes_tecnicas,
                o.valor_final,
                o.foto_conclusao,
                o.os_original_id,
                o.data_entrada or _agora(),
                o.data_conclusao or None,
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def atualizar(self, o: OrdemServico) -> None:
        if o.id is None:
            raise ValueError("ordem sem id")
        self._conn.execute(
            """
            UPDATE ordens_servico SET
                cliente_id=?, tipo_dispositivo=?, marca=?, modelo=?, serie=?, valor=?,
                problema=?, diagnostico=?, status=?, solucao=?, passos=?, motivo_falha=?,
                observacoes_tecnicas=?, valor_final=?, foto_conclusao=?, data_conclusao=?
            WHERE id=?
            """,
            (
                o.cliente_id,
                o.tipo_dispositivo.value,
                o.marca,
                o.modelo,
                o.serie,
                o.valor,
                o.problema,
                o.diagnostico,
                o.status.value,
                o.solucao,
                o.passos,
                o.motivo_falha,
                o.observacoes_tecnicas,
                o.valor_final,
                o.foto_conclusao,
                o.data_conclusao or None,
                o.id,
            ),
        )
        self._conn.commit()

    def excluir(self, ordem_id: int) -> None:
        # Fotos apagadas em cascata via FK (ON DELETE CASCADE).
        self._conn.execute("DELETE FROM ordens_servico WHERE id=?", (ordem_id,))
        self._conn.commit()

    def por_id(self, ordem_id: int) -> Optional[OrdemServico]:
        row = self._conn.execute(
            "SELECT * FROM ordens_servico WHERE id=?", (ordem_id,)
        ).fetchone()
        if not row:
            return None
        ordem = _row_para_ordem(row)
        ordem.fotos = self.fotos_da_ordem(ordem_id)
        return ordem

    # --- consultas de negócio ---------------------------------------------
    def listar_abertas(self) -> list[OrdemServico]:
        rows = self._conn.execute(
            "SELECT * FROM ordens_servico WHERE status=? ORDER BY data_entrada DESC",
            (StatusOrdem.EM_REPARO.value,),
        ).fetchall()
        return [_row_para_ordem(r) for r in rows]

    def listar_historico(
        self, status: Optional[StatusOrdem] = None, termo: str = ""
    ) -> list[OrdemServico]:
        sql = "SELECT * FROM ordens_servico WHERE 1=1"
        params: list[object] = []
        if status is not None:
            sql += " AND status=?"
            params.append(status.value)
        if termo.strip():
            like = f"%{termo.strip()}%"
            sql += " AND (marca LIKE ? OR modelo LIKE ? OR problema LIKE ?)"
            params.extend([like, like, like])
        sql += " ORDER BY data_entrada DESC"
        rows = self._conn.execute(sql, params).fetchall()
        return [_row_para_ordem(r) for r in rows]

    def recentes(self, limite: int = 50) -> list[OrdemServico]:
        rows = self._conn.execute(
            "SELECT * FROM ordens_servico ORDER BY data_entrada DESC LIMIT ?",
            (limite,),
        ).fetchall()
        return [_row_para_ordem(r) for r in rows]

    def contar_por_status(self) -> dict[str, int]:
        rows = self._conn.execute(
            "SELECT status, COUNT(*) AS n FROM ordens_servico GROUP BY status"
        ).fetchall()
        return {r["status"]: int(r["n"]) for r in rows}

    # --- fotos -------------------------------------------------------------
    def fotos_da_ordem(self, ordem_id: int) -> list[OrdemFoto]:
        rows = self._conn.execute(
            "SELECT * FROM ordem_fotos WHERE ordem_id=? ORDER BY ordem",
            (ordem_id,),
        ).fetchall()
        return [
            OrdemFoto(
                id=r["id"],
                ordem_id=r["ordem_id"],
                caminho=r["caminho"],
                ordem=r["ordem"],
                criado_em=r["criado_em"],
            )
            for r in rows
        ]

    def adicionar_foto(self, foto: OrdemFoto) -> int:
        cur = self._conn.execute(
            "INSERT INTO ordem_fotos (ordem_id, caminho, ordem, criado_em) VALUES (?, ?, ?, ?)",
            (foto.ordem_id, foto.caminho, foto.ordem, foto.criado_em or _agora()),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def remover_foto(self, foto_id: int) -> None:
        self._conn.execute("DELETE FROM ordem_fotos WHERE id=?", (foto_id,))
        self._conn.commit()
