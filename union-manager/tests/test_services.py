"""Sanidade das regras de negócio (services) — sem UI.

Cobre: validação de criação, encerramento (RF-OS-4), auto-aprendizado
(RF-OS-5), garantia (RF-OS-6) e relatórios (RF-REP-1/2).

Executar: python -m tests.test_services
"""
from __future__ import annotations

import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.db.connection import abrir_conexao
from app.core.db.migrations.runner import rodar_migracoes
from app.core.db.repos.cliente_repo import ClienteRepository
from app.core.db.repos.conhecimento_repo import ConhecimentoRepository
from app.core.db.repos.ordem_repo import OrdemRepository
from app.core.models.models import Cliente, TipoCliente, TipoDispositivo
from app.core.services.ordem_service import (
    OrdemServicoService,
    ValidacaoError,
    StatusOrdem,
)
from app.core.services.relatorio_service import RelatorioService


def _deve_falhar(fn, *a, **k) -> None:
    try:
        fn(*a, **k)
    except ValidacaoError:
        return
    raise AssertionError(f"esperava ValidacaoError em {fn.__name__}")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        conn = abrir_conexao(Path(td) / "teste.db")
        rodar_migracoes(conn)

        clientes = ClienteRepository(conn)
        cid = clientes.criar(Cliente(nome="Maria", telefone="85988887777", tipo=TipoCliente.LOJISTA))

        ordens = OrdemRepository(conn)
        kb = ConhecimentoRepository(conn)
        svc = OrdemServicoService(ordens, kb)
        hoje = date.today()

        # --- validação de criação (RF-OS-2) ---
        _deve_falhar(svc.criar, cid, TipoDispositivo.SMARTPHONE, "", "A05", "n liga")
        _deve_falhar(svc.criar, cid, TipoDispositivo.SMARTPHONE, "Samsung", "", "n liga")
        _deve_falhar(svc.criar, cid, TipoDispositivo.SMARTPHONE, "Samsung", "A05", "")
        _deve_falhar(svc.criar, cid, TipoDispositivo.SMARTPHONE, "Samsung", "A05", "x", valor=-1)

        oid = svc.criar(cid, TipoDispositivo.SMARTPHONE, "Samsung", "A05", "Nao liga", valor=100)
        assert oid > 0

        # --- encerramento: regras (RF-OS-4) ---
        from app.core.models.models import StatusOrdem as S

        _deve_falhar(svc.encerrar, oid, S.EM_REPARO)  # status final inválido
        _deve_falhar(svc.encerrar, oid, S.CONCLUIDO_SUCESSO, solucao="", passos="p")  # sucesso sem solução
        _deve_falhar(svc.encerrar, oid, S.CONCLUIDO_SUCESSO, solucao="s", passos="")  # sem passos
        _deve_falhar(svc.encerrar, oid, S.CONCLUIDO_SEM_SOLUCAO, passos="p", motivo_falha="")  # sem motivo

        # --- encerramento com sucesso + auto-aprendizado (RF-OS-5) ---
        antes = len(kb.buscar(termo="A05"))
        svc.encerrar(oid, S.CONCLUIDO_SUCESSO, solucao="Trocar bateria", passos="abrir; trocar", valor_final=100)
        depois = len(kb.buscar(termo="A05"))
        assert depois == antes + 1, "auto-aprendizado não registrou no conhecimento"
        ordem_fechada = ordens.por_id(oid)
        assert ordem_fechada.status == S.CONCLUIDO_SUCESSO and ordem_fechada.data_conclusao

        # --- relatórios (RF-REP-1/2) ---
        rel = RelatorioService(conn)
        d = rel.resumo_diario(hoje)
        assert d.concluidas_sucesso == 1 and abs(d.faturamento - 100.0) < 1e-6
        m = rel.resumo_mensal(hoje.year, hoje.month)
        assert m.concluidas_sucesso == 1
        assert abs(m.taxa_sucesso - 100.0) < 1e-6

        # --- segunda OS: sem solução, p/ garantia (RF-OS-6) ---
        oid2 = svc.criar(cid, TipoDispositivo.NOTEBOOK, "Dell", "Inspiron", "Nao liga")
        svc.encerrar(oid2, S.CONCLUIDO_SEM_SOLUCAO, passos="diagnosticar", motivo_falha="placa queimada")
        nova = svc.reabrir_garantia(oid2)
        assert nova > 0
        assert ordens.por_id(nova).os_original_id == oid2
        assert ordens.por_id(nova).status == S.EM_REPARO

        # sem solução NÃO entra no conhecimento
        assert len(kb.buscar(termo="Inspiron")) == 0

        conn.close()

    print("OK — services (validações, auto-aprendizado, garantia, relatórios).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
