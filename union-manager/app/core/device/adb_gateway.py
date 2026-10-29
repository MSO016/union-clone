"""Implementação do DeviceGateway via subprocesso `adb` (platform-tools).

Requer o `adb` no PATH ou no diretório do app (SPEC RF-TOL-5).
"""
from __future__ import annotations

import shutil
import subprocess
from typing import Optional

from .gateway import DeviceGateway, Dispositivo


class AdbGateway(DeviceGateway):
    def __init__(self, adb_path: Optional[str] = None, timeout: float = 30.0):
        self._adb = adb_path or shutil.which("adb") or "adb"
        self._timeout = timeout

    def disponivel(self) -> bool:
        return shutil.which(self._adb) is not None

    def _rodar(self, args: list[str], timeout: Optional[float] = None) -> str:
        try:
            proc = subprocess.run(
                [self._adb, *args],
                capture_output=True,
                text=True,
                timeout=timeout or self._timeout,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return proc.stdout or ""
        except FileNotFoundError:
            return ""
        except subprocess.TimeoutExpired:
            return ""

    def listar_dispositivos(self) -> list[Dispositivo]:
        saida = self._rodar(["devices", "-l"])
        dispositivos: list[Dispositivo] = []
        for linha in saida.splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("List of devices") or linha.startswith("*"):
                continue
            partes = linha.split()
            if len(partes) >= 2:
                dispositivos.append(
                    Dispositivo(serial=partes[0], estado=partes[1], descricao=linha)
                )
        return dispositivos

    def executar_shell(self, comando: str, serial: Optional[str] = None,
                       timeout: float = 30.0) -> str:
        args = ["shell"] if serial is None else ["-s", serial, "shell"]
        return self._rodar([*args, comando], timeout=timeout)
