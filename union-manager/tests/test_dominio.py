"""Sanidade da camada de domínio (banco + modelos) — sem UI.

Valida: migrações, CRUD de clientes/ordens, ciclo de vida de OS e
o auto-aprendizado (encerrar com sucesso -> registrar no conhecimento).

Executar:
    python -m tests.test_dominio
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.db.connection import abrir_conexao
from app.core.db.migrations.runner import rodar_migracoes
from app.core.db.repos.cliente_repo import ClienteRepository
from app.core.db.repos.conhecimento_repo import ConhecimentoRepository
from app.core.db.repos.ordem_repo import OrdemRepository
from app.core.models.models import (
    Cliente,
    Conhecimento,
    OrigemConhecimento,
    OrdemServico,
    StatusOrdem,
    TipoCliente,
    TipoDispositivo,
)


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        conn = abrir_conexao(Path(td) / "teste.db")
        rodar_migracoes(conn)

        # --- cliente ---
        clientes = ClienteRepository(conn)
        c = Cliente(
            nome="João da Silva",
            telefone="85999990000",
            email="joao@example.com",
            tipo=TipoCliente.PESSOA_FISICA,
        )
        c.id = clientes.criar(c)
        assert c.id and c.id > 0, "falha ao criar cliente"
        assert not clientes.duplicado("João da Silva", "85999990000", excluir_id=c.id)
        achado = clientes.por_id(c.id)
        assert achado is not None and achado.nome == "João da Silva"
        assert len(clientes.buscar("joão")) == 1

        # --- ordem: criação em reparo ---
        ordens = OrdemRepository(conn)
        o = OrdemServico(
            cliente_id=c.id,
            tipo_dispositivo=TipoDispositivo.SMARTPHONE,
            marca="Samsung",
            modelo="Galaxy A05",
            valor=150.0,
            problema="Não liga",
            diagnostico="Bateria oxidada, substituída",
            status=StatusOrdem.EM_REPARO,
        )
        o.id = ordens.criar(o)
        assert o.id and o.id > 0, "falha ao criar OS"
        abertas = ordens.listar_abertas()
        assert any(x.id == o.id for x in abertas), "OS criada não aparece em abertas"

        # --- encerramento com sucesso (auto-aprendizado) ---
        o.status = StatusOrdem.CONCLUIDO_SUCESSO
        o.solucao = "Substituição da bateria"
        o.passos = "Abrir, trocar bateria, testar"
        o.valor_final = 150.0
        ordens.atualizar(o)

        kb = ConhecimentoRepository(conn)
        entrada_kb = Conhecimento(
            tipo_dispositivo=TipoDispositivo.SMARTPHONE,
            marca=o.marca,
            modelo=o.modelo,
            problema=o.problema,
            solucao=o.solucao,
            passos=o.passos,
            taxa_sucesso=100,
            origem=OrigemConhecimento.OS_ENCERRADA,
            ordem_origem_id=o.id,
        )
        entrada_kb.id = kb.criar(entrada_kb)
        assert entrada_kb.id, "falha ao registrar no conhecimento"
        ach = kb.buscar(termo="A05", tipo_dispositivo=TipoDispositivo.SMARTPHONE)
        assert any(x.id == entrada_kb.id for x in ach), "entrada não encontrada na busca"

        # --- contagem por status ---
        contagem = ordens.contar_por_status()
        assert contagem.get(StatusOrdem.CONCLUIDO_SUCESSO.value, 0) == 1

        conn.close()

    print("OK — domínio íntegro (clientes, OS, ciclo de vida, conhecimento).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
