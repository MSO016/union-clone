"""Parsers de diagnóstico (puros, sem Qt nem subprocess).

Convertem a saída bruta do `adb shell dumpsys ...` em estruturas tipadas.
Testáveis offline a partir de fixtures (SPEC RF-DIA-6).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class LeituraBateria:
    nivel: Optional[int]          # 0..100
    temperatura_c: Optional[float]  # graus Celsius
    voltagem_mv: Optional[int]
    status: Optional[str]
    saude: Optional[str]


def parse_dumpsys_bateria(saida: str) -> LeituraBateria:
    """Interpreta `adb shell dumpsys battery`."""
    nivel: Optional[int] = None
    temp_c: Optional[float] = None
    volt: Optional[int] = None
    status: Optional[str] = None
    saude: Optional[str] = None

    for linha in saida.splitlines():
        linha = linha.strip()
        baixo = linha.lower()
        if baixo.startswith("level:"):
            nivel = _int_de(linha)
        elif baixo.startswith("temperature:"):
            # O Android reporta décimos de °C.
            t = _int_de(linha)
            if t is not None:
                temp_c = t / 10.0
        elif baixo.startswith("voltage:"):
            volt = _int_de(linha)
        elif baixo.startswith("status:"):
            status = _valor_apos_dois_pontos(linha)
        elif baixo.startswith("health:"):
            saude = _valor_apos_dois_pontos(linha)

    return LeituraBateria(
        nivel=nivel,
        temperatura_c=temp_c,
        voltagem_mv=volt,
        status=status,
        saude=saude,
    )


def _valor_apos_dois_pontos(linha: str) -> str:
    if ":" in linha:
        return linha.split(":", 1)[1].strip()
    return ""


def _int_de(linha: str) -> Optional[int]:
    valor = _valor_apos_dois_pontos(linha)
    try:
        return int(valor)
    except (ValueError, TypeError):
        return None
