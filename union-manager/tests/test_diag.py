"""Sanidade dos parsers de diagnóstico (offline, via fixture).

Executar: python -m tests.test_diag
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.diag.bateria import parse_dumpsys_bateria


def main() -> int:
    fixture = (ROOT / "fixtures" / "dumpsys_bateria.txt").read_text(encoding="utf-8")
    b = parse_dumpsys_bateria(fixture)

    assert b.nivel == 85, f"nivel={b.nivel}"
    assert abs(b.temperatura_c - 28.7) < 1e-6, f"temp={b.temperatura_c}"
    assert b.voltagem_mv == 4123, f"volt={b.voltagem_mv}"
    assert b.status is not None and b.saude is not None

    # Caso vazio não pode explodir.
    vazio = parse_dumpsys_bateria("")
    assert vazio.nivel is None and vazio.temperatura_c is None

    print("OK — parser de bateria (fixture offline).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
