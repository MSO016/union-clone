"""Regras de negócio de clientes (SPEC RF-CLI-*)."""
from __future__ import annotations

from typing import Optional

from ..db.repos.cliente_repo import ClienteRepository
from ..models.models import Cliente, TipoCliente
from .ordem_service import ValidacaoError


class ClienteService:
    def __init__(self, repo: ClienteRepository):
        self._repo = repo

    def criar(
        self,
        nome: str,
        telefone: str,
        email: str = "",
        rua: str = "",
        numero: str = "",
        bairro: str = "",
        cidade: str = "",
        tipo: TipoCliente = TipoCliente.PESSOA_FISICA,
        observacoes: str = "",
        user_id: Optional[int] = None,
    ) -> int:
        if not nome.strip():
            raise ValidacaoError("Informe o nome do cliente.")
        if not telefone.strip():
            raise ValidacaoError("Informe o telefone do cliente.")
        if email.strip() and "@" not in email:
            raise ValidacaoError("E-mail inválido (deve conter '@').")
        if self._repo.duplicado(nome.strip(), telefone.strip()):
            raise ValidacaoError("Já existe um cliente com este nome e telefone.")

        c = Cliente(
            user_id=user_id,
            nome=nome.strip(),
            telefone=telefone.strip(),
            email=email.strip(),
            rua=rua.strip(),
            numero=numero.strip(),
            bairro=bairro.strip(),
            cidade=cidade.strip(),
            tipo=tipo,
            observacoes=observacoes.strip(),
        )
        return self._repo.criar(c)

    def editar(self, cliente: Cliente) -> None:
        if not cliente.nome.strip():
            raise ValidacaoError("Informe o nome do cliente.")
        if not cliente.telefone.strip():
            raise ValidacaoError("Informe o telefone do cliente.")
        if cliente.email.strip() and "@" not in cliente.email:
            raise ValidacaoError("E-mail inválido (deve conter '@').")
        if self._repo.duplicado(
            cliente.nome.strip(), cliente.telefone.strip(), excluir_id=cliente.id
        ):
            raise ValidacaoError("Já existe outro cliente com este nome e telefone.")
        self._repo.atualizar(cliente)

    def excluir(self, cliente_id: int, forcar: bool = False) -> None:
        """Exclui; bloqueia se houver OS vinculadas, a menos que `forcar` (RF-CLI-2)."""
        if not forcar and self._repo.contar_ordens(cliente_id) > 0:
            raise ValidacaoError(
                "Este cliente possui ordens de serviço vinculadas."
            )
        self._repo.excluir(cliente_id)

    def buscar(self, termo: str) -> list[Cliente]:
        return self._repo.buscar(termo)

    def listar_todos(self) -> list[Cliente]:
        return self._repo.listar_todos()

    def por_id(self, cliente_id: int) -> Optional[Cliente]:
        return self._repo.por_id(cliente_id)
