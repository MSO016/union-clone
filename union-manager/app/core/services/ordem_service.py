"""Regras de negócio das ordens de serviço.

Centraliza validações do SPEC (RF-OS-*) e o auto-aprendizado:
encerrar com sucesso injeta a solução na base de conhecimento (RF-OS-5).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from ..db.repos.conhecimento_repo import ConhecimentoRepository
from ..db.repos.ordem_repo import OrdemRepository
from ..models.models import (
    Conhecimento,
    OrigemConhecimento,
    OrdemServico,
    StatusOrdem,
    TipoDispositivo,
)


class ValidacaoError(ValueError):
    """Erro de regra de negócio com mensagem amigável (RF-NF-7)."""


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


class OrdemServicoService:
    def __init__(self, ordem_repo: OrdemRepository, conhecimento_repo: ConhecimentoRepository):
        self._ordens = ordem_repo
        self._conhecimento = conhecimento_repo

    # --- consultas delegadas (usadas pela UI) ------------------------------
    def listar_abertas(self) -> list[OrdemServico]:
        return self._ordens.listar_abertas()

    def contar_por_status(self) -> dict[str, int]:
        return self._ordens.contar_por_status()

    def por_id(self, ordem_id: int) -> Optional[OrdemServico]:
        return self._ordens.por_id(ordem_id)

    def listar_historico(self, status=None, termo: str = "") -> list[OrdemServico]:
        return self._ordens.listar_historico(status=status, termo=termo)

    def excluir(self, ordem_id: int) -> None:
        self._ordens.excluir(ordem_id)

    # --- criação (RF-OS-2) ------------------------------------------------
    def criar(
        self,
        cliente_id: int,
        tipo_dispositivo: TipoDispositivo,
        marca: str,
        modelo: str,
        problema: str,
        serie: str = "",
        valor: Optional[float] = None,
        diagnostico: str = "",
        user_id: Optional[int] = None,
    ) -> int:
        if not marca.strip():
            raise ValidacaoError("Informe a marca do dispositivo.")
        if not modelo.strip():
            raise ValidacaoError("Informe o modelo do dispositivo.")
        if not problema.strip():
            raise ValidacaoError("Descreva o problema relatado.")
        if valor is not None and valor < 0:
            raise ValidacaoError("O valor do serviço não pode ser negativo.")

        ordem = OrdemServico(
            user_id=user_id,
            cliente_id=cliente_id,
            tipo_dispositivo=tipo_dispositivo,
            marca=marca.strip(),
            modelo=modelo.strip(),
            serie=serie.strip(),
            valor=valor,
            problema=problema.strip(),
            diagnostico=diagnostico.strip(),
            status=StatusOrdem.EM_REPARO,
            data_entrada=_agora(),
        )
        return self._ordens.criar(ordem)

    # --- encerramento (RF-OS-4 + RF-OS-5) ---------------------------------
    def encerrar(
        self,
        ordem_id: int,
        status_final: StatusOrdem,
        solucao: str = "",
        passos: str = "",
        motivo_falha: str = "",
        observacoes_tecnicas: str = "",
        valor_final: Optional[float] = None,
        foto_conclusao: str = "",
        registrar_conhecimento: bool = True,
    ) -> OrdemServico:
        if status_final == StatusOrdem.EM_REPARO:
            raise ValidacaoError("Status final inválido para encerramento.")

        ordem = self._ordens.por_id(ordem_id)
        if ordem is None:
            raise ValidacaoError("Ordem de serviço não encontrada.")

        # Regras do SPEC RF-OS-4.
        if status_final == StatusOrdem.CONCLUIDO_SUCESSO and not solucao.strip():
            raise ValidacaoError("Concluído com sucesso exige a solução aplicada.")
        if not passos.strip():
            raise ValidacaoError("Informe os passos realizados.")
        if status_final == StatusOrdem.CONCLUIDO_SEM_SOLUCAO and not motivo_falha.strip():
            raise ValidacaoError("Concluído sem solução exige o motivo da falha.")
        if valor_final is not None and valor_final < 0:
            raise ValidacaoError("O valor final não pode ser negativo.")

        ordem.status = status_final
        ordem.solucao = solucao.strip()
        ordem.passos = passos.strip()
        ordem.motivo_falha = motivo_falha.strip()
        ordem.observacoes_tecnicas = observacoes_tecnicas.strip()
        ordem.valor_final = valor_final
        ordem.foto_conclusao = foto_conclusao
        ordem.data_conclusao = _agora()
        self._ordens.atualizar(ordem)

        # Auto-aprendizado: sucesso alimenta a base de conhecimento (RF-OS-5).
        if status_final == StatusOrdem.CONCLUIDO_SUCESSO and registrar_conhecimento:
            self._registrar_no_conhecimento(ordem)

        return ordem

    def _registrar_no_conhecimento(self, ordem: OrdemServico) -> None:
        entrada = Conhecimento(
            user_id=ordem.user_id,
            tipo_dispositivo=ordem.tipo_dispositivo,
            marca=ordem.marca,
            modelo=ordem.modelo,
            problema=ordem.problema,
            solucao=ordem.solucao,
            passos=ordem.passos,
            taxa_sucesso=100,
            origem=OrigemConhecimento.OS_ENCERRADA,
            ordem_origem_id=ordem.id,
            criado_em=_agora(),
        )
        self._conhecimento.criar(entrada)

    # --- reabertura/garantia (RF-OS-6) ------------------------------------
    def reabrir_garantia(self, ordem_id: int) -> int:
        ordem = self._ordens.por_id(ordem_id)
        if ordem is None:
            raise ValidacaoError("Ordem de serviço não encontrada.")
        nova = OrdemServico(
            user_id=ordem.user_id,
            cliente_id=ordem.cliente_id,
            tipo_dispositivo=ordem.tipo_dispositivo,
            marca=ordem.marca,
            modelo=ordem.modelo,
            serie=ordem.serie,
            valor=ordem.valor,
            problema=ordem.problema,
            diagnostico=f"Garantia da OS #{ordem.id}: {ordem.problema}",
            status=StatusOrdem.EM_REPARO,
            os_original_id=ordem.id,
            data_entrada=_agora(),
        )
        return self._ordens.criar(nova)
