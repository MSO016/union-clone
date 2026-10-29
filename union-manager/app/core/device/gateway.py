"""Porta (interface) do gateway de dispositivo.

A UI e os serviços dependem só desta abstração; a implementação concreta
(ADB/fastboot) fica em `adb_gateway.py`. Isso mantém a camada de teste
independente de hardware.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Dispositivo:
    serial: str
    estado: str  # device | offline | unauthorized | ...
    descricao: str = ""


class DeviceGateway(ABC):
    """Contrato mínimo de acesso a um aparelho conectado."""

    @abstractmethod
    def listar_dispositivos(self) -> list[Dispositivo]:
        """Lista aparelhos visíveis (via `adb devices`)."""

    @abstractmethod
    def executar_shell(self, comando: str, serial: Optional[str] = None,
                       timeout: float = 30.0) -> str:
        """Executa um comando `adb shell` e devolve a saída bruta."""

    @abstractmethod
    def disponivel(self) -> bool:
        """Indica se a ferramenta (adb) foi encontrada no ambiente."""
