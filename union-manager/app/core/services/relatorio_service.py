"""Regras de relatório (diário e mensal) — SPEC RF-REP-1 / RF-REP-2."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date


@dataclass
class ResumoDiario:
    dia: date
    abertas: int
    concluidas_sucesso: int
    concluidas_sem_solucao: int
    faturamento: float


@dataclass
class ResumoMensal:
    ano: int
    mes: int
    total: int
    concluidas_sucesso: int
    concluidas_sem_solucao: int
    em_reparo: int
    taxa_sucesso: float  # 0..100
    faturamento: float


class RelatorioService:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    # As datas são gravadas em ISO (YYYY-MM-DD...), então um prefixo de data casa.
    def resumo_diario(self, dia: date) -> ResumoDiario:
        prefixo = dia.isoformat()
        row_ab = self._conn.execute(
            "SELECT COUNT(*) AS n FROM ordens_servico WHERE substr(data_entrada,1,10)=?",
            (prefixo,),
        ).fetchone()
        row_su = self._conn.execute(
            "SELECT COUNT(*) AS n FROM ordens_servico "
            "WHERE status='concluido_sucesso' AND substr(data_conclusao,1,10)=?",
            (prefixo,),
        ).fetchone()
        row_se = self._conn.execute(
            "SELECT COUNT(*) AS n FROM ordens_servico "
            "WHERE status='concluido_sem_solucao' AND substr(data_conclusao,1,10)=?",
            (prefixo,),
        ).fetchone()
        row_fat = self._conn.execute(
            "SELECT COALESCE(SUM(valor_final),0) AS s FROM ordens_servico "
            "WHERE status='concluido_sucesso' AND substr(data_conclusao,1,10)=?",
            (prefixo,),
        ).fetchone()
        return ResumoDiario(
            dia=dia,
            abertas=int(row_ab["n"]),
            concluidas_sucesso=int(row_su["n"]),
            concluidas_sem_solucao=int(row_se["n"]),
            faturamento=float(row_fat["s"] or 0.0),
        )

    def resumo_mensal(self, ano: int, mes: int) -> ResumoMensal:
        # Compara pelo prefixo AAAA-MM para abertura e conclusão.
        pfx = f"{ano:04d}-{mes:02d}"
        total = self._conn.execute(
            "SELECT COUNT(*) AS n FROM ordens_servico WHERE substr(data_entrada,1,7)=?",
            (pfx,),
        ).fetchone()
        su = self._conn.execute(
            "SELECT COUNT(*) AS n FROM ordens_servico "
            "WHERE status='concluido_sucesso' AND substr(data_conclusao,1,7)=?",
            (pfx,),
        ).fetchone()
        se = self._conn.execute(
            "SELECT COUNT(*) AS n FROM ordens_servico "
            "WHERE status='concluido_sem_solucao' AND substr(data_conclusao,1,7)=?",
            (pfx,),
        ).fetchone()
        ab = self._conn.execute(
            "SELECT COUNT(*) AS n FROM ordens_servico WHERE status='em_reparo' AND substr(data_entrada,1,7)=?",
            (pfx,),
        ).fetchone()
        fat = self._conn.execute(
            "SELECT COALESCE(SUM(valor_final),0) AS s FROM ordens_servico "
            "WHERE status='concluido_sucesso' AND substr(data_conclusao,1,7)=?",
            (pfx,),
        ).fetchone()

        n_su = int(su["n"])
        n_se = int(se["n"])
        fechadas = n_su + n_se
        taxa = (n_su / fechadas * 100.0) if fechadas else 0.0

        return ResumoMensal(
            ano=ano,
            mes=mes,
            total=int(total["n"]),
            concluidas_sucesso=n_su,
            concluidas_sem_solucao=n_se,
            em_reparo=int(ab["n"]),
            taxa_sucesso=taxa,
            faturamento=float(fat["s"] or 0.0),
        )
