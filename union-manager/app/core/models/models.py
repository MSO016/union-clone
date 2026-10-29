"""Modelos de domínio (dataclasses) — sem dependência de Qt nem de banco.

São a fronteira entre persistência (sqlite3.Row) e serviços/UI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TipoCliente(str, Enum):
    PESSOA_FISICA = "pessoa_fisica"
    LOJISTA = "lojista"


class StatusOrdem(str, Enum):
    EM_REPARO = "em_reparo"
    CONCLUIDO_SUCESSO = "concluido_sucesso"
    CONCLUIDO_SEM_SOLUCAO = "concluido_sem_solucao"


# Rótulos legados exibíveis em histórico (SPEC RF-OS-1).
ROTULOS_LEGADOS = {
    "aberto": "Aberto",
    "em_andamento": "Em Andamento",
    "cancelado": "Cancelado",
}


class TipoDispositivo(str, Enum):
    NOTEBOOK = "Notebook"
    SMARTPHONE = "Smartphone"
    DESKTOP = "Desktop"
    TABLET = "Tablet"
    IMPRESSORA = "Impressora"
    OUTRO = "Outro"


class OrigemConhecimento(str, Enum):
    MANUAL = "manual"
    OS_ENCERRADA = "os_encerrada"


@dataclass
class Cliente:
    id: Optional[int] = None
    user_id: Optional[int] = None
    nome: str = ""
    telefone: str = ""
    email: str = ""
    rua: str = ""
    numero: str = ""
    bairro: str = ""
    cidade: str = ""
    tipo: TipoCliente = TipoCliente.PESSOA_FISICA
    observacoes: str = ""
    criado_em: str = ""
    atualizado_em: str = ""

    @property
    def endereco_completo(self) -> str:
        partes = [self.rua, self.numero, self.bairro, self.cidade]
        return ", ".join(p for p in partes if p)


@dataclass
class OrdemFoto:
    id: Optional[int] = None
    ordem_id: Optional[int] = None
    caminho: str = ""
    ordem: int = 0
    criado_em: str = ""


@dataclass
class OrdemServico:
    id: Optional[int] = None
    user_id: Optional[int] = None
    cliente_id: int = 0
    tipo_dispositivo: TipoDispositivo = TipoDispositivo.SMARTPHONE
    marca: str = ""
    modelo: str = ""
    serie: str = ""
    valor: Optional[float] = None
    problema: str = ""
    diagnostico: str = ""
    status: StatusOrdem = StatusOrdem.EM_REPARO
    solucao: str = ""
    passos: str = ""
    motivo_falha: str = ""
    observacoes_tecnicas: str = ""
    valor_final: Optional[float] = None
    foto_conclusao: str = ""
    os_original_id: Optional[int] = None
    data_entrada: str = ""
    data_conclusao: str = ""
    fotos: list[OrdemFoto] = field(default_factory=list)


@dataclass
class ConhecimentoAnexo:
    id: Optional[int] = None
    conhecimento_id: Optional[int] = None
    tipo: str = ""
    caminho: str = ""
    descricao: str = ""


@dataclass
class Conhecimento:
    id: Optional[int] = None
    user_id: Optional[int] = None
    tipo_dispositivo: TipoDispositivo = TipoDispositivo.SMARTPHONE
    marca: str = ""
    modelo: str = ""
    problema: str = ""
    solucao: str = ""
    passos: str = ""
    taxa_sucesso: int = 100
    origem: OrigemConhecimento = OrigemConhecimento.MANUAL
    ordem_origem_id: Optional[int] = None
    criado_em: str = ""
    anexos: list[ConhecimentoAnexo] = field(default_factory=list)


@dataclass
class SolucaoMidia:
    id: Optional[int] = None
    solucao_id: Optional[int] = None
    tipo: str = "imagem"  # imagem | diagrama
    caminho: str = ""
    posicao: int = 0


@dataclass
class Solucao:
    id: Optional[int] = None
    user_id: Optional[int] = None
    marca: str = ""
    modelo: str = ""
    descricao: str = ""
    observacoes: str = ""
    status: str = "ativo"
    hash: str = ""
    versao: int = 1
    criado_em: str = ""
    atualizado_em: str = ""
    midias: list[SolucaoMidia] = field(default_factory=list)


@dataclass
class ConfigEmpresa:
    user_id: int = 0
    logo: Optional[bytes] = None
    razao_social: str = ""
    cnpj: str = ""
    nome_fantasia: str = ""
    endereco: str = ""
    cidade: str = ""
    estado: str = ""
    telefone: str = ""
    email: str = ""
    website: str = ""
    mensagem_rodape: str = ""
    termos_garantia: str = (
        "Garantia de 90 dias sobre serviços e peças descritas nesta ordem de serviço."
    )


@dataclass
class PerfilUsuario:
    user_id: int = 0
    nome: str = ""
    telefone: str = ""
    email: str = ""
    foto: Optional[bytes] = None
    bio: str = ""
    nascimento: str = ""
    notif_email: bool = False
    notif_push: bool = False
